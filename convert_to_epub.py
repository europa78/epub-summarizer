#!/usr/bin/env python3
"""Convert beastie-boys-sample-analysis.md to EPUB."""

import re
from pathlib import Path
from ebooklib import epub
import markdown

CSS = """
body { font-family: Georgia, serif; line-height: 1.6; margin: 1em 2em; }
h1 { font-size: 1.8em; margin-top: 2em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }
h2 { font-size: 1.4em; margin-top: 1.8em; color: #222; }
h3 { font-size: 1.1em; margin-top: 1.2em; }
p { margin: 0.8em 0; text-align: justify; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.5em 0; }
em { font-style: italic; }
strong { font-weight: bold; }
"""

def make_chapter(uid, title, html_body):
    ch = epub.EpubHtml(title=title, file_name=f"{uid}.xhtml", lang="en")
    escaped_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    ch.content = (
        f"<html><head><title>{escaped_title}</title>"
        '<link rel="stylesheet" type="text/css" href="style/main.css"/>'
        f"</head><body>{html_body}</body></html>"
    )
    return ch


def md_to_epub(md_path: str, epub_path: str):
    md_text = Path(md_path).read_text(encoding="utf-8")

    book = epub.EpubBook()
    book.set_identifier("beastie-boys-sample-analysis")
    book.set_title("Beastie Boys: A Complete Sample Analysis")
    book.set_language("en")
    book.add_author("Compiled from WhoSampled.com data")

    css_item = epub.EpubItem(
        uid="style",
        file_name="style/main.css",
        media_type="text/css",
        content=CSS,
    )
    book.add_item(css_item)

    # Split on heading lines (# or ##), keeping the delimiter
    # Strategy: accumulate lines until next heading
    chapters = []       # list of epub.EpubHtml
    toc = []            # epub TOC structure
    spine = ["nav"]

    current_album = None    # current album Section
    current_album_chapters = []

    # Walk line by line, collecting chunks per heading
    all_lines = md_text.splitlines()
    chunk_start = None
    chunk_lines = []

    def flush_chunk(lines, idx):
        nonlocal current_album, current_album_chapters
        if not lines:
            return
        text = "\n".join(lines).strip()
        if not text:
            return

        first = lines[0]
        if first.startswith("## "):
            track_title = first.lstrip("# ").strip().strip('“').strip('”').strip('"')
            uid = f"ch{idx:03d}"
            html_body = markdown.markdown(text, extensions=["extra"])
            ch = make_chapter(uid, track_title, html_body)
            ch.add_item(css_item)
            book.add_item(ch)
            chapters.append(ch)
            spine.append(ch)
            current_album_chapters.append(ch)
        elif first.startswith("# "):
            album_title = first.lstrip("# ").strip()
            # Save previous album group into TOC
            if current_album is not None and current_album_chapters:
                toc.append((current_album, list(current_album_chapters)))
                current_album_chapters = []
            elif current_album_chapters:
                # intro chapters before first album heading
                toc.extend(current_album_chapters)
                current_album_chapters = []

            current_album = epub.Section(album_title)
            uid = f"ch{idx:03d}"
            html_body = markdown.markdown(text, extensions=["extra"])
            ch = make_chapter(uid, album_title, html_body)
            ch.add_item(css_item)
            book.add_item(ch)
            chapters.append(ch)
            spine.append(ch)
            current_album_chapters.append(ch)
        else:
            # Preamble / intro before first heading
            uid = f"ch{idx:03d}"
            html_body = markdown.markdown(text, extensions=["extra"])
            ch = make_chapter(uid, "Introduction", html_body)
            ch.add_item(css_item)
            book.add_item(ch)
            chapters.append(ch)
            spine.append(ch)
            current_album_chapters.append(ch)

    idx = 0
    current_lines = []
    for line in all_lines:
        if re.match(r'^#{1,2} ', line) and current_lines:
            flush_chunk(current_lines, idx)
            idx += 1
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        flush_chunk(current_lines, idx)

    # Flush last album group
    if current_album is not None and current_album_chapters:
        toc.append((current_album, list(current_album_chapters)))
    elif current_album_chapters:
        toc.extend(current_album_chapters)

    book.toc = toc
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(epub_path, book)
    print(f"Written: {epub_path}")
    print(f"Chapters: {len(chapters)}")


if __name__ == "__main__":
    md_to_epub(
        "/home/user/epub-summarizer/beastie-boys-sample-analysis.md",
        "/home/user/epub-summarizer/beastie-boys-sample-analysis.epub",
    )
