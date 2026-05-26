"""
음식별 영양정보 데이터베이스 (100g 기준)

우선순위:
  1. data/processed/nutrition_db_real.json   — Food-101용 실측 평균값
  2. data/processed/kfood_nutrition_db.json  — K-Food 56-class용 실측/평균값
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REAL_DB_PATH = Path("data/processed/nutrition_db_real.json")
KFOOD_DB_PATH = Path("data/processed/kfood_nutrition_db.json")


@dataclass
class NutritionInfo:
    food_name: str
    calories: float       # kcal
    carbs: float          # g  (탄수화물)
    sugar: float          # g  (당류)
    protein: float        # g
    fat: float            # g
    fiber: float          # g
    glycemic_index: float # GI 지수 (0~100)


# Food-101 한국어 이름 매핑
FOOD101_KO_NAME: dict[str, str] = {
    "apple_pie": "애플파이", "baby_back_ribs": "베이비백립", "baklava": "바클라바",
    "beef_carpaccio": "비프카르파초", "beef_tartare": "육회", "beet_salad": "비트샐러드",
    "beignets": "베녜", "bibimbap": "비빔밥", "bread_pudding": "브레드푸딩",
    "breakfast_burrito": "조식부리토", "bruschetta": "브루스케타", "caesar_salad": "시저샐러드",
    "cannoli": "카놀리", "caprese_salad": "카프레제샐러드", "carrot_cake": "당근케이크",
    "ceviche": "세비체", "cheesecake": "치즈케이크", "cheese_plate": "치즈플레이트",
    "chicken_curry": "치킨커리", "chicken_quesadilla": "치킨케사디야", "chicken_wings": "치킨윙",
    "chocolate_cake": "초콜릿케이크", "chocolate_mousse": "초콜릿무스", "churros": "추로스",
    "clam_chowder": "클램차우더", "club_sandwich": "클럽샌드위치", "crab_cakes": "크랩케이크",
    "creme_brulee": "크렘브륄레", "croque_madame": "크로크마담", "cup_cakes": "컵케이크",
    "deviled_eggs": "데빌드에그", "donuts": "도넛", "dumplings": "만두",
    "edamame": "에다마메", "eggs_benedict": "에그베네딕트", "escargots": "에스카르고",
    "falafel": "팔라펠", "filet_mignon": "필레미뇽", "fish_and_chips": "피시앤칩스",
    "foie_gras": "푸아그라", "french_fries": "감자튀김", "french_onion_soup": "프렌치어니언수프",
    "french_toast": "프렌치토스트", "fried_calamari": "프라이드칼라마리", "fried_rice": "볶음밥",
    "frozen_yogurt": "프로즌요거트", "garlic_bread": "갈릭브레드", "gnocchi": "뇨키",
    "greek_salad": "그릭샐러드", "grilled_cheese_sandwich": "그릴드치즈샌드위치",
    "grilled_salmon": "그릴드연어", "guacamole": "과카몰리", "gyoza": "교자",
    "hamburger": "햄버거", "hot_and_sour_soup": "산라탕", "hot_dog": "핫도그",
    "huevos_rancheros": "우에보스란체로스", "hummus": "후무스", "ice_cream": "아이스크림",
    "lasagna": "라자냐", "lobster_bisque": "랍스터비스크", "lobster_roll_sandwich": "랍스터롤샌드위치",
    "macaroni_and_cheese": "맥앤치즈", "macarons": "마카롱", "miso_soup": "된장국",
    "mussels": "홍합", "nachos": "나초", "omelette": "달걀말이",
    "onion_rings": "어니언링", "oysters": "굴", "pad_thai": "팟타이",
    "paella": "파에야", "pancakes": "팬케이크", "panna_cotta": "판나코타",
    "peking_duck": "오리구이", "pho": "쌀국수", "pizza": "피자",
    "pork_chop": "삼겹살구이", "poutine": "푸틴", "prime_rib": "소고기갈비",
    "pulled_pork_sandwich": "풀드포크샌드위치", "ramen": "라면", "ravioli": "라비올리",
    "red_velvet_cake": "레드벨벳케이크", "risotto": "리조또", "samosa": "사모사",
    "sashimi": "회", "scallops": "가리비", "seaweed_salad": "해초샐러드",
    "shrimp_and_grits": "새우요리", "spaghetti_bolognese": "스파게티볼로네제",
    "spaghetti_carbonara": "스파게티카르보나라", "spring_rolls": "스프링롤",
    "steak": "스테이크", "strawberry_shortcake": "딸기케이크", "sushi": "초밥",
    "tacos": "타코", "takoyaki": "타코야키", "tiramisu": "티라미수",
    "tuna_tartare": "참치타르타르", "waffles": "와플",
}

# ── 실제 DB 로드 ──────────────────────────────────────────────────────────────

def _load_real_db() -> dict[str, NutritionInfo]:
    if not REAL_DB_PATH.exists():
        logger.warning("nutrition_db_real.json 없음 — fallback 사용. "
                       "python -m src.nutrition.nutrition_db_builder 로 생성하세요.")
        return {}
    with open(REAL_DB_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    db = {}
    for food_key, d in raw.items():
        ko_name = FOOD101_KO_NAME.get(food_key, food_key)
        db[food_key] = NutritionInfo(
            food_name=ko_name,
            calories=d["calories"],
            carbs=d["carbs"],
            sugar=d["sugar"],
            protein=d["protein"],
            fat=d["fat"],
            fiber=d["fiber"],
            glycemic_index=d["glycemic_index"],
        )
    logger.debug("nutrition_db_real.json 로드: %d개", len(db))
    return db


def _load_kfood_db() -> dict[str, NutritionInfo]:
    if not KFOOD_DB_PATH.exists():
        logger.warning(
            "kfood_nutrition_db.json 없음 — "
            "python3 scripts/build_kfood_nutrition_db.py 로 생성하세요."
        )
        return {}
    with open(KFOOD_DB_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    db = {}
    for food_key, d in raw.items():
        db[food_key] = NutritionInfo(
            food_name=d.get("food_name", food_key),
            calories=d["calories"],
            carbs=d["carbs"],
            sugar=d["sugar"],
            protein=d["protein"],
            fat=d["fat"],
            fiber=d["fiber"],
            glycemic_index=d["glycemic_index"],
        )
    logger.debug("kfood_nutrition_db.json 로드: %d개", len(db))
    return db


NUTRITION_DB: dict[str, NutritionInfo] = {**_load_real_db(), **_load_kfood_db()}


def get_nutrition(food_key: str) -> Optional[NutritionInfo]:
    """음식 키로 영양정보 조회"""
    return NUTRITION_DB.get(food_key) or NUTRITION_DB.get(food_key.lower())


def get_all_food_keys() -> list[str]:
    return list(NUTRITION_DB.keys())
