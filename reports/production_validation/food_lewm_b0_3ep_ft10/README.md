# K-Food Model Evaluation

- name: `food_lewm_b0_3ep_ft10`
- checkpoint: `data/models/food_lewm_b0_classifier_3ep_ft10.pt`
- metadata: `data/models/food_lewm_b0_meta_3ep_ft10.json`
- classes: `data/models/food_lewm_b0_classes_3ep_ft10.json`
- data_dir: `data/raw/korean_food_1000`
- model_type: `food_lewm_classifier`
- model_name: `efficientnet_b0`
- image_size: `224`
- tta: `none`
- val_top1: `0.86796498123995`
- val_top3: `0.961586564230838`
- macro_f1: `0.8680396484464304`
- num_classes: `56`
- num_samples: `11194`
