import base64
import io

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

MAX_DIMENSION = 1568
MAX_FILE_SIZE_BYTES = 4_500_000


def prepare_image_for_api(image_bytes: bytes, filename: str) -> tuple[str, str]:
    """Takes raw image bytes, returns (base64_data, media_type) for the Claude API."""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")

    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    buffer = io.BytesIO()
    quality = 85
    img.save(buffer, format="JPEG", quality=quality)

    while buffer.tell() > MAX_FILE_SIZE_BYTES and quality > 30:
        buffer = io.BytesIO()
        quality -= 10
        img.save(buffer, format="JPEG", quality=quality)

    b64_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
    return b64_data, "image/jpeg"
