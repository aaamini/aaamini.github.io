#!/usr/bin/env python3
"""Compare the website bibliography with the CV bibliography.

The CV file has accumulated duplicate keys, missing keys, and some records that
are not meant for the public website.  This script is deliberately tolerant: it
uses light brace matching and field extraction instead of requiring a fully
valid BibTeX database.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_BIB = ROOT / "data" / "papers.bib"
DEFAULT_CV_BIB = Path("/Users/arash/Dropbox/latex-docs/cv/mypubs.bib")
DEFAULT_OLD_SITE_BIB = Path("/Users/arash/Dropbox/Sites/new_site/_bibliography/papers.bib")
DEFAULT_TEX_ROOTS = [
    Path("/Users/arash/Dropbox/latex-docs/cv/cv_aaa.tex"),
    Path("/Users/arash/Dropbox/latex-docs/cv/merit_pubs_2024.tex"),
]

ENTRY_RE = re.compile(r"(?im)^[ \t]*@(?P<type>[A-Za-z]+)[ \t]*[{(]")
FIELD_RE = re.compile(r"(?im)([A-Za-z][A-Za-z0-9_-]*)\s*=")
CITE_RE = re.compile(r"\\(?:fullcite|cite|nocite)(?:\[[^\]]*\])*\{([^}]*)\}")

INTERNAL_VENUE_PATTERNS = (
    "working",
    "working paper",
    "under review",
    "submitted",
    "technical report",
)


@dataclass
class Entry:
    source: str
    entry_type: str
    key: str
    line: int
    text: str
    fields: dict[str, str]
    issue: str | None = None

    @property
    def title(self) -> str:
        return self.fields.get("title", "")

    @property
    def year(self) -> str:
        return self.fields.get("year", "") or self.fields.get("date", "")

    @property
    def venue(self) -> str:
        return (
            self.fields.get("journal", "")
            or self.fields.get("booktitle", "")
            or self.fields.get("publisher", "")
            or self.fields.get("note", "")
        )

    @property
    def arxiv(self) -> str:
        return (
            self.fields.get("arxiv", "")
            or self.fields.get("eprint", "")
            or self.fields.get("eprint_inactive", "")
        )


def matching_brace(text: str, start: int) -> int | None:
    opener = text[start]
    closer = "}" if opener == "{" else ")"
    depth = 0
    escaped = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return idx
    return None


def split_top_level_fields(text: str) -> list[str]:
    fields: list[str] = []
    start = 0
    depth = 0
    quote = False
    escaped = False
    for idx, ch in enumerate(text):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"' and depth == 0:
            quote = not quote
        elif not quote:
            if ch == "{":
                depth += 1
            elif ch == "}" and depth:
                depth -= 1
            elif ch == "," and depth == 0:
                fields.append(text[start:idx])
                start = idx + 1
    tail = text[start:].strip()
    if tail:
        fields.append(tail)
    return fields


def clean_value(value: str) -> str:
    value = value.strip().rstrip(",")
    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1]
    elif value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return re.sub(r"\s+", " ", value).strip()


def parse_fields(entry_body_after_key: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for chunk in split_top_level_fields(entry_body_after_key):
        match = FIELD_RE.search(chunk)
        if not match:
            continue
        name = match.group(1).lower()
        value = chunk[match.end() :].strip()
        fields[name] = clean_value(value)
    return fields


def parse_bib(path: Path, source: str) -> list[Entry]:
    text = path.read_text(errors="replace")
    entries: list[Entry] = []
    for match in ENTRY_RE.finditer(text):
        entry_type = match.group("type")
        if entry_type.lower() == "comment":
            continue
        open_idx = text.find(match.group(0).rstrip()[-1], match.start())
        close_idx = matching_brace(text, open_idx)
        if close_idx is None:
            body = text[open_idx + 1 :]
            issue = "unbalanced entry"
        else:
            body = text[open_idx + 1 : close_idx]
            issue = None
        line = text.count("\n", 0, match.start()) + 1
        key_part, sep, rest = body.partition(",")
        key = key_part.strip()
        if not sep or not key:
            key = f"<missing-key:{line}>"
            rest = body
            issue = issue or "missing citation key"
        fields = parse_fields(rest)
        entries.append(
            Entry(
                source=source,
                entry_type=entry_type,
                key=key,
                line=line,
                text=text[match.start() : close_idx + 1] if close_idx else body,
                fields=fields,
                issue=issue,
            )
        )
    return entries


def delatexish(value: str) -> str:
    value = value.lower()
    value = re.sub(r"\\[a-zA-Z]+", " ", value)
    value = value.replace("{", " ").replace("}", " ")
    value = value.replace("~", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_title(value: str) -> str:
    words = delatexish(value).split()
    return " ".join(words)


def normalize_arxiv(value: str) -> str:
    value = value.strip()
    value = re.sub(r"https?://arxiv\.org/(abs|pdf)/", "", value)
    value = re.sub(r"\.pdf$", "", value)
    return value.lower()


def entry_label(entry: Entry) -> str:
    title = clean_value(entry.title) or "(no title parsed)"
    venue = clean_value(entry.venue)
    bits = [f"`{entry.key}`", str(entry.year or "?"), title]
    if venue:
        bits.append(f"[{venue}]")
    return " - ".join(bits)


def is_internal_or_working(entry: Entry) -> bool:
    venue = delatexish(entry.venue)
    if any(pattern in venue for pattern in INTERNAL_VENUE_PATTERNS):
        return True
    if "--" in entry.year:
        return True
    if entry.entry_type.lower() in {"misc", "online"}:
        return True
    key = entry.key.lower()
    return any(part in key for part in (":pkg", "pkg", "repo", "comp"))


def index_by(entries: list[Entry], getter) -> dict[str, list[Entry]]:
    index: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        value = getter(entry)
        if value:
            index[value].append(entry)
    return index


def duplicate_keys(entries: list[Entry]) -> dict[str, list[Entry]]:
    grouped: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.key].append(entry)
    return {key: vals for key, vals in grouped.items() if len(vals) > 1}


def strip_tex_comment(line: str) -> str:
    escaped = False
    for idx, ch in enumerate(line):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "%":
            return line[:idx]
    return line


def active_tex_citations(roots: list[Path]) -> dict[str, set[Path]]:
    keys: dict[str, set[Path]] = defaultdict(set)
    for root in roots:
        paths = [root] if root.is_file() else sorted(root.rglob("*.tex"))
        for path in paths:
            text = "\n".join(strip_tex_comment(line) for line in path.read_text(errors="replace").splitlines())
            for match in CITE_RE.finditer(text):
                for key in match.group(1).split(","):
                    key = key.strip()
                    if key:
                        keys[key].add(path)
    return keys


def print_section(title: str) -> None:
    print(f"\n## {title}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE_BIB)
    parser.add_argument("--cv", type=Path, default=DEFAULT_CV_BIB)
    parser.add_argument("--old-site", type=Path, default=DEFAULT_OLD_SITE_BIB)
    parser.add_argument(
        "--tex-root",
        action="append",
        type=Path,
        dest="tex_roots",
        help="TeX file or directory to scan for active CV citation keys.",
    )
    args = parser.parse_args()

    site = parse_bib(args.site, "site")
    cv = parse_bib(args.cv, "cv")
    old_site = parse_bib(args.old_site, "old-site") if args.old_site.exists() else []
    tex_roots = args.tex_roots or DEFAULT_TEX_ROOTS
    cited = active_tex_citations(tex_roots)

    site_by_key = {entry.key: entry for entry in site}
    cv_by_key = {entry.key: entry for entry in cv}
    site_keys = set(site_by_key)
    cv_keys = set(cv_by_key)
    site_only = site_keys - cv_keys
    cv_only = cv_keys - site_keys

    site_by_title = index_by(site, lambda e: normalize_title(e.title))
    cv_by_title = index_by(cv, lambda e: normalize_title(e.title))
    site_by_arxiv = index_by(site, lambda e: normalize_arxiv(e.arxiv))
    cv_by_arxiv = index_by(cv, lambda e: normalize_arxiv(e.arxiv))

    same_arxiv_diff_key: list[tuple[Entry, Entry]] = []
    same_title_diff_key: list[tuple[Entry, Entry]] = []
    matched_cv_only: set[str] = set()
    matched_site_only: set[str] = set()

    for key in sorted(cv_only):
        cv_entry = cv_by_key[key]
        arxiv = normalize_arxiv(cv_entry.arxiv)
        title = normalize_title(cv_entry.title)
        site_match = None
        if arxiv and arxiv in site_by_arxiv:
            site_match = site_by_arxiv[arxiv][0]
            same_arxiv_diff_key.append((cv_entry, site_match))
        elif title and title in site_by_title:
            site_match = site_by_title[title][0]
            same_title_diff_key.append((cv_entry, site_match))
        if site_match:
            matched_cv_only.add(cv_entry.key)
            matched_site_only.add(site_match.key)

    unmatched_cv = [cv_by_key[key] for key in sorted(cv_only - matched_cv_only)]
    unmatched_site = [site_by_key[key] for key in sorted(site_only - matched_site_only)]
    internal_cv = [entry for entry in unmatched_cv if is_internal_or_working(entry)]
    cited_keys = set(cited)
    cited_missing_site = sorted(cited_keys - site_keys)
    cited_missing_cv = sorted(cited_keys - cv_keys)

    print("# Bibliography audit")
    print()
    print(f"- Site bibliography: `{args.site}`")
    print(f"- CV bibliography: `{args.cv}`")
    if args.old_site.exists():
        old_same = Counter(entry.key for entry in old_site) == Counter(entry.key for entry in site)
        print(f"- Old-site bibliography: `{args.old_site}`")
        print(f"- Old-site keys match current site: `{old_same}`")
    print("- TeX citation roots:")
    for root in tex_roots:
        print(f"  - `{root}`")

    print_section("Summary")
    rows = [
        ("site entries", len(site)),
        ("CV entries", len(cv)),
        ("exact key overlap", len(site_keys & cv_keys)),
        ("same arXiv, different key", len(same_arxiv_diff_key)),
        ("same title, different key", len(same_title_diff_key)),
        ("CV-only unmatched", len(unmatched_cv)),
        ("site-only unmatched", len(unmatched_site)),
        ("CV-only likely internal/working/software", len(internal_cv)),
        ("active TeX citation keys", len(cited_keys)),
        ("active TeX keys missing from site", len(cited_missing_site)),
        ("active TeX keys missing from CV bib", len(cited_missing_cv)),
    ]
    print("| category | count |")
    print("| --- | ---: |")
    for label, count in rows:
        print(f"| {label} | {count} |")

    issues = [entry for entry in site + cv if entry.issue]
    site_dupes = duplicate_keys(site)
    cv_dupes = duplicate_keys(cv)
    if issues or site_dupes or cv_dupes:
        print_section("Parse and Key Issues")
        for entry in issues:
            print(f"- `{entry.source}` line {entry.line}: {entry.issue} in `{entry.key}`")
        for label, dupes in (("site", site_dupes), ("cv", cv_dupes)):
            for key, entries in dupes.items():
                lines = ", ".join(str(entry.line) for entry in entries)
                print(f"- `{label}` duplicate key `{key}` at lines {lines}")

    if same_arxiv_diff_key:
        print_section("Same arXiv, Different Key")
        for cv_entry, site_entry in same_arxiv_diff_key:
            print(f"- CV {entry_label(cv_entry)}")
            print(f"  site match: {entry_label(site_entry)}")

    if same_title_diff_key:
        print_section("Same Title, Different Key")
        for cv_entry, site_entry in same_title_diff_key:
            print(f"- CV {entry_label(cv_entry)}")
            print(f"  site match: {entry_label(site_entry)}")

    if unmatched_cv:
        print_section("CV-Only Unmatched Candidates")
        for entry in unmatched_cv:
            marker = " likely `site = {false}`" if is_internal_or_working(entry) else ""
            print(f"- {entry_label(entry)}{marker}")

    if unmatched_site:
        print_section("Site-Only Unmatched Candidates")
        for entry in unmatched_site:
            print(f"- {entry_label(entry)}")

    if cited_missing_site:
        print_section("Active TeX Citation Keys Not in Site Bibliography")
        for key in cited_missing_site:
            files = ", ".join(f"`{path}`" for path in sorted(cited[key]))
            print(f"- `{key}` cited in {files}")

    if cited_missing_cv:
        print_section("Active TeX Citation Keys Missing from CV Bibliography")
        for key in cited_missing_cv:
            files = ", ".join(f"`{path}`" for path in sorted(cited[key]))
            print(f"- `{key}` cited in {files}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
