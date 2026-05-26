# Suggested Data Actions

## 1. Label Review Priority

Review `high_confidence_errors_top300.csv` first. These are the cases where the model was most confident but wrong.

Review criteria:

- Is the label actually wrong?
- Does the image contain multiple foods?
- Is the target food too small or occluded?
- Is the class definition ambiguous?
- Does this pair overlap visually with another class?

## 2. Class-Specific Actions

### Soup/stew/tang classes

- Prioritize label review for 동태찌개, 김치찌개, 순두부찌개, 된장찌개, 곰탕_설렁탕, 갈비탕, 삼계탕.
- Add or prioritize images where distinctive ingredients are visible, not only broth color.
- Mark close-up broth-only images as ambiguous review candidates.

### Jeon classes

- Review 호박전, 감자전, 파전 confusion.
- Prefer images where ingredient texture is visible.

### Similar paired dishes

- 떡볶이/라볶이: check whether noodles are visible.
- 물냉면/비빔냉면: check broth/sauce visibility.
- 족발/보쌈: check skin/fat texture and plating ambiguity.
