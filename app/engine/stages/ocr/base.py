"""
Base OCR Interface
"""

from abc import ABC, abstractmethod


class OCRBackend(ABC):

    @abstractmethod
    def read(self, image, preprocess=True):
        """
        Perform OCR on an image.

        Parameters
        ----------
        image : ndarray | str | Path
        preprocess : bool
            Whether the backend should apply its own preprocessing
            (backends without any simply ignore it).

        Returns
        -------
        list | dict
        """
        pass

    def read_batch(self, images, preprocess=True):
        """
        Perform OCR on several images in whatever way is most efficient
        for this backend. Default: one read() call per image -- a backend
        that can do better (e.g. ParseqBackend, a single subprocess
        round-trip + stacked forward pass for the whole batch) overrides
        this.

        Parameters
        ----------
        images : list[ndarray | str | Path]

        Returns
        -------
        list[dict], same order as images
        """
        return [self.read(image, preprocess=preprocess) for image in images]
