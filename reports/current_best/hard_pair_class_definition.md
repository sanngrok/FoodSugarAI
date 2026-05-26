# Current Best Hard Pair Class Definition

작성일: 2026-05-13  
대상 모델: B3 continuation 3-model weighted ensemble + hflip  
기준 리포트: `reports/current_best/error_analysis`

## 목적

현재 best 모델의 남은 오류는 단순 capacity 문제만이 아니라 class boundary / label ambiguity 문제가 많이 섞여 있다.  
이 문서는 high-confidence error top300과 train hard-pair 후보를 사람이 검수할 때 일관된 기준으로 사용하기 위한 class definition이다.

검수 status 권장값:

```text
model_error
wrong_label
ambiguous
multi_food
bad_crop
class_definition_overlap
unclear
```

action 권장값:

```text
keep
relabel
remove
needs_class_definition
needs_more_data
```

## 공통 원칙

1. 이미지에서 핵심 재료나 조리 방식이 명확하면 해당 class로 둔다.
2. 국물 색, 양념 색, 조명만으로 판단하지 않는다.
3. 여러 음식이 같은 비중으로 있으면 `multi_food` 또는 `ambiguous`로 둔다.
4. 음식이 작거나 가려져 핵심 단서가 부족하면 `bad_crop` 또는 `ambiguous`로 둔다.
5. 사람이 봐도 두 class 사이가 흔들리면 억지로 relabel하지 말고 `ambiguous` 또는 `class_definition_overlap`으로 표시한다.

## 곰탕_설렁탕 vs 갈비탕 vs 삼계탕

갈비탕:

- 갈비뼈, 갈비대, 뼈에 붙은 고기 형태가 명확하면 갈비탕.
- 맑은 국물이라도 갈비뼈가 보이면 갈비탕 우선.

삼계탕:

- 닭 형태, 닭다리, 통닭, 반계, 닭 속 재료가 명확하면 삼계탕.
- 뽀얀 국물이라도 닭 형태가 보이면 삼계탕 우선.

곰탕_설렁탕:

- 맑거나 뽀얀 고기국물 중심이고 갈비뼈/닭 형태가 명확하지 않으면 곰탕_설렁탕.
- 얇게 썬 고기, 파, 소면 중심의 탕 이미지가 해당된다.

Ambiguous:

- 국물만 보이거나 고기 형태가 불명확하면 ambiguous.
- 갈비뼈인지 일반 고기인지 구분되지 않으면 ambiguous 또는 needs_class_definition.

## 김치찌개 vs 동태찌개 vs 순두부찌개 vs 된장찌개

동태찌개:

- 생선살, 동태 조각, 생선 껍질/뼈 형태가 명확하면 동태찌개.
- 빨간 국물만으로는 동태찌개로 바꾸지 않는다.

김치찌개:

- 김치, 돼지고기, 두부 중심이고 생선이 명확하지 않으면 김치찌개.
- 김치찜처럼 큰 김치 덩어리와 찜 형태가 강하면 김치찜 후보도 같이 고려한다.

순두부찌개:

- 순두부 덩어리, 부드러운 두부 질감, 고추기름/찌개 구성이 명확하면 순두부찌개.

된장찌개:

- 된장 국물 색, 두부/호박/감자 등 된장찌개 재료가 명확하면 된장찌개.
- 빨간 국물 계열이면 된장찌개로 두지 않는다.

Ambiguous:

- 빨간 국물만 보이고 생선/두부/김치 특징이 불명확하면 ambiguous.
- 숟가락, 그릇, 국물 색만으로 relabel하지 않는다.

## 감자전 vs 호박전 vs 파전

감자전:

- 감자 질감, 갈린 감자 특유의 균일하고 얇은 전 형태가 명확하면 감자전.
- 채썬 감자 또는 감자전 특유의 바삭한 표면이 보이면 감자전.

호박전:

- 호박 조각, 초록/노란 호박 단면, 원형 애호박 슬라이스가 명확하면 호박전.

파전:

- 파가 길게 보이고 파가 주재료이면 파전.
- 해물/파 중심의 넓은 전도 파전으로 둔다.

Ambiguous:

- 전의 재료 texture가 보이지 않거나 일부 조각만 보이면 ambiguous.
- 감자전과 호박전이 같은 접시에 섞여 있으면 multi_food 또는 ambiguous.

## 칼국수 vs 수제비

칼국수:

- 긴 면발이 명확하면 칼국수.
- 면이 굵고 납작해도 길게 이어진 면이면 칼국수.

수제비:

- 뜯은 반죽 조각, 불규칙한 납작 반죽 형태가 명확하면 수제비.

Ambiguous:

- 국물과 반죽이 섞여 형태가 불분명하면 ambiguous.
- 면과 수제비가 같이 있으면 multi_food 또는 ambiguous.

## 갈비구이 vs 갈비찜 vs 삼겹살

갈비구이:

- 구운 고기, 불판, 석쇠, 숯불, 갈비뼈가 붙은 구이 느낌이 명확하면 갈비구이.
- 양념이 있어도 구이 맥락이 명확하면 갈비구이.

갈비찜:

- 찜 양념, 국물/소스, 그릇 안에서 조리된 형태, 당근/감자 등 찜 재료가 보이면 갈비찜.

삼겹살:

- 삼겹살의 지방층/고기층이 반복되는 단면, 불판 위 구운 삼겹살 형태가 명확하면 삼겹살.

Ambiguous:

- 고기 close-up만 있고 조리 방식이 불명확하면 ambiguous.
- 갈비인지 삼겹살인지 부위가 불명확하면 needs_class_definition 또는 ambiguous.

## 물냉면 vs 비빔냉면

물냉면:

- 육수가 명확하고 면이 국물에 잠겨 있으면 물냉면.
- 얼음/육수/맑은 국물 단서가 보이면 물냉면.

비빔냉면:

- 육수 없이 양념장 중심이고 빨간 비빔 양념이 주된 단서이면 비빔냉면.

Ambiguous:

- 육수 여부가 불명확하거나 비빔냉면에 소량 육수가 보이는 경우 ambiguous.

## 떡볶이 vs 라볶이

라볶이:

- 라면/면이 명확하면 라볶이.
- 떡과 면이 함께 있어도 면이 주요 구성으로 보이면 라볶이.

떡볶이:

- 떡 중심이고 면이 명확하지 않으면 떡볶이.

Ambiguous:

- 면이 가려져 있거나 일부만 보여 판단이 어렵다면 ambiguous.

## 양념치킨 vs 후라이드치킨

양념치킨:

- 양념 소스가 전체적으로 명확하면 양념치킨.
- 빨간/갈색 소스가 치킨 표면을 덮고 있으면 양념치킨.

후라이드치킨:

- 튀김옷 중심이고 소스가 없거나 거의 없으면 후라이드치킨.

Ambiguous:

- 부분 양념, 조명, 소스 반사 때문에 소스 여부가 불명확하면 ambiguous.

## 족발 vs 보쌈

족발:

- 껍질/콜라겐층, 진한 갈색 윤기, 족발 특유의 둥근 단면이 명확하면 족발.

보쌈:

- 삶은 돼지고기 편육 형태, 밝은 살코기/비계 층, 김치/쌈 구성과 함께 나오면 보쌈.

Ambiguous:

- 고기 close-up만 있고 껍질/편육 구분이 어렵다면 ambiguous.

## 검수 후 요약 기준

high-confidence top300 검수 후 아래 비율을 계산한다.

```text
label_boundary_noise = wrong_label + ambiguous + multi_food + bad_crop + class_definition_overlap
```

판단:

```text
label_boundary_noise >= 20%:
  label/hard-pair cleaning 우선.

label_boundary_noise 10~20%:
  cleaning과 B3 full run 병행 검토.

label_boundary_noise < 10%:
  model capacity 병목 가능성이 커서 B3 full run 가치 상승.
```

