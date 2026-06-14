# PDFMind

A command line research assistant for a single PDF. Load a document, then
ask questions about it, summarize sections, and pull out key concepts,
powered by the Gemini API (gemini-2.5-flash-lite).

## Setup

```
pip install -r requirements.txt
```

On first run, it will ask for a Gemini API key and save it to
`~/.pdfmind_config.json`. Get a free key from
[Google AI Studio](https://aistudio.google.com/app/apikey).

## Usage

```
python main.py path/to/document.pdf
```

This loads the PDF and starts an interactive session.

## Commands

- `chapters` - list detected chapters and sections
- `summarize` - summarize the whole document
- `summarize <n>` - summarize chapter or section number n
- `summarize <a>-<b>` - summarize pages a to b
- `concepts` - extract key concepts from the whole document
- `concepts <n>` - extract key concepts from chapter or section n
- `ask <question>` - ask a question about the document
- `pages` - show the total page count
- `key` - update the stored Gemini API key
- `help` - show the command list
- `exit` - quit

## How it works

- `pdf_reader.py` extracts text from the PDF page by page using pypdf, and
  tries to detect chapter or section headings using simple text patterns
  such as "Chapter 1" or "2.1 Background". This detection is approximate
  and may miss headings or pick up extra ones, depending on how the PDF
  was made.
- `gemini_client.py` handles the API key and sends prompts to Gemini.
- `main.py` ties it together into an interactive command line session.

## Limitations

- Chapter detection is heuristic and works best on documents with clear,
  text based headings such as "Chapter 1" or numbered section titles.
  Scanned PDFs without selectable text will not work well.
- For `ask` and whole document `summarize` or `concepts`, the entire
  document text is sent to Gemini in one request. This works for most
  papers, reports, and short books, but very large documents may exceed
  the model's context limit.
