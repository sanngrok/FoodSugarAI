# Current Best High-Confidence Top300 AI Draft Review

- 작성일: 2026-05-13
- 입력: `reports/current_best/error_analysis/current_best_high_conf_review_top300.csv`
- 출력: `reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_AI_DRAFT.csv`
- 근거 이미지: `reports/current_best/error_analysis/contact_sheets_top300/review_sheet_001.jpg` ~ `review_sheet_012.jpg`
- 범위: current best 3-model weighted ensemble + hflip의 high-confidence validation 오류 후보 top300

## Important Limitation

이 파일은 사람이 원본 이미지를 확정 검수한 결과가 아니라 Codex가 contact sheet를 보고 만든 **AI visual draft**입니다. 운영 확정 `cleaned_v1` 생성에는 바로 쓰지 말고, 사람이 확인하기 위한 초안 또는 `cleaned_candidate` 실험 후보로만 사용해야 합니다.

## Summary

- 총 검수 후보: 300
- relabel 후보: 129
- keep/model_error 후보: 112
- remove 후보: 25
- needs_human_review 후보: 34

## Status Counts

- `wrong_label`: 129
- `model_error`: 112
- `ambiguous`: 34
- `multi_food`: 23
- `bad_crop`: 2

## Action Counts

- `relabel`: 129
- `keep`: 112
- `needs_human_review`: 34
- `remove`: 25

## Top Corrected Labels

- `수제비`: 10
- `닭볶음탕`: 9
- `동태찌개`: 7
- `닭갈비`: 6
- `보쌈`: 5
- `칼국수`: 5
- `파전`: 5
- `갈비탕`: 5
- `호박전`: 5
- `김치찌개`: 4
- `떡갈비`: 4
- `비빔냉면`: 3
- `갈비찜`: 3
- `감자탕`: 3
- `불고기`: 3
- `주먹밥`: 3
- `라볶이`: 3
- `순두부찌개`: 3
- `새우볶음밥`: 3
- `쫄면`: 3

## Most Affected True Labels

- `곰탕_설렁탕`: 16
- `갈비찜`: 10
- `닭계장`: 8
- `호박전`: 8
- `물냉면`: 7
- `갈비구이`: 7
- `칼국수`: 7
- `김치찜`: 7
- `수제비`: 7
- `삼겹살`: 6
- `김치찌개`: 6
- `찜닭`: 5
- `짬뽕`: 5
- `라면`: 5
- `감자전`: 5
- `떡볶이`: 4
- `족발`: 4
- `불고기`: 4
- `잔치국수`: 4
- `양념치킨`: 4

## Suggested Use

1. 사람이 `relabel`, `remove`, `needs_human_review` 행만 우선 확인한다.
2. 특히 `needs_human_review`는 patch 생성에서 제외한다.
3. `relabel`은 corrected_label이 56-class 목록에 있는지 이미 확인했지만, 운영 반영 전 원본 이미지를 다시 확인한다.
4. 이 draft만으로 B3 full 또는 운영용 cleaned split을 확정하지 않는다.

## Stop Condition Reminder

- 이 draft는 validation high-confidence 오류 후보 기반이므로, train 라벨 노이즈 개선 효과를 보장하지 않는다.
- 다음 단계에서 train 영향 audit이 약하면 cleaned training split 실험으로 바로 넘어가지 말고 보고 후 재판단한다.
