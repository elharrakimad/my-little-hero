"""Wrap logical Arabic text first, then shape/reorder each printed line."""
import re
from functools import lru_cache
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable

ARABIC = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]")
RESHAPER = arabic_reshaper.ArabicReshaper(configuration={
    "delete_harakat": False, "shift_harakat_position": True})


def has_arabic(text):
    return bool(ARABIC.search(str(text)))


@lru_cache(maxsize=4096)
def visual_line(text):
    text = re.sub(r"[\u202a-\u202e\u2066-\u2069]", "", str(text))
    return get_display(RESHAPER.reshape(text), base_dir="R")


class ArabicParagraph(Flowable):
    def __init__(self, text, font, size, leading, centered=False):
        super().__init__()
        self.text, self.font, self.size = str(text), font, size
        self.leading, self.centered = leading, centered
        self.logical_lines = []

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.logical_lines = []
        for block in self.text.splitlines() or [""]:
            line = ""
            for word in block.split():
                candidate = (line + " " + word).strip()
                if line and pdfmetrics.stringWidth(visual_line(candidate), self.font, self.size) > availWidth:
                    self.logical_lines.append(line)
                    line = word
                else:
                    line = candidate
                if pdfmetrics.stringWidth(visual_line(line), self.font, self.size) > availWidth:
                    raise ValueError("Mot arabe trop long pour la zone de texte.")
            self.logical_lines.append(line)
        self.height = len(self.logical_lines) * self.leading
        return self.width, self.height

    def draw(self):
        self.canv.setFillColorRGB(0, 0, 0)
        self.canv.setFont(self.font, self.size)
        for index, line in enumerate(self.logical_lines):
            text = visual_line(line)
            y = self.height - self.size - index * self.leading
            if self.centered:
                self.canv.drawCentredString(self.width / 2, y, text)
            else:
                self.canv.drawRightString(self.width, y, text)
