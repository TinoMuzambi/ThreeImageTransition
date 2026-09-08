#!/usr/bin/env python3
"""Validate the demo's HTML and local assets without third-party packages."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
ASSET = re.compile(
    r"""(?P<quote>["'])(?P<path>(?:\.\.?/|/)[^"'?#]+\.(?:css|gif|ico|jpe?g|js|png|svg|webp))(?P=quote)""",
    re.IGNORECASE,
)


def check_reference(reference: str, base: Path, context: str, errors: list[str]) -> None:
    reference = reference.strip()
    if not reference:
        errors.append(f"{context}: empty reference")
        return
    if reference.startswith(("#", "mailto:", "tel:", "data:")):
        return
    if reference.startswith("//"):
        errors.append(f"{context}: protocol-relative URL is not allowed")
        return
    parsed = urlsplit(reference)
    if parsed.scheme:
        if parsed.scheme != "https":
            errors.append(f"{context}: external URL must use HTTPS: {reference}")
        return
    path = unquote(parsed.path)
    target = ROOT / path.lstrip("/") if path.startswith("/") else base / path
    if path.endswith("/"):
        target /= "index.html"
    target = target.resolve()
    if not target.is_relative_to(ROOT) or not target.exists():
        errors.append(f"{context}: missing local target {reference}")


class Document(HTMLParser):
    def __init__(self, source: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.stack: list[str] = []
        self.ids: set[str] = set()
        self.errors: list[str] = []
        self.doctype = False
        self.lang = False
        self.charset = False
        self.viewport = False
        self.titles = 0
        self.mains = 0

    def handle_decl(self, declaration: str) -> None:
        self.doctype |= declaration.lower() == "doctype html"

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.inspect(tag.lower(), attrs, False)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.inspect(tag, attrs, tag not in VOID)

    def inspect(
        self, tag: str, attrs: list[tuple[str, str | None]], push: bool
    ) -> None:
        values = {name.lower(): value for name, value in attrs}
        element_id = values.get("id")
        if element_id in self.ids:
            self.errors.append(f"duplicate id #{element_id}")
        elif element_id:
            self.ids.add(element_id)
        self.lang |= tag == "html" and bool(values.get("lang"))
        self.charset |= tag == "meta" and "charset" in values
        self.viewport |= (
            tag == "meta" and (values.get("name") or "").lower() == "viewport"
        )
        self.titles += tag == "title"
        self.mains += tag == "main"
        if tag == "img" and "alt" not in values:
            self.errors.append("image is missing an alt attribute")
        if (values.get("target") or "").lower() == "_blank":
            rel = set((values.get("rel") or "").lower().split())
            if not {"noopener", "noreferrer"}.issubset(rel):
                self.errors.append('target="_blank" must use rel="noopener noreferrer"')
        for attribute in ("href", "src"):
            if attribute in values:
                check_reference(
                    values[attribute] or "",
                    self.source.parent,
                    f"{tag}[{attribute}]",
                    self.errors,
                )
        if push:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"unexpected closing </{tag}>")
            return
        expected = self.stack.pop()
        if expected != tag:
            self.errors.append(f"closing </{tag}> does not match <{expected}>")

    def finish(self) -> list[str]:
        if self.stack:
            self.errors.append(f"unclosed element(s): {', '.join(self.stack)}")
        for valid, message in (
            (self.doctype, "missing HTML5 doctype"),
            (self.lang, "missing document language"),
            (self.charset, "missing charset metadata"),
            (self.viewport, "missing viewport metadata"),
            (self.titles == 1, f"expected one title, found {self.titles}"),
            (self.mains == 1, f"expected one main, found {self.mains}"),
        ):
            if not valid:
                self.errors.append(message)
        return self.errors


def main() -> int:
    errors: list[str] = []
    html_files = sorted(ROOT.rglob("*.html"))
    if not html_files:
        errors.append("no HTML files found")
    for source in html_files:
        parser = Document(source)
        parser.feed(source.read_text(encoding="utf-8"))
        parser.close()
        errors.extend(f"{source.relative_to(ROOT)}: {error}" for error in parser.finish())
    for source in [*ROOT.rglob("*.js"), *ROOT.rglob("*.css")]:
        text = source.read_text(encoding="utf-8")
        for match in ASSET.finditer(text):
            check_reference(
                match.group("path"), source.parent, str(source.relative_to(ROOT)), errors
            )
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Validated {len(html_files)} HTML file(s), metadata, and local assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
