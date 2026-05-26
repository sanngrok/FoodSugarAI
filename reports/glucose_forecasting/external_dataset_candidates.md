# External Dataset Candidates

- Date: 2026-05-25
- Purpose: plan validation beyond OhioT1DM

## Candidates

| Candidate | What it can validate | Key limitation |
|---|---|---|
| OhioT1DM held-out test | current benchmark continuation | already used in current pipeline |
| public CGM challenge datasets | CGM-only forecasting robustness | event schema may differ |
| consented internal pilot | real app behavior | small sample and privacy setup needed |
| Korean food CGM pilot | target product flow | requires recruitment and food confirmation |
| device export samples | device-specific timestamp/cadence issues | consent and format variability |

## Minimum External Validation Questions

- Does 30m MAE remain acceptable outside OhioT1DM?
- Does 90m interval coverage remain around the target coverage?
- Are hypo/hyper possibility signals understandable to users?
- Does Korean-food nutrition estimation correlate with observed post-meal CGM response?

## Current Decision

Do not expand claims beyond a safe wellness pilot until at least one non-OhioT1DM or user-pilot dataset has been evaluated.

