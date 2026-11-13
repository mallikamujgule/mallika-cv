#!/usr/bin/env python3
"""
install_fonts.py — make Latin Modern Roman 10 usable by the ReportLab renderer.

MacTeX ships LM Roman 10 as OpenType (CFF) files. ReportLab only reads TrueType
outlines, so this converts them to .ttf and writes them to okf/fonts/, where the
renderer looks first. The LaTeX renderer needs no conversion: pdflatex uses the
font from the TeX installation directly.

Usage: python install_fonts.py            (finds the TeX Live folder itself)
       python install_fonts.py <lm-dir>   (folder that holds lmroman10-*.otf)
"""
import glob
import os
import sys

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "okf", "fonts")
NAMES = ["regular", "bold", "italic", "bolditalic"]


def find_lm_dir(arg=None):
    if arg:
        return arg
    patterns = [
        "/usr/local/texlive/*/texmf-dist/fonts/opentype/public/lm",
        "/Library/TeX/Root/texmf-dist/fonts/opentype/public/lm",
        "/usr/share/texlive/texmf-dist/fonts/opentype/public/lm",
        "/usr/share/texmf/fonts/opentype/public/lm",
    ]
    for pattern in patterns:
        for d in sorted(glob.glob(pattern), reverse=True):
            if os.path.exists(os.path.join(d, "lmroman10-regular.otf")):
                return d
    return None


def otf_to_ttf(font):
    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyphs[name] = pen.glyph()

    font["loca"] = newTable("loca")
    font["glyf"] = glyf = newTable("glyf")
    glyf.glyphOrder = glyph_order
    glyf.glyphs = glyphs
    del font["CFF "]
    if "VORG" in font:
        del font["VORG"]
    glyf.compile(font)

    hmtx = font["hmtx"]
    for name, glyph in glyf.glyphs.items():
        glyph.recalcBounds(glyf)
        hmtx[name] = (hmtx[name][0], getattr(glyph, "xMin", 0))

    font["maxp"] = maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = max(
        (len(getattr(g, "components", [])) for g in glyphs.values()), default=0)
    maxp.compile(font)

    post = font["post"]
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = glyph_order
    font.sfntVersion = "\000\001\000\000"
    font["head"].glyphDataFormat = 0


def main():
    lm_dir = find_lm_dir(sys.argv[1] if len(sys.argv) > 1 else None)
    if not lm_dir:
        print("Latin Modern OpenType files not found. Install MacTeX or BasicTeX, "
              "or pass the folder that holds lmroman10-regular.otf.")
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    for style in NAMES:
        src = os.path.join(lm_dir, f"lmroman10-{style}.otf")
        dst = os.path.join(OUT_DIR, f"lmroman10-{style}.ttf")
        if not os.path.exists(src):
            print(f"missing {src}")
            return 1
        font = TTFont(src)
        otf_to_ttf(font)
        font.save(dst)
        print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
