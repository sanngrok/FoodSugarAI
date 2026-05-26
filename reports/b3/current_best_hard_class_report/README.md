# K-Food Hard Class Report

- source_error_dir: `reports/b3/current_best_error_analysis`
- hard_class_count: `19`
- hard_pair_count: `30`

## Hard Classes

| Class | F1 | Recall | High-Conf Errors | Action |
|---|---:|---:|---:|---|
| 곰탕_설렁탕 | 0.801762 | 0.758333 | 16 | review broth-only images; prioritize images with distinctive ingredients |
| 닭볶음탕 | 0.824034 | 0.800000 | 14 | review broth-only images; prioritize images with distinctive ingredients |
| 삼겹살 | 0.828194 | 0.783333 | 8 | review high-confidence errors and add diverse clean examples |
| 갈비구이 | 0.829694 | 0.791667 | 10 | review high-confidence errors and add diverse clean examples |
| 동태찌개 | 0.837398 | 0.858333 | 7 | review broth-only images; prioritize images with distinctive ingredients |
| 김치찌개 | 0.842975 | 0.850000 | 11 | review broth-only images; prioritize images with distinctive ingredients |
| 수제비 | 0.863071 | 0.866667 | 8 | review high-confidence errors and add diverse clean examples |
| 닭계장 | 0.869198 | 0.858333 | 9 | review high-confidence errors and add diverse clean examples |
| 감자전 | 0.872881 | 0.858333 | 9 | review ingredient texture and crop quality |
| 칼국수 | 0.873950 | 0.866667 | 9 | review broth-only images; prioritize images with distinctive ingredients |
| 닭갈비 | 0.875000 | 0.875000 | 2 | review high-confidence errors and add diverse clean examples |
| 짬뽕 | 0.877637 | 0.866667 | 7 | review high-confidence errors and add diverse clean examples |
| 갈비찜 | 0.878661 | 0.875000 | 12 | review high-confidence errors and add diverse clean examples |
| 김치찜 | 0.878661 | 0.875000 | 10 | review high-confidence errors and add diverse clean examples |
| 불고기 | 0.879032 | 0.908333 | 5 | review high-confidence errors and add diverse clean examples |
| 양념치킨 |  |  | 7 | review high-confidence errors and add diverse clean examples |
| 삼계탕 |  |  | 5 | review broth-only images; prioritize images with distinctive ingredients |
| 감자탕 |  |  | 4 | review broth-only images; prioritize images with distinctive ingredients |
| 순두부찌개 |  |  | 5 | review broth-only images; prioritize images with distinctive ingredients |

## Hard Pairs

| True | Pred | Count | True Accuracy |
|---|---|---:|---:|
| 감자전 | 호박전 | 12 | 0.8583333333333333 |
| 곰탕_설렁탕 | 갈비탕 | 9 | 0.7583333333333333 |
| 김치찜 | 김치찌개 | 8 | 0.875 |
| 칼국수 | 수제비 | 8 | 0.8666666666666667 |
| 곰탕_설렁탕 | 삼계탕 | 7 | 0.7583333333333333 |
| 떡볶이 | 라볶이 | 7 | 0.9 |
| 호박전 | 감자전 | 7 | 0.9 |
| 갈비찜 | 닭볶음탕 | 6 | 0.875 |
| 김치찌개 | 동태찌개 | 6 | 0.85 |
| 물냉면 | 비빔냉면 | 6 | 0.925 |
| 순두부찌개 | 김치찌개 | 6 | 0.8916666666666667 |
| 양념치킨 | 후라이드치킨 | 6 | 0.9083333333333333 |
| 갈비구이 | 갈비찜 | 5 | 0.7916666666666666 |
| 닭계장 | 감자탕 | 5 | 0.8583333333333333 |
| 떡갈비 | 갈비구이 | 5 | 0.9083333333333333 |
| 약식 | 잡곡밥 | 5 | 0.9083333333333333 |
| 잔치국수 | 칼국수 | 5 | 0.875 |
| 족발 | 보쌈 | 5 | 0.9333333333333333 |
| 갈비구이 | 떡갈비 | 4 | 0.7916666666666666 |
| 갈비구이 | 삼겹살 | 4 | 0.7916666666666666 |
