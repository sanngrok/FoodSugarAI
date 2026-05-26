# Glucose Logging Policy

- Date: 2026-05-25

## Allowed Log Fields

- request id
- endpoint name
- model version
- horizons requested
- count of CGM readings
- count of meal/bolus/basal events
- latency
- success/failure status
- validation error class

## Disallowed Log Fields

- raw `glucose_mg_dl` values
- full CGM reading arrays
- raw insulin/bolus/basal values
- exact user meal timestamps
- food image bytes or direct public URLs
- user name, email, phone, or direct identifier
- unredacted free-text notes

## Masking Rule

Use `src.glucose.privacy.mask_glucose_payload_for_log()` before logging any glucose request shape. The masked payload may include event counts but not raw health values.

## Example

```json
{
  "endpoint": "/predict/cgm-forecast-enriched-events",
  "readings_count": 13,
  "readings": "[masked]",
  "meals_count": 1,
  "meals": "[masked]",
  "bolus_count": 1,
  "bolus": "[masked]"
}
```

