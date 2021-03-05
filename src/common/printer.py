import logging
from typing import Optional

import escpos.printer
from PIL import Image

from common.patterns import singleton


@singleton
class Printer:
    """Send printing command to the thermal printer"""

    def __init__(self) -> None:
        self.devfile: Optional[str] = None
        self.printer: Optional[str] = None
        self.logger = logging.getLogger("Printer")

    def configure(self, devfile: str) -> None:
        """Configure line printer device file"""
        self.devfile = devfile

    def _get_printer(self) -> escpos.escpos.Escpos:
        return escpos.printer.File(self.devfile)

    def text(self, text: str) -> None:
        """Print text"""
        printer = self._get_printer()
        printer.text(text)

    def image(self, image: Image, center: bool = False) -> None:
        """Print image"""
        printer = self._get_printer()
        printer.image(image, center)

    def newline(self, count: int = 1) -> None:
        """Print newlines"""
        printer = self._get_printer()
        for _ in range(count):
            printer.text("\n")
