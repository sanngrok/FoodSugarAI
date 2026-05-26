# Suspect 7 AI Visual Draft Review

- 작성일: 2026-05-10
- 입력: `reports/cleaned_v1/train_hard_review/train_hard_review_suspects.csv`
- contact sheet: `reports/cleaned_v1/train_hard_review/suspect_contact_sheets/review_sheet_001.jpg`
- 출력: `reports/cleaned_v1/train_hard_review/suspect_ai_visual_review.csv`

## 주의

이 파일은 운영 확정용 human review가 아니다. 이미지 기반 AI visual draft 검토 결과이므로 `cleaned_v1` 확정 patch로 바로 승격하지 않는다.

## 결과 요약

- total reviewed: 7
- proposed remove: 2
- proposed relabel: 4
- proposed keep/model_error: 1
- apply_to_ai_candidate=yes: 6
- apply_to_ai_candidate=no: 1

## 핵심 변경 판단

`족발/Img_131_0545.jpg`는 기존 AI draft와 ensemble이 `닭갈비` relabel 쪽으로 의심했지만, 확대 확인 결과 시장 진열대의 족발 이미지로 보인다. 따라서 이 항목은 relabel하지 않고 `keep` 후보로 내린다.

## 현재 의미

이번 7개 검토 후에도 train correction 후보 규모는 크게 늘지 않는다.

- 기존 AI draft train affected: 49
- 이번 검토에서 기존 후보 중 keep으로 내린 항목: 1
- 이번 검토에서 신규로 추가 가능한 후보: 2
- 순증 효과: 약 +1

따라서 아직 B0/B3 재학습을 시작하기에는 train label 개선 규모가 작다.
