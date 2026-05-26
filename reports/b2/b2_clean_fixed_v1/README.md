# B2 Clean Fixed V1 Training

- status: `interrupted_after_epoch4_checkpoint_due_to_extreme_runtime_slowdown`
- checkpoint: `data/models/efficientnet_korean_b2_clean_fixed_v1.pt`
- data_dir: `data/raw/korean_food_fixed_v1`
- model_name: `efficientnet_b2`
- image_size: `260`
- best_epoch: `4`
- val_top1: `0.8339285714285715`
- val_top3: `0.953125`
- macro_f1: `0.8335263399815835`

The original 20-epoch run was stopped because epoch runtime became abnormally long. The epoch 4 best checkpoint was preserved and evaluated as the B2 clean candidate.
