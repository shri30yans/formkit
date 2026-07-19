"""Export helpers (thin wrappers around Document.export)."""

from __future__ import annotations

from formkit.document import Document
from formkit.body import Body


def export(doc: Document, path: str, body: Body | str | None = None) -> None:
    doc.export(path, body=body)
