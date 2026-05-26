# Korean Food CGM Validation Plan

- Date: 2026-05-25

## Goal

한국 음식 사진 기반 서비스 흐름이 실제 CGM 반응과 어느 정도 연결되는지 검증한다.

## Flow

```text
food image
-> K-Food classifier
-> user-confirmed food label
-> nutrition estimate
-> glucose risk score
-> CGM 30/60/90m observation
-> forecast/error/signal analysis
```

## Required Labels

- model food prediction
- user-corrected food name
- portion estimate
- meal timestamp with timezone
- CGM readings around meal
- exercise/sleep context when available

## Metrics

- food classification top1 after user correction
- nutrition estimate disagreement rate
- carb estimate error bucket
- post-meal CGM rise at 30/60/90m
- forecast error by food category
- risk score vs observed glucose rise correlation
- user misunderstanding rate

## Limitations

- Korean mixed dishes have variable recipes and portions.
- Side dishes and shared meals make image-to-nutrition mapping noisy.
- CGM lag and sensor error can affect short-horizon labels.
- Individual response varies by insulin sensitivity, activity, sleep, stress, and medication.

