# Glucose Safety Wording Audit

- Date: 2026-05-25
- Scope: API constants, enriched forecast response policy, UX/docs wording
- Result: pass with pilot caveats

## Checked

| Area | Status | Notes |
|---|---|---|
| product positioning | pass | wellness/dietary support only |
| reference notice | pass | explicitly says reference-only and not diagnosis/treatment |
| event wording | pass | uses possibility signal wording |
| 90m uncertainty | pass | 90m uncertainty message required when interval config exists |
| treatment language | pass | API messages do not instruct insulin/medication changes |
| K-Food classifier protection | pass | classifier code/checkpoints/weights not modified |

## Required Runtime Fields

- `reference_notice`
- `risk_interpretation`
- `safety_warning`
- `prediction_intervals_mg_dl` for enriched forecasts when model artifacts exist
- `uncertainty_level`
- `uncertainty_message`
- `risk_messages` using possibility/signal wording

## Remaining Caveats

- A UI must not hide the reference notice below the fold.
- 90m prediction should be displayed as range-first, not point-first.
- External validation is still required before broader user claims.

