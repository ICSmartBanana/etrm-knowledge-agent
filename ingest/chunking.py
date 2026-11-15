"""Split a Markdown document into chunks at level-2 headings (iteration-1 chunking)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    index: int
    heading: str
    text: str


def chunk_markdown(title: str, body: str, max_chars: int) -> list[Chunk]:
    sections: list[tuple[str, list[str]]] = [("Introduction", [])]
    for line in body.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif line.startswith("# "):
            continue  # the title; added to every chunk below
        else:
            sections[-1][1].append(line)

    chunks: list[Chunk] = []
    for heading, lines in sections:
        text = "\n".join(lines).strip()
        if not text:
            continue
        for part in _split(text, max_chars):
            chunks.append(Chunk(len(chunks), heading, f"{title} - {heading}\n\n{part}"))
    return chunks


def _split(text: str, max_chars: int) -> list[str]:
    """Split on paragraph boundaries; a part exceeds max_chars only if one paragraph does."""
    parts: list[str] = []
    current = ""
    for para in text.split("\n\n"):
        if current and len(current) + len(para) + 2 > max_chars:
            parts.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        parts.append(current)
    return parts
