#!/usr/bin/env python3
"""Build contact sheets for K-Food label review CSVs."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--items-per-sheet", type=int, default=25)
    parser.add_argument("--thumb-size", type=int, default=180)
    parser.add_argument("--cols", type=int, default=5)
    return parser.parse_args()


def load_font(size: int) -> ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def fit_image(path: Path, size: int) -> Image.Image:
    with Image.open(path) as img:
        img = img.convert("RGB")
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (size, size), "white")
        left = (size - img.width) // 2
        top = (size - img.height) // 2
        canvas.paste(img, (left, top))
        return canvas


def draw_cell(
    canvas: Image.Image,
    row: dict[str, str],
    row_idx: int,
    col_idx: int,
    cell_w: int,
    cell_h: int,
    thumb_size: int,
    font: ImageFont.ImageFont,
    small_font: ImageFont.ImageFont,
) -> None:
    draw = ImageDraw.Draw(canvas)
    x = col_idx * cell_w
    y = row_idx * cell_h
    draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(210, 210, 210))

    image_path = Path(row["image_path"])
    try:
        thumb = fit_image(image_path, thumb_size)
    except Exception:
        thumb = Image.new("RGB", (thumb_size, thumb_size), (245, 220, 220))
        ImageDraw.Draw(thumb).text((8, 8), "image load failed", fill=(120, 0, 0), font=small_font)
    canvas.paste(thumb, (x + 8, y + 8))

    confidence = float(row.get("ensemble_confidence") or row.get("confidence") or 0)
    pred_label = row.get("ensemble_pred_label") or row.get("pred_label", "")
    text = "\n".join([
        f"#{row.get('rank', '')} conf {confidence:.3f}",
        f"T: {row.get('true_label', '')}",
        f"P: {pred_label}",
        Path(row.get("image_path", "")).name,
    ])
    draw.multiline_text(
        (x + 8, y + thumb_size + 14),
        text,
        fill=(20, 20, 20),
        font=font,
        spacing=2,
    )


def write_sheet(
    rows: list[dict[str, str]],
    output_path: Path,
    cols: int,
    thumb_size: int,
    font: ImageFont.ImageFont,
    small_font: ImageFont.ImageFont,
) -> None:
    cell_w = thumb_size + 20
    cell_h = thumb_size + 96
    sheet_rows = math.ceil(len(rows) / cols)
    canvas = Image.new("RGB", (cell_w * cols, cell_h * sheet_rows), "white")
    for idx, row in enumerate(rows):
        draw_cell(
            canvas,
            row,
            row_idx=idx // cols,
            col_idx=idx % cols,
            cell_w=cell_w,
            cell_h=cell_h,
            thumb_size=thumb_size,
            font=font,
            small_font=small_font,
        )
    canvas.save(output_path, quality=92)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with args.review_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    font = load_font(13)
    small_font = load_font(11)
    sheet_paths: list[Path] = []
    for start in range(0, len(rows), args.items_per_sheet):
        sheet_rows = rows[start : start + args.items_per_sheet]
        sheet_num = len(sheet_paths) + 1
        output_path = args.output_dir / f"review_sheet_{sheet_num:03d}.jpg"
        write_sheet(sheet_rows, output_path, args.cols, args.thumb_size, font, small_font)
        sheet_paths.append(output_path)

    index_lines = [
        "# K-Food Label Review Contact Sheets",
        "",
        f"- source: `{args.review_csv}`",
        f"- total_samples: `{len(rows)}`",
        f"- items_per_sheet: `{args.items_per_sheet}`",
        "",
        "## Sheets",
        "",
    ]
    for path in sheet_paths:
        index_lines.append(f"- `{path.name}`")
    (args.output_dir / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
