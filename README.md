# Retail Case Study 구매 패턴과 RFM 고객 세분화


고객, 상품, 거래 데이터를 연결해 구매 패턴을 분석하고 RFM으로 고객을 분류한다. [분석 노트북](notebooks/analysis_report.ipynb)은 결측치 처리, IQR 이상치 탐지, 인구통계 피처, 통계 분석, 여섯 유형의 시각화를 포함한다. 전처리와 집계는 [DataAnalyzer](src/pipeline.py)에 구현했다.

## 데이터와 분석 범위

출처는 [Retail Case Study Data](https://www.kaggle.com/datasets/darpan25bajaj/retail-case-study-data)다. 거래 CSV의 고객 ID를 정렬해 시드 42로 100명을 뽑고, 선택된 고객의 전체 관측 기간 거래를 유지했다. 반품에 해당하는 음수 거래 금액은 분석에서 제외해 고객 300명, 거래 1,188행, 상품 23종이 추출됐다.

| 입력 | 출처 | 사용한 정보 |
| --- | --- | --- |
| `Transactions.csv` | Kaggle 다운로드 | 거래일, 고객 ID, 상품 코드, 수량, 거래 금액 |
| `Customer.csv` | Kaggle 다운로드 | 고객 ID, 생년월일, 성별, 도시 코드 |
| `prod_cat_info.csv` | Kaggle 다운로드 | 상품 카테고리 코드, 카테고리명, 서브카테고리명 |
| `data/images/` | 저장소 포함 (직접 생성) | 카테고리별 대표 이미지 — 픽셀 평균·표준편차 피처 추출용 |

> **이미지 출처**: 원본 데이터셋에는 상품 이미지가 없다. `data/images/{카테고리}/{서브카테고리}.jpg`는 카테고리별 색상 그라디언트로 직접 생성한 대표 이미지이며 저장소에 포함되어 있다. 이미지 피처(픽셀 평균·표준편차) 추출 파이프라인 시연 목적으로 제작했다.

RFM 기준일은 표본의 마지막 거래일인 **2014-02-19**다. Recency는 마지막 구매 후 지난 일수, Frequency는 서로 다른 구매 날짜 수, Monetary는 거래 금액 합계다.

## 분석 결과

IQR 기준을 벗어난 거래 금액은 18행(1.52%)이었다. 이상치 분포 비교에는 박스플롯을 사용하고 RFM에는 전체 거래를 사용했다. 이미지 피처는 카테고리별 대표 이미지 파일에서 추출했으며, 거래 금액과의 피어슨 상관계수는 모두 0 근방으로 나타났다(이미지가 가격 정보를 담지 않으므로 예상된 결과).

| 세그먼트 | 고객 수 | 평균 구매일 수 | 구매금액 비중 |
| --- | ---: | ---: | ---: |
| VIP | 50명 | 6.40 | 29.20% |
| Loyal | 31명 | 5.87 | 13.23% |
| Regular | 94명 | 3.19 | 26.78% |
| At Risk | 120명 | 3.14 | 30.36% |
| New | 5명 | 1.00 | 0.43% |

## 비즈니스 인사이트

1. **At Risk 고객 재활성화 우선 검토.** At Risk 120명이 구매금액의 30.36%를 차지하며 전체 세그먼트 중 가장 높다. 마지막 구매 후 평균 488일이 경과했으므로 과거 구매금액과 구매 간격을 함께 보고 연락 대상을 좁혀 재구매를 유도한다. 선별된 고객의 후속 구매율을 동일 기간 대조군과 비교한다.
2. **VIP 고객 유지.** VIP 50명이 구매금액의 29.20%를 차지한다. 평균 구매일 수는 6.40일로 가장 높으며, 선호 카테고리의 신상품이나 프로모션을 안내해 재구매를 유도한다. VIP 내 대조군을 두고 동일 기간의 재구매율과 고객당 구매금액을 비교한다.
3. **Loyal과 Regular의 다음 구매 유도.** Loyal 평균 구매일 수는 5.87일, Regular는 3.19일이었다. Loyal에는 반복 구매한 카테고리의 후속 상품을, Regular에는 관심 상품과 함께 구매할 만한 상품을 안내해 구매일 수 증가를 목표로 한다. 세그먼트마다 대조군을 두고 후속 구매일 수를 비교한다.

## 로컬 실행

1. Kaggle에서 [Retail Case Study Data](https://www.kaggle.com/datasets/darpan25bajaj/retail-case-study-data)의 세 파일(`Transactions.csv`, `Customer.csv`, `prod_cat_info.csv`)을 내려받는다.
2. 저장소 루트의 `data/` 아래에 세 CSV를 둔다. 다른 위치에 두었다면 Jupyter를 실행하기 전에 `RETAIL_DATA_DIR` 환경변수에 데이터 디렉터리를 지정한다.
   - `data/images/`는 저장소에 이미 포함되어 있어 별도 다운로드가 필요 없다.
3. Python 3.11 환경에서 아래 명령으로 Jupyter를 열고, `notebooks/analysis_report.ipynb`의 셀을 위에서부터 실행한다.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt notebook
python -m jupyter notebook
```

거래 CSV는 고객 ID 수집과 거래 추출을 위해 청크 단위로 두 번 읽는다. 노트북에 저장된 표와 차트는 고객 300명 표본의 집계 결과다.
