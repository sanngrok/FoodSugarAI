"""
AIHub 한국 음식 이미지 데이터셋 구조/클래스 집계 도구.

사용법:
    python -m src.data.inspect_kfood \
        --root "/Users/sangrok/Downloads/한국 음식 이미지/kfood"
"""

from __future__ import annotations

import argparse
import csv
import logging
import unicodedata
from dataclasses import dataclass
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_ROOT = Path("/Users/sangrok/Downloads/한국 음식 이미지/kfood")
DEFAULT_OUTPUT = Path("data/processed/kfood_class_counts.csv")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass(frozen=True)
class KFoodClassSummary:
    category: str
    class_name: str
    image_count: int
    sample_path: str


def _normalize_name(value: str) -> str:
    """macOS 한글 자모 분리 경로를 사람이 읽기 좋은 NFC 형태로 정규화."""
    return unicodedata.normalize("NFC", value)


def _is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def collect_class_counts(root: Path) -> list[KFoodClassSummary]:
    if not root.exists():
        raise FileNotFoundError(f"kfood root not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"kfood root is not a directory: {root}")

    summaries: list[KFoodClassSummary] = []

    for category_dir in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: _normalize_name(p.name)):
        for class_dir in sorted((p for p in category_dir.iterdir() if p.is_dir()), key=lambda p: _normalize_name(p.name)):
            images = sorted((p for p in class_dir.iterdir() if _is_image(p)), key=lambda p: p.name)
            summaries.append(
                KFoodClassSummary(
                    category=_normalize_name(category_dir.name),
                    class_name=_normalize_name(class_dir.name),
                    image_count=len(images),
                    sample_path=str(images[0]) if images else "",
                )
            )

    return summaries


def write_csv(summaries: list[KFoodClassSummary], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["category", "class_name", "image_count", "sample_path"],
        )
        writer.writeheader()
        for item in summaries:
            writer.writerow(
                {
                    "category": item.category,
                    "class_name": item.class_name,
                    "image_count": item.image_count,
                    "sample_path": item.sample_path,
                }
            )


def print_summary(summaries: list[KFoodClassSummary], preview: int) -> None:
    total_images = sum(item.image_count for item in summaries)
    categories = sorted({item.category for item in summaries})
    empty_classes = [item for item in summaries if item.image_count == 0]

    logger.info("대분류 수: %d", len(categories))
    logger.info("음식 클래스 수: %d", len(summaries))
    logger.info("이미지 수: %d", total_images)

    if empty_classes:
        logger.warning("이미지가 없는 클래스: %d개", len(empty_classes))

    logger.info("이미지 수 상위 %d개 클래스:", min(preview, len(summaries)))
    for item in sorted(summaries, key=lambda x: x.image_count, reverse=True)[:preview]:
        logger.info("  %s/%s: %d", item.category, item.class_name, item.image_count)


def main() -> None:
    parser = argparse.ArgumentParser(description="AIHub kfood 클래스/이미지 수 집계")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="kfood 데이터셋 루트")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="CSV 저장 경로")
    parser.add_argument("--preview", type=int, default=20, help="터미널에 보여줄 상위 클래스 개수")
    args = parser.parse_args()

    summaries = collect_class_counts(args.root)
    write_csv(summaries, args.output)
    print_summary(summaries, args.preview)
    logger.info("CSV 저장 완료: %s", args.output)


if __name__ == "__main__":
    main()
