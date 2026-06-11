import io
import logging
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

_logger = logging.getLogger(__name__)


def protect_image(
    raw_bytes,
    blur_enabled=True,
    watermark_enabled=True,
    watermark_text="Alfons Güell",
    blur_intensity=10,
    watermark_opacity=60,
    watermark_font_scale=20,
    watermark_spacing_x=2.5,
    watermark_spacing_y=3.0,
    watermark_angle=30,
    jpeg_quality=85,
):
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")

    if blur_enabled:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_intensity))

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))

    if watermark_enabled:
        draw = ImageDraw.Draw(overlay)

        font_size = max(img.size) // watermark_font_scale
        font = None
        for path in (
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ):
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except OSError:
                continue
        if font is None:
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        spacing_x = int(text_w * watermark_spacing_x)
        spacing_y = int(text_h * watermark_spacing_y)

        tile_size = (
            int(math.sqrt(spacing_x**2 + spacing_y**2)) + max(text_w, text_h) + 20
        )
        tile = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
        tile_draw = ImageDraw.Draw(tile)

        tx = (tile_size - text_w) // 2
        ty = (tile_size - text_h) // 2
        tile_draw.text(
            (tx, ty),
            watermark_text,
            fill=(255, 255, 255, int(watermark_opacity * 2.55)),
            font=font,
        )

        tile = tile.rotate(
            watermark_angle, expand=False, center=(tile_size // 2, tile_size // 2)
        )

        for y in range(-tile_size, img.size[1] + tile_size, spacing_y):
            for x in range(-tile_size, img.size[0] + tile_size, spacing_x):
                overlay.paste(tile, (x, y), tile)

    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")

    out = io.BytesIO()
    result.save(out, format="JPEG", quality=jpeg_quality)
    return out.getvalue()
