"""Physical display profiles for LAB Pocket game frames."""
from PIL import Image

PANELS = (480, 720)


def render_panel(image, size):
    """Fill the physical square. At 720, source pixels cover four or five pixels."""
    if type(size) is not int or size not in PANELS or image.size != (160, 160):
        raise ValueError("Choose a 480 or 720 pixel panel and a 160 × 160 game canvas.")
    return image.resize((size, size), Image.Resampling.NEAREST)
