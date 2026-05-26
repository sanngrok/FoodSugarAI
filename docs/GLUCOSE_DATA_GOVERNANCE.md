# Glucose Data Governance

- Date: 2026-05-25
- Scope: FoodSugar AI wellness pilot

## Data Classification

| Data | Sensitivity | Policy |
|---|---|---|
| food image | sensitive personal context | store only with consent |
| CGM readings | sensitive health-related data | encrypt and minimize |
| insulin/bolus/basal inputs | highly sensitive | optional, masked in logs |
| exercise/sleep | personal wellness data | minimize |
| model predictions | derived health-related data | keep with model version |
| app logs | operational data | never include raw health values |

## Retention

Recommended pilot retention:

- raw food images: delete or de-identify after analysis window, default 90 days
- raw CGM readings: default 180 days unless user withdraws earlier
- derived aggregate metrics: keep only de-identified summaries
- logs: 30 days, masked only

## Deletion Request Flow

1. Receive deletion request.
2. Verify the requester through the pilot account channel.
3. Resolve `user_id` from identity store.
4. Delete or anonymize food images, CGM readings, meal events, predictions, feedback.
5. Remove join keys where deletion is not possible in aggregate reports.
6. Record deletion completion event without raw health data.

## Separation Principle

- Identity store and health event store should be separate.
- Pilot data and research benchmark data should be separate.
- Model artifacts should reference dataset version, not raw user identity.

## Encryption Assumptions

- Encrypt at rest for raw food images and CGM/event tables.
- Use TLS in transit.
- Restrict access by role.
- Keep secrets out of code and reports.

