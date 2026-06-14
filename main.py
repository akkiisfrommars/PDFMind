#!/usr/bin/env python3
"""
main.py

PDFMind: an interactive command line research assistant for a single PDF.

Usage:
    python main.py path/to/document.pdf
"""

import sys
from pathlib import Path

from pdf_reader import Document
from gemini_client import ask_gemini, update_api_key


HELP_TEXT = """
Commands:
  chapters              List detected chapters and sections
  summarize             Summarize the whole document
  summarize <n>         Summarize chapter or section number n
  summarize <a>-<b>     Summarize pages a to b
  concepts              Extract key concepts from the whole document
  concepts <n>          Extract key concepts from chapter or section n
  ask <question>        Ask a question about the document
  pages                 Show the total page count
  key                   Update the stored Gemini API key
  help                  Show this help message
  exit                  Quit
""".strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-pdf>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    print(f"Loading {path.name}...")
    try:
        doc = Document(str(path))
    except Exception as error:
        print(f"Could not read this PDF: {error}")
        sys.exit(1)

    print(f"Loaded {doc.page_count} pages.")

    if doc.chapters:
        print(f"Detected {len(doc.chapters)} possible chapters or sections.")
        print("Type 'chapters' to see them. Heading detection is approximate.")
    else:
        print("No chapter headings detected. Use page ranges instead, for example: summarize 1-10")

    print()
    print(HELP_TEXT)
    print()

    run_session(doc)


def run_session(doc):
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        command, _, rest = line.partition(" ")
        command = command.lower()
        rest = rest.strip()

        if command in ("exit", "quit"):
            break
        elif command == "help":
            print(HELP_TEXT)
        elif command == "pages":
            print(f"{doc.page_count} pages")
        elif command == "chapters":
            show_chapters(doc)
        elif command == "key":
            update_api_key()
        elif command == "summarize":
            handle_summarize(doc, rest)
        elif command == "concepts":
            handle_concepts(doc, rest)
        elif command == "ask":
            if not rest:
                print("Usage: ask <question>")
                continue
            handle_ask(doc, rest)
        else:
            print("Unknown command. Type 'help' for a list of commands.")


def show_chapters(doc):
    if not doc.chapters:
        print("No chapters detected.")
        return

    for i, chapter in enumerate(doc.chapters, start=1):
        print(f"  {i}. {chapter['title']} (page {chapter['page']})")


def resolve_target(doc, arg):
    """Turn a command argument into (label, text) for chapters or page ranges."""
    if not arg:
        return "the whole document", doc.full_text

    if "-" in arg:
        parts = arg.split("-")
        if len(parts) == 2 and all(p.strip().isdigit() for p in parts):
            start, end = int(parts[0]), int(parts[1])
            text = doc.get_page_range(start, end)
            return f"pages {start} to {end}", text

    if arg.isdigit():
        index = int(arg)
        text = doc.get_chapter_text(index)
        if text is None:
            print(f"No chapter or section {index}. Type 'chapters' to see the list.")
            return None, None
        title = doc.chapters[index - 1]["title"]
        return f"the section '{title}'", text

    print("Could not understand that. Use a chapter number or a page range like 10-20.")
    return None, None


def handle_summarize(doc, arg):
    label, text = resolve_target(doc, arg)
    if text is None:
        return

    text = text.strip()
    if not text:
        print(f"No text found for {label}.")
        return

    prompt = "\n".join([
        "You summarize sections of documents clearly and concisely.",
        f"Summarize the following text from {label}.",
        "Write three to six sentences covering the main ideas.",
        "",
        "Rules:",
        "- Do not use emojis.",
        "- Do not use em dashes or en dashes. Use commas or periods instead.",
        "",
        "Text:",
        text,
    ])

    print(f"Summarizing {label}...")
    run_prompt(prompt)


def handle_concepts(doc, arg):
    label, text = resolve_target(doc, arg)
    if text is None:
        return

    text = text.strip()
    if not text:
        print(f"No text found for {label}.")
        return

    prompt = "\n".join([
        "You extract key concepts and terms from documents.",
        f"Read the following text from {label}.",
        "List five to ten key concepts or terms from this text.",
        "For each one, write the term, then a colon, then a one sentence explanation.",
        "Put each concept on its own line.",
        "",
        "Rules:",
        "- Do not use emojis.",
        "- Do not use em dashes or en dashes. Use commas or periods instead.",
        "",
        "Text:",
        text,
    ])

    print(f"Extracting key concepts from {label}...")
    run_prompt(prompt)


def handle_ask(doc, question):
    prompt = "\n".join([
        "You answer questions about a document using only the text provided below.",
        "If the answer is not in the document, say so clearly instead of guessing.",
        "",
        "Document text:",
        doc.full_text,
        "",
        "Question:",
        question,
        "",
        "Rules:",
        "- Do not use emojis.",
        "- Do not use em dashes or en dashes. Use commas or periods instead.",
        "- Answer in two to five sentences unless the question clearly needs more detail.",
    ])

    print("Thinking...")
    run_prompt(prompt)


def run_prompt(prompt):
    try:
        result = ask_gemini(prompt)
    except RuntimeError as error:
        print(f"Error: {error}")
        return

    print()
    print(result.strip())
    print()


if __name__ == "__main__":
    main()
