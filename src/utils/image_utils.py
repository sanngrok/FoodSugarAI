from io import BytesIO
from pathlib import Path

from PIL import Image


def load_image(source: bytes | str | Path) -> Image.Image:
    """bytes, 파일 경로, Path 어디서든 PIL Image 반환"""
    if isinstance(source, bytes):
        return Image.open(BytesIO(source)).convert("RGB")
    return Image.open(source).convert("RGB")


def validate_image(data: bytes, max_mb: int = 10) -> None:
    """크기 및 포맷 검증. 문제 있으면 ValueError 발생."""
    if len(data) > max_mb * 1024 * 1024:
        raise ValueError(f"이미지 크기가 {max_mb}MB를 초과합니다.")
    try:
        img = Image.open(BytesIO(data))
        img.verify()
    except Exception as e:
        raise ValueError(f"유효하지 않은 이미지 파일입니다: {e}")


def image_to_base64(img: Image.Image, fmt: str = "JPEG") -> str:
    import base64
    buf = BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode()
