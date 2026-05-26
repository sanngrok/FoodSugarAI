# K-Food Model Evaluation

- name: `b3_cont_fixed_v1_none`
- checkpoint: `data/models/efficientnet_korean_b3_cont_fixed_v1.pt`
- metadata: `data/models/korean_food_model_meta_b3_cont_fixed_v1.json`
- classes: `data/models/korean_food_classes_b3_cont_fixed_v1.json`
- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- model_type: `timm_classifier`
- model_name: `efficientnet_b3`
- image_size: `300`
- tta: `none`
- val_top1: `0.893154761904762`
- val_top3: `0.9724702380952381`
- macro_f1: `0.8929091781856305`
- num_classes: `56`
- num_samples: `6720`
