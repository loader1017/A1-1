from pathlib import Path

import numpy as np
import pandas as pd


class DataAnalyzer:
    """Prepare and analyze a customer-level sample of Retail transactions."""

    def __init__(self, data_path):
        self.data_path = Path(data_path)

    def load_data(self, sample_size=100, random_state=42, chunksize=250_000):
        transaction_path = self.data_path / "Transactions.csv"
        customer_ids = set()

        with pd.read_csv(
            transaction_path,
            usecols=["cust_id"],
            dtype={"cust_id": "string"},
            chunksize=chunksize,
        ) as chunks:
            for chunk in chunks:
                customer_ids.update(chunk["cust_id"].dropna().unique())

        sample_ids = pd.Series(sorted(customer_ids), dtype="string").sample(
            n=sample_size, random_state=random_state
        )

        with pd.read_csv(
            transaction_path,
            dtype={
                "cust_id": "string",
                "prod_subcat_code": "string",
                "prod_cat_code": "string",
            },
            chunksize=chunksize,
        ) as chunks:
            transactions = pd.concat(
                [chunk.loc[chunk["cust_id"].isin(sample_ids)] for chunk in chunks]
            )

        transactions = transactions.rename(columns={"cust_id": "customer_id"})
        transactions["tran_date"] = pd.to_datetime(
            transactions["tran_date"].str.replace("/", "-", regex=False),
            format="%d-%m-%Y",
            errors="coerce",
        )
        # 반품(음수 금액)은 구매 패턴 분석에서 제외
        transactions = transactions.loc[transactions["total_amt"] > 0].copy()

        customers = pd.read_csv(
            self.data_path / "Customer.csv",
            dtype={"customer_Id": "string"},
        )
        customers = customers.rename(columns={"customer_Id": "customer_id"})
        customers = customers.loc[customers["customer_id"].isin(sample_ids)].copy()

        customers["DOB"] = pd.to_datetime(
            customers["DOB"], dayfirst=True, errors="coerce"
        )
        reference_date = transactions["tran_date"].max()
        customers["age"] = (
            (reference_date - customers["DOB"]).dt.days / 365.25
        ).round(1)

        products = pd.read_csv(
            self.data_path / "prod_cat_info.csv",
            dtype={"prod_cat_code": "string", "prod_sub_cat_code": "string"},
        )
        products = products.rename(columns={"prod_sub_cat_code": "prod_subcat_code"})
        product_ids = transactions["prod_subcat_code"].unique()
        products = products.loc[products["prod_subcat_code"].isin(product_ids)].copy()

        return transactions, customers, products

    @staticmethod
    def handle_missing_values(data, column, *, group_col=None, strategy="median"):
        """Fill missing numeric values with a group statistic and an overall fallback."""
        if strategy not in {"median", "mean"}:
            raise ValueError("strategy must be 'median' or 'mean'")

        values = data[column]
        if group_col is not None:
            group_values = data.groupby(group_col)[column].transform(strategy)
            values = values.fillna(group_values)
        return values.fillna(values.agg(strategy))

    @staticmethod
    def detect_outliers(values, threshold=1.5):
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        return (values < lower) | (values > upper)

    def add_image_features(self, articles, image_size=(32, 32), random_state=42):
        """
        상품 코드 기반 고정 시드로 합성 이미지 배열을 생성하고 픽셀 통계를 추출한다.
        (n, H, W, 3) 배열 전체에 NumPy 축 연산을 적용해 for loop 없이 배치 처리한다.
        """
        articles = articles.copy()
        n = len(articles)
        h, w = image_size

        rng = np.random.default_rng(random_state)
        images = rng.integers(0, 256, size=(n, h, w, 3), dtype=np.uint8)

        pixels = images.astype(np.float32) / 255.0
        articles["image_mean"] = pixels.mean(axis=(1, 2, 3))
        articles["image_std"] = pixels.std(axis=(1, 2, 3))

        return articles

    @staticmethod
    def add_text_features(data):
        return data.assign(product_name_length=data["prod_subcat"].str.len())

    @staticmethod
    def summarize(data, columns):
        return data[columns].describe()

    @staticmethod
    def calculate_rfm(
        data,
        customer_col="customer_id",
        date_col="tran_date",
        amount_col="total_amt",
        reference_date=None,
    ):
        if reference_date is None:
            reference_date = data[date_col].max()

        rfm = data.groupby(customer_col).agg(
            last_purchase=(date_col, "max"),
            frequency=(date_col, "nunique"),
            monetary=(amount_col, "sum"),
        )
        recency = (pd.Timestamp(reference_date) - rfm.pop("last_purchase")).dt.days
        rfm.insert(0, "recency", recency)
        return rfm
