# K-Food Hard Class Report

- source_error_dir: `reports/error_analysis/final_candidate`
- hard_class_count: `16`
- hard_pair_count: `30`

## Hard Classes

| Class | F1 | Recall | High-Conf Errors | Action |
|---|---:|---:|---:|---|
| 동태찌개 | 0.798165 | 0.870000 | 4 | review broth-only images; prioritize images with distinctive ingredients |
| 갈비찜 | 0.816626 | 0.835000 | 8 | review high-confidence errors and add diverse clean examples |
| 김치찌개 | 0.817955 | 0.820000 | 8 | review broth-only images; prioritize images with distinctive ingredients |
| 갈비구이 | 0.824691 | 0.835000 | 7 | review high-confidence errors and add diverse clean examples |
| 삼겹살 | 0.827586 | 0.783920 | 6 | review high-confidence errors and add diverse clean examples |
| 라면 | 0.834646 | 0.798995 | 11 | review high-confidence errors and add diverse clean examples |
| 닭볶음탕 | 0.835897 | 0.815000 | 15 | review broth-only images; prioritize images with distinctive ingredients |
| 곰탕_설렁탕 | 0.839895 | 0.800000 | 15 | review broth-only images; prioritize images with distinctive ingredients |
| 닭갈비 | 0.842365 | 0.855000 | 2 | review high-confidence errors and add diverse clean examples |
| 불고기 | 0.843434 | 0.835000 | 6 | review high-confidence errors and add diverse clean examples |
| 칼국수 | 0.846348 | 0.840000 | 11 | review broth-only images; prioritize images with distinctive ingredients |
| 김치찜 | 0.851385 | 0.845000 | 5 | review high-confidence errors and add diverse clean examples |
| 수제비 | 0.860825 | 0.839196 | 7 | review high-confidence errors and add diverse clean examples |
| 닭계장 | 0.861538 | 0.840000 | 10 | review high-confidence errors and add diverse clean examples |
| 감자탕 | 0.865672 | 0.870000 | 7 | review broth-only images; prioritize images with distinctive ingredients |
| 삼계탕 |  |  | 3 | review broth-only images; prioritize images with distinctive ingredients |

## Hard Pairs

| True | Pred | Count | True Accuracy |
|---|---|---:|---:|
| 곰탕_설렁탕 | 갈비탕 | 13 | 0.8 |
| 김치찌개 | 동태찌개 | 13 | 0.82 |
| 호박전 | 감자전 | 12 | 0.875 |
| 감자전 | 호박전 | 11 | 0.88 |
| 갈비구이 | 갈비찜 | 10 | 0.835 |
| 곰탕_설렁탕 | 삼계탕 | 10 | 0.8 |
| 비빔냉면 | 물냉면 | 10 | 0.905 |
| 삼겹살 | 갈비구이 | 10 | 0.7839195979899497 |
| 칼국수 | 수제비 | 10 | 0.84 |
| 김치찜 | 김치찌개 | 9 | 0.845 |
| 수제비 | 칼국수 | 9 | 0.8391959798994975 |
| 잔치국수 | 칼국수 | 9 | 0.875 |
| 갈비구이 | 삼겹살 | 8 | 0.835 |
| 떡볶이 | 라볶이 | 8 | 0.8793969849246231 |
| 라면 | 라볶이 | 8 | 0.7989949748743719 |
| 순두부찌개 | 김치찌개 | 8 | 0.86 |
| 양념치킨 | 후라이드치킨 | 8 | 0.91 |
| 족발 | 보쌈 | 8 | 0.9 |
| 칼국수 | 잔치국수 | 8 | 0.84 |
| 갈비구이 | 떡갈비 | 7 | 0.835 |
