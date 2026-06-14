"""
pdf_reader.py

Loads a PDF, extracts text page by page, and tries to detect chapter or
section headings using simple text patterns. Heading detection is a
best-effort heuristic, not a guarantee, since most PDFs do not carry
structured chapter information.
"""

import re
from collections import Counter

from pypdf import PdfReader


CHAPTER_PATTERN = re.compile(r"^(chapter|part)\s+\S+", re.IGNORECASE)
SECTION_PATTERN = re.compile(r"^\d{1,2}(\.\d{1,2}){0,2}\.?\s+[A-Z][A-Za-z]")
DOT_LEADER_PATTERN = re.compile(r"\.{3,}|\.\s*\.\s*\.")

MAX_HEADING_LENGTH = 90
MIN_HEADING_LENGTH = 3


class Document:
    """Represents a loaded PDF: its pages, full text, and detected chapters."""

    def __init__(self, path):
        self.path = path
        self.pages = []
        self.full_text = ""
        self.chapters = []
        self._load()

    def _load(self):
        reader = PdfReader(self.path)

        for page in reader.pages:
            text = page.extract_text() or ""
            self.pages.append(text)

        self.full_text = "\n".join(self.pages)
        self.chapters = self._detect_chapters()

    @property
    def page_count(self):
        return len(self.pages)

    def get_page_range(self, start, end):
        """Return joined text for pages start to end, inclusive, 1-indexed."""
        start = max(1, start)
        end = min(self.page_count, end)
        if start > end:
            return ""
        return "\n".join(self.pages[start - 1:end])

    def get_chapter_text(self, index):
        """Return the text belonging to chapter number `index` (1-indexed)."""
        if index < 1 or index > len(self.chapters):
            return None

        start = self.chapters[index - 1]["start_char"]
        if index < len(self.chapters):
            end = self.chapters[index]["start_char"]
        else:
            end = len(self.full_text)

        return self.full_text[start:end]

    def _detect_chapters(self):
        repeated_lines = self._find_repeated_lines()

        chapters = []
        char_pos = 0

        for page_index, page_text in enumerate(self.pages):
            for line in page_text.split("\n"):
                stripped = line.strip()

                if self._looks_like_heading(stripped, repeated_lines):
                    chapters.append({
                        "title": stripped,
                        "page": page_index + 1,
                        "start_char": char_pos,
                    })

                char_pos += len(line) + 1

        return chapters

    def _find_repeated_lines(self):
        """Find lines (likely running headers or footers) that repeat across
        many pages, so they are not mistaken for chapter headings."""
        counts = Counter()

        for page_text in self.pages:
            seen_this_page = set()
            for line in page_text.split("\n"):
                stripped = line.strip()
                if stripped and len(stripped) <= MAX_HEADING_LENGTH:
                    seen_this_page.add(stripped)
            for line in seen_this_page:
                counts[line] += 1

        threshold = max(2, self.page_count // 3)
        return {line for line, count in counts.items() if count > threshold}

    def _looks_like_heading(self, stripped, repeated_lines):
        if not stripped or stripped in repeated_lines:
            return False

        if len(stripped) < MIN_HEADING_LENGTH or len(stripped) > MAX_HEADING_LENGTH:
            return False

        if DOT_LEADER_PATTERN.search(stripped):
            return False

        if CHAPTER_PATTERN.match(stripped):
            return True

        if SECTION_PATTERN.match(stripped):
            return True

        return False
