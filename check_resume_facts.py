#!/usr/bin/env python3
"""
check_resume_facts.py — verify the resume's numbers against Mallika's source files.

For Resume.yaml it reports:
  1. Bullets (and the summary) that contain a number not found in
     okf/base_files/*/resume*.md or okf/project_catalog.yaml (possible invention).
  2. Experience bullets that have no number at all (the pipeline asks for a
     quantifiable action wherever the sources have a real figure).

Usage: python check_resume_facts.py <Resume.yaml>
Exit code 0 always prints a report; exit 3 only when untraceable numbers exist.
"""
import glob
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
NUM = re.compile(r"\d+(?:[.,]\d+)?")


def source_numbers():
    texts = []
    for pattern in ("okf/base_files/*/*.md", "okf/project_catalog.yaml"):
        for path in glob.glob(os.path.join(HERE, pattern)):
            with open(path, encoding="utf-8") as f:
                texts.append(f.read())
    return set(NUM.findall(" ".join(texts)))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    with open(sys.argv[1], encoding="utf-8") as f:
        resume = yaml.safe_load(f) or {}
    known = source_numbers()

    items = [("summary", resume.get("summary", ""))]
    for exp in resume.get("professional_experience", []):
        for b in exp.get("bullets", []):
            items.append((exp.get("company", ""), b))
        for pb in exp.get("project_bullets", []):
            for b in pb.get("bullets", []):
                items.append((pb.get("name", ""), b))
    for proj in resume.get("projects", []):
        for b in proj.get("bullets", []):
            items.append((proj.get("name", ""), b))

    untraceable, no_number = [], []
    for where, text in items:
        nums = NUM.findall(str(text))
        bad = [n for n in nums if n not in known]
        if bad:
            untraceable.append((where, bad, text))
        if not nums and where != "summary":
            no_number.append((where, text))

    total = len([i for i in items if i[0] != "summary"])
    print(f"Fact check: {total - len(no_number)}/{total} bullets carry a number")
    for where, bad, text in untraceable:
        print(f"  UNTRACEABLE {bad} in [{where}]: {text}")
    for where, text in no_number:
        print(f"  no number   [{where}]: {text}")
    if no_number:
        print("  Ask Mallika for a real figure for the bullets above, or leave them as they are.")
    if not untraceable:
        print("  All numbers appear in the base resume or the project catalog.")
    return 3 if untraceable else 0


if __name__ == "__main__":
    sys.exit(main())
