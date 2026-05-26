# K-Food Model Evaluation

- name: `b3_probe_fixed_v1_hflip`
- checkpoint: `data/models/efficientnet_korean_b3_probe_fixed_v1.pt`
- metadata: `data/models/korean_food_model_meta_b3_probe_fixed_v1.json`
- classes: `data/models/korean_food_classes_b3_probe_fixed_v1.json`
- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- model_type: `timm_classifier`
- model_name: `efficientnet_b3`
- image_size: `300`
- tta: `hflip`
- val_top1: `0.8888392857142857`
- val_top3: `0.9723214285714286`
- macro_f1: `0.8887008612156023`
- num_classes: `56`
- num_samples: `6720`
