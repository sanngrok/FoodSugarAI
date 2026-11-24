import json
from pathlib import Path


def test_production_ensemble_config_is_valid_json():
    path = Path("config/kfood_production_ensemble_config.json")
    config = json.loads(path.read_text(encoding="utf-8"))

    assert config["name"] == "kfood_hflip_4model_weighted_2026_11_25"
    assert config["derived_from"] == "kfood_92_hflip_7model_weighted_2026_05_16"
    assert config["tta"] == "hflip"
    assert config["verified_metrics"]["top1"] >= 0.919
    assert config["verified_metrics"]["correct"] >= 6182
    assert len(config["models"]) == 4
    assert abs(sum(model["weight"] for model in config["models"]) - 1.0) < 1e-9


def test_production_ensemble_model_paths_exist():
    config = json.loads(Path("config/kfood_production_ensemble_config.json").read_text(encoding="utf-8"))

    for model in config["models"]:
        assert Path(model["checkpoint"]).exists(), model["checkpoint"]
        assert Path(model["metadata"]).exists(), model["metadata"]
        assert Path(model["classes"]).exists(), model["classes"]


def test_production_ensemble_class_order_is_identical():
    config = json.loads(Path("config/kfood_production_ensemble_config.json").read_text(encoding="utf-8"))
    class_lists = [
        json.loads(Path(model["classes"]).read_text(encoding="utf-8"))
        for model in config["models"]
    ]

    assert len(class_lists[0]) == 56
    assert all(class_lists[0] == class_list for class_list in class_lists[1:])


def test_kfood_nutrition_db_covers_production_classes():
    from src.nutrition.nutrition_db import get_nutrition

    classes = json.loads(Path("data/models/korean_food_classes_b3_full_fixed_v1.json").read_text(encoding="utf-8"))
    missing = [food_key for food_key in classes if get_nutrition(food_key) is None]

    assert missing == []
