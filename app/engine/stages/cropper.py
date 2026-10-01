from app.core.config.ocr_engine_config import CropConfig


"""
Margin Cropper

Crops the page using the detected separator so that only the left
annotation region is retained for subsequent annotation detection
and OCR.
"""


class Cropper:

    def __init__(self, config: CropConfig):
        """
        config.right_padding :
            Number of pixels to include AFTER the separator.
        """

        self.right_padding = config.right_padding

    def crop(self, image, separator):

        if separator is None:
            return None

        x = separator["x"] + self.right_padding

        # Prevent overflow
        x = min(x, image.shape[1])

        cropped = image[:, :x]

        return cropped
