"""Create the model/data bundle required by a server-style backend deploy."""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path


DEFAULT_OUTPUT = Path("artifacts/foodsugar_server_artifacts.tar.gz")


def _read_ensemble_paths(config_path: Path) -> set[Path]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paths: set[Path] = {config_path}
    for member in config.get("models", []):
        for key in ("checkpoint", "metadata", "classes"):
            value = member.get(key)
            if value:
                paths.add(Path(value))
    return paths


def collect_paths() -> list[Path]:
    paths = _read_ensemble_paths(Path("config/kfood_production_ensemble_config.json"))
    paths.update(
        [
            Path("data/models/xgboost_sugar.pkl"),
            Path("data/processed/kfood_nutrition_db.json"),
            Path("data/processed/nutrition_db_real.json"),
        ]
    )
    for model_dir in [
        Path("data/processed/glucose_models"),
        Path("data/processed/glucose_models_enriched"),
    ]:
        if model_dir.exists():
            paths.update(path for path in model_dir.rglob("*") if path.is_file())
    return sorted(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    paths = collect_paths()
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("Missing required artifact files:\n" + "\n".join(missing))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.output, "w:gz") as archive:
        for path in paths:
            archive.add(path, arcname=path.as_posix())

    size_mb = args.output.stat().st_size / 1024 / 1024
    print(f"Wrote {args.output} ({size_mb:.1f} MB, {len(paths)} files)")


if __name__ == "__main__":
    main()
