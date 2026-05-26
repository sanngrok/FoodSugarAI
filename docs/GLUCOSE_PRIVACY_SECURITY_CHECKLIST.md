# Glucose Privacy and Security Checklist

- Date: 2026-05-25

## Before Internal Beta

- [x] Reference-only safety wording exists.
- [x] Prediction interval and uncertainty fields exist for enriched CGM forecasts.
- [x] Raw glucose logging policy is documented.
- [x] Log masking helper exists.
- [ ] Storage encryption verified in deployment environment.
- [ ] Deletion request owner assigned.
- [ ] Pilot consent reviewed.
- [ ] API latency measured.

## Before Limited User Pilot

- [ ] User consent finalized.
- [ ] Data retention schedule approved.
- [ ] User ID separated from health data.
- [ ] Raw request/response logs disabled or masked.
- [ ] Food image storage access restricted.
- [ ] CGM import/export path documented.
- [ ] Monitoring dashboard excludes raw glucose values.
- [ ] Incident response path defined.

## Never Log Directly

- raw CGM sequence
- insulin/bolus values
- basal rates
- exact meal timestamps
- food images
- user identifiers
- free-text notes before redaction

