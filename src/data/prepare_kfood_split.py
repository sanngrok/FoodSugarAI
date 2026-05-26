"""
AIHub 한국 음식 이미지 데이터셋을 torchvision ImageFolder 학습 구조로 준비.

기본 동작:
  - 혈당/실사용 우선 클래스만 선택
  - 클래스당 최대 600장 사용
  - train/val = 80/20 split
  - 이미지 복사 대신 symlink 생성

사용법:
    python3 -m src.data.prepare_kfood_split \
        --source-root "/Users/sangrok/Downloads/한국 음식 이미지/kfood" \
        --output-dir data/raw/korean_food
"""

from __future__ import annotations

import argparse
import csv
import logging
import random
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_SOURCE_ROOT = Path("/Users/sangrok/Downloads/한국 음식 이미지/kfood")
DEFAULT_OUTPUT_DIR = Path("data/raw/korean_food")
DEFAULT_MANIFEST_PATH = Path("data/processed/kfood_split_manifest.csv")
DEFAULT_SELECTED_CLASSES_PATH = Path("data/processed/kfood_selected_classes.txt")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# 1차 실험용: 혈당 분석/일상 한식 사용성에 영향이 큰 클래스 위주.
DEFAULT_PRIORITY_CLASSES = [
    "김밥",
    "김치볶음밥",
    "비빔밥",
    "새우볶음밥",
    "알밥",
    "유부초밥",
    "잡곡밥",
    "주먹밥",
    "라면",
    "물냉면",
    "비빔냉면",
    "수제비",
    "잔치국수",
    "짜장면",
    "짬뽕",
    "쫄면",
    "칼국수",
    "떡볶이",
    "라볶이",
    "만두",
    "김치찌개",
    "된장찌개",
    "순두부찌개",
    "동태찌개",
    "닭계장",
    "갈비탕",
    "감자탕",
    "곰탕_설렁탕",
    "삼계탕",
    "갈비구이",
    "고등어구이",
    "닭갈비",
    "떡갈비",
    "불고기",
    "삼겹살",
    "훈제오리",
    "감자전",
    "김치전",
    "파전",
    "호박전",
    "계란말이",
    "갈비찜",
    "김치찜",
    "닭볶음탕",
    "순대",
    "족발",
    "찜닭",
    "보쌈",
    "양념치킨",
    "후라이드치킨",
    "피자",
    "약과",
    "약식",
    "한과",
    "식혜",
    "수정과",
]


@dataclass(frozen=True)
class ClassImages:
    category: str
    class_name: str
    class_dir: Path
    images: list[Path]


def _normalize_name(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def discover_classes(source_root: Path) -> dict[str, ClassImages]:
    if not source_root.exists():
        raise FileNotFoundError(f"source root not found: {source_root}")

    classes: dict[str, ClassImages] = {}
    for category_dir in sorted((p for p in source_root.iterdir() if p.is_dir()), key=lambda p: _normalize_name(p.name)):
        for class_dir in sorted((p for p in category_dir.iterdir() if p.is_dir()), key=lambda p: _normalize_name(p.name)):
            class_name = _normalize_name(class_dir.name)
            images = sorted((p for p in class_dir.iterdir() if _is_image(p)), key=lambda p: p.name)
            if class_name in classes:
                raise ValueError(f"duplicate class name found: {class_name}")
            classes[class_name] = ClassImages(
                category=_normalize_name(category_dir.name),
                class_name=class_name,
                class_dir=class_dir,
                images=images,
            )
    return classes


def read_classes(path: Path) -> list[str]:
    return [
        _normalize_name(line.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def reset_split_dir(output_dir: Path) -> None:
    for split in ("train", "val"):
        split_dir = output_dir / split
        if split_dir.exists():
            shutil.rmtree(split_dir)
        split_dir.mkdir(parents=True, exist_ok=True)


def place_file(source: Path, target: Path, mode: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "symlink":
        target.symlink_to(source.resolve())
    elif mode == "hardlink":
        target.hardlink_to(source.resolve())
    elif mode == "copy":
        shutil.copy2(source, target)
    else:
        raise ValueError(f"unknown mode: {mode}")


def write_manifest(rows: list[dict[str, str]], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["split", "category", "class_name", "source_path", "target_path"],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_selected_classes(selected_classes: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(selected_classes) + "\n", encoding="utf-8")


def prepare_split(
    source_root: Path,
    output_dir: Path,
    selected_classes: list[str],
    max_per_class: int,
    val_ratio: float,
    seed: int,
    mode: str,
    manifest_path: Path,
    selected_classes_path: Path,
) -> None:
    classes = discover_classes(source_root)
    missing = [name for name in selected_classes if name not in classes]
    if missing:
        raise ValueError(f"selected classes not found in source: {', '.join(missing)}")

    rng = random.Random(seed)
    reset_split_dir(output_dir)

    manifest_rows: list[dict[str, str]] = []
    train_count = 0
    val_count = 0

    for class_name in selected_classes:
        item = classes[class_name]
        images = item.images[:]
        rng.shuffle(images)
        if max_per_class > 0:
            images = images[:max_per_class]

        val_size = max(1, round(len(images) * val_ratio))
        val_images = set(images[:val_size])

        for source in images:
            split = "val" if source in val_images else "train"
            target = output_dir / split / class_name / source.name
            place_file(source, target, mode)
            manifest_rows.append(
                {
                    "split": split,
                    "category": item.category,
                    "class_name": class_name,
                    "source_path": str(source),
                    "target_path": str(target),
                }
            )
            if split == "val":
                val_count += 1
            else:
                train_count += 1

    write_manifest(manifest_rows, manifest_path)
    write_selected_classes(selected_classes, selected_classes_path)

    logger.info("선택 클래스 수: %d", len(selected_classes))
    logger.info("학습 이미지: %d장", train_count)
    logger.info("검증 이미지: %d장", val_count)
    logger.info("출력 디렉터리: %s", output_dir)
    logger.info("manifest 저장: %s", manifest_path)
    logger.info("선택 클래스 저장: %s", selected_classes_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="AIHub kfood train/val split 생성")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--classes-file", type=Path, default=None, help="사용할 클래스명 목록(txt)")
    parser.add_argument("--all-classes", action="store_true", help="전체 150개 클래스 사용")
    parser.add_argument("--max-per-class", type=int, default=600, help="클래스당 최대 이미지 수. 0이면 전체 사용")
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=["symlink", "hardlink", "copy"], default="symlink")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--selected-classes-output", type=Path, default=DEFAULT_SELECTED_CLASSES_PATH)
    args = parser.parse_args()

    discovered = discover_classes(args.source_root)
    if args.all_classes:
        selected_classes = sorted(discovered, key=_normalize_name)
    elif args.classes_file:
        selected_classes = read_classes(args.classes_file)
    else:
        selected_classes = DEFAULT_PRIORITY_CLASSES

    prepare_split(
        source_root=args.source_root,
        output_dir=args.output_dir,
        selected_classes=selected_classes,
        max_per_class=args.max_per_class,
        val_ratio=args.val_ratio,
        seed=args.seed,
        mode=args.mode,
        manifest_path=args.manifest,
        selected_classes_path=args.selected_classes_output,
    )


if __name__ == "__main__":
    main()
