"""Download and unpack server deploy artifacts when a bundle URL is provided."""

from __future__ import annotations

import os
import tarfile
import urllib.request
from pathlib import Path


REQUIRED_PATHS = [
    Path("config/kfood_production_ensemble_config.json"),
    Path("data/models/efficientnet_korean_b3_full_fixed_v1.pt"),
    Path("data/processed/glucose_models_enriched/glucose_forecast_90m.joblib"),
]


def _required_artifacts_exist() -> bool:
    return all(path.exists() for path in REQUIRED_PATHS)


def main() -> None:
    if _required_artifacts_exist():
        print("Server artifacts already present.")
        return

    bundle_url = os.getenv("FOODSUGAR_MODEL_BUNDLE_URL", "").strip()
    if not bundle_url:
        missing = ", ".join(str(path) for path in REQUIRED_PATHS if not path.exists())
        print(f"FOODSUGAR_MODEL_BUNDLE_URL is not set; missing artifacts: {missing}")
        return

    target = Path("/tmp/foodsugar_server_artifacts.tar.gz")
    print(f"Downloading FoodSugar server artifacts from {bundle_url}")
    urllib.request.urlretrieve(bundle_url, target)

    print("Unpacking FoodSugar server artifacts")
    with tarfile.open(target, "r:gz") as archive:
        archive.extractall(Path("."))

    if not _required_artifacts_exist():
        missing = ", ".join(str(path) for path in REQUIRED_PATHS if not path.exists())
        raise SystemExit(f"Artifact bundle unpacked, but required files are still missing: {missing}")

    print("Server artifacts are ready.")


if __name__ == "__main__":
    main()
