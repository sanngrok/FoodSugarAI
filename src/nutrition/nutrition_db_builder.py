"""
Food-101 food_key → foodsafety_clean.csv 영양정보 매핑 빌더

Food-101 101개 클래스를 한국 식품안전나라 DB에서 키워드 검색으로 매칭하고
평균 영양정보를 계산해 nutrition_db_real.json으로 저장합니다.

사용법:
    python -m src.nutrition.nutrition_db_builder
"""

import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CLEAN_CSV = Path("data/processed/foodsafety_clean.csv")
OUTPUT    = Path("data/processed/nutrition_db_real.json")

# Food-101 food_key → 한국 식품DB 검색 키워드 매핑
# 여러 키워드는 OR 검색, 매칭된 항목의 평균값 사용
FOOD101_KR_KEYWORDS: dict[str, list[str]] = {
    "apple_pie":               ["애플파이"],
    "baby_back_ribs":          ["등갈비", "백립"],
    "baklava":                 ["바클라바"],
    "beef_carpaccio":          ["카르파초"],
    "beef_tartare":            ["육회", "타르타르"],
    "beet_salad":              ["비트샐러드", "비트 샐러드"],
    "beignets":                ["베녜", "도넛"],
    "bibimbap":                ["비빔밥"],
    "bread_pudding":           ["브레드푸딩", "식빵푸딩"],
    "breakfast_burrito":       ["부리또", "부리토"],
    "bruschetta":              ["브루스케타"],
    "caesar_salad":            ["시저샐러드", "시저 샐러드"],
    "cannoli":                 ["카놀리"],
    "caprese_salad":           ["카프레제"],
    "carrot_cake":             ["당근케이크", "당근 케이크"],
    "ceviche":                 ["세비체"],
    "cheesecake":              ["치즈케이크"],
    "cheese_plate":            ["치즈"],
    "chicken_curry":           ["치킨커리", "닭갈비", "닭고기 카레"],
    "chicken_quesadilla":      ["케사디야"],
    "chicken_wings":           ["치킨윙", "닭날개", "윙"],
    "chocolate_cake":          ["초콜릿케이크", "초코케이크"],
    "chocolate_mousse":        ["초콜릿무스", "초코무스"],
    "churros":                 ["추로스", "츄러스"],
    "clam_chowder":            ["클램차우더"],
    "club_sandwich":           ["클럽샌드위치", "샌드위치"],
    "crab_cakes":              ["크랩케이크", "게살"],
    "creme_brulee":            ["크렘브륄레"],
    "croque_madame":           ["크로크마담"],
    "cup_cakes":               ["컵케이크"],
    "deviled_eggs":            ["달걀", "계란"],
    "donuts":                  ["도넛", "도너츠"],
    "dumplings":               ["만두"],
    "edamame":                 ["에다마메", "풋콩"],
    "eggs_benedict":           ["에그베네딕트"],
    "escargots":               ["에스카르고"],
    "falafel":                 ["팔라펠"],
    "filet_mignon":            ["안심스테이크", "소고기 안심"],
    "fish_and_chips":          ["피시앤칩스", "생선튀김"],
    "foie_gras":               ["푸아그라"],
    "french_fries":            ["감자튀김"],
    "french_onion_soup":       ["어니언수프", "양파수프"],
    "french_toast":            ["프렌치토스트"],
    "fried_calamari":          ["오징어튀김", "칼라마리"],
    "fried_rice":              ["볶음밥"],
    "frozen_yogurt":           ["프로즌요거트", "아이스요거트"],
    "garlic_bread":            ["갈릭브레드", "마늘빵"],
    "gnocchi":                 ["뇨키"],
    "greek_salad":             ["그릭샐러드", "그리스샐러드"],
    "grilled_cheese_sandwich": ["그릴드치즈", "치즈샌드위치"],
    "grilled_salmon":          ["연어구이", "연어 구이"],
    "guacamole":               ["과카몰리"],
    "gyoza":                   ["교자", "만두"],
    "hamburger":               ["햄버거"],
    "hot_and_sour_soup":       ["산라탕", "짬뽕"],
    "hot_dog":                 ["핫도그"],
    "huevos_rancheros":        ["우에보스란체로스"],
    "hummus":                  ["후무스"],
    "ice_cream":               ["아이스크림"],
    "lasagna":                 ["라자냐"],
    "lobster_bisque":          ["랍스터비스크"],
    "lobster_roll_sandwich":   ["랍스터롤"],
    "macaroni_and_cheese":     ["맥앤치즈", "마카로니"],
    "macarons":                ["마카롱"],
    "miso_soup":               ["미소국", "된장국", "된장찌개"],
    "mussels":                 ["홍합"],
    "nachos":                  ["나초"],
    "omelette":                ["오믈렛", "달걀말이", "계란말이"],
    "onion_rings":             ["어니언링"],
    "oysters":                 ["굴"],
    "pad_thai":                ["팟타이"],
    "paella":                  ["파에야"],
    "pancakes":                ["팬케이크"],
    "panna_cotta":             ["판나코타"],
    "peking_duck":             ["베이징덕", "오리구이"],
    "pho":                     ["쌀국수"],
    "pizza":                   ["피자"],
    "pork_chop":               ["돼지고기 구이", "포크찹", "삼겹살"],
    "poutine":                 ["푸틴"],
    "prime_rib":               ["프라임립", "소고기 갈비"],
    "pulled_pork_sandwich":    ["풀드포크", "돼지고기샌드위치"],
    "ramen":                   ["라면"],
    "ravioli":                 ["라비올리"],
    "red_velvet_cake":         ["레드벨벳"],
    "risotto":                 ["리조또", "리소토"],
    "samosa":                  ["사모사"],
    "sashimi":                 ["회", "사시미"],
    "scallops":                ["가리비"],
    "seaweed_salad":           ["해초샐러드", "미역무침", "해조"],
    "shrimp_and_grits":        ["새우"],
    "spaghetti_bolognese":     ["스파게티", "볼로네제"],
    "spaghetti_carbonara":     ["카르보나라"],
    "spring_rolls":            ["스프링롤", "월남쌈", "춘권"],
    "steak":                   ["스테이크", "소고기구이"],
    "strawberry_shortcake":    ["딸기케이크", "딸기 케이크"],
    "sushi":                   ["초밥", "스시"],
    "tacos":                   ["타코"],
    "takoyaki":                ["타코야키"],
    "tiramisu":                ["티라미수"],
    "tuna_tartare":            ["참치", "타르타르"],
    "waffles":                 ["와플"],
}

# foodsafety DB에 없는 항목의 fallback GI (nutrition_db.py 원본값 유지)
FALLBACK_GI: dict[str, float] = {
    "apple_pie": 65, "baby_back_ribs": 0, "baklava": 55, "beef_carpaccio": 0,
    "beef_tartare": 10, "beet_salad": 64, "beignets": 72, "bibimbap": 55,
    "bread_pudding": 68, "breakfast_burrito": 52, "bruschetta": 60,
    "caesar_salad": 15, "cannoli": 62, "caprese_salad": 30, "carrot_cake": 69,
    "ceviche": 25, "cheesecake": 65, "cheese_plate": 10, "chicken_curry": 40,
    "chicken_quesadilla": 55, "chicken_wings": 0, "chocolate_cake": 75,
    "chocolate_mousse": 70, "churros": 76, "clam_chowder": 42,
    "club_sandwich": 52, "crab_cakes": 38, "creme_brulee": 65,
    "croque_madame": 50, "cup_cakes": 72, "deviled_eggs": 0, "donuts": 76,
    "dumplings": 55, "edamame": 18, "eggs_benedict": 48, "escargots": 0,
    "falafel": 42, "filet_mignon": 0, "fish_and_chips": 62, "foie_gras": 5,
    "french_fries": 75, "french_onion_soup": 35, "french_toast": 65,
    "fried_calamari": 40, "fried_rice": 64, "frozen_yogurt": 50,
    "garlic_bread": 73, "gnocchi": 68, "greek_salad": 15, "grilled_cheese_sandwich": 55,
    "grilled_salmon": 0, "guacamole": 40, "gyoza": 52, "hamburger": 61,
    "hot_and_sour_soup": 30, "hot_dog": 60, "huevos_rancheros": 45,
    "hummus": 30, "ice_cream": 61, "lasagna": 55, "lobster_bisque": 35,
    "lobster_roll_sandwich": 52, "macaroni_and_cheese": 64, "macarons": 78,
    "miso_soup": 20, "mussels": 0, "nachos": 72, "omelette": 0,
    "onion_rings": 70, "oysters": 0, "pad_thai": 58, "paella": 55,
    "pancakes": 67, "panna_cotta": 55, "peking_duck": 5, "pho": 47,
    "pizza": 60, "pork_chop": 0, "poutine": 65, "prime_rib": 0,
    "pulled_pork_sandwich": 52, "ramen": 55, "ravioli": 60,
    "red_velvet_cake": 72, "risotto": 62, "samosa": 58, "sashimi": 0,
    "scallops": 0, "seaweed_salad": 18, "shrimp_and_grits": 52,
    "spaghetti_bolognese": 55, "spaghetti_carbonara": 55, "spring_rolls": 58,
    "steak": 0, "strawberry_shortcake": 66, "sushi": 52, "tacos": 55,
    "takoyaki": 60, "tiramisu": 65, "tuna_tartare": 10, "waffles": 76,
}


def build(clean_csv: Path = CLEAN_CSV, output: Path = OUTPUT) -> dict:
    df = pd.read_csv(clean_csv)
    logger.info("식품DB 로드: %d건", len(df))

    result = {}
    matched = 0
    fallback = 0

    for food_key, keywords in FOOD101_KR_KEYWORDS.items():
        pattern = "|".join(keywords)
        hits = df[df["food_name"].str.contains(pattern, na=False)]

        gi = FALLBACK_GI.get(food_key, 50)

        if len(hits) >= 3:
            avg = hits[["calories", "carbs", "sugar", "protein", "fat", "fiber"]].mean()
            result[food_key] = {
                "calories":      round(float(avg["calories"]), 1),
                "carbs":         round(float(avg["carbs"]), 1),
                "sugar":         round(float(avg["sugar"]), 1),
                "protein":       round(float(avg["protein"]), 1),
                "fat":           round(float(avg["fat"]), 1),
                "fiber":         round(float(avg["fiber"]), 1),
                "glycemic_index": gi,
                "sample_count":  len(hits),
                "source":        "foodsafety_db",
            }
            matched += 1
        else:
            # 매칭 부족 → nutrition_db.py 원본 수치 유지 (fallback)
            from src.nutrition.nutrition_db import NUTRITION_DB
            orig = NUTRITION_DB.get(food_key)
            if orig:
                result[food_key] = {
                    "calories":       orig.calories,
                    "carbs":          orig.carbs,
                    "sugar":          orig.sugar,
                    "protein":        orig.protein,
                    "fat":            orig.fat,
                    "fiber":          orig.fiber,
                    "glycemic_index": orig.glycemic_index,
                    "sample_count":   0,
                    "source":         "manual_fallback",
                }
            fallback += 1

    logger.info("매핑 완료: foodsafety DB=%d개, fallback=%d개 / 전체 101개", matched, fallback)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info("저장: %s", output)
    return result


if __name__ == "__main__":
    build()
