#!/usr/bin/env python3
"""Static site generator for aaamini.github.io.

Reads
    data/       site.yml, news.yml, classes.yml, students.yml, papers.bib
    content/    markdown pages; content/notes/*.md become /notes/<slug>/
    templates/  Jinja2 templates
    assets/     copied verbatim to /assets/
    teaching/   *.md rendered at their `permalink`; everything else copied as-is

and writes the whole site to _site/.

Usage
    python build.py             build once
    python build.py --serve     build, serve at http://127.0.0.1:8000, rebuild on change
"""

from __future__ import annotations

import argparse
import datetime as dt
import functools
import http.server
import re
import shutil
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

import yaml
from bibtexparser.bparser import BibTexParser
from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"

env = Environment(
    loader=FileSystemLoader(ROOT / "templates"),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

import html as _html


def _math_inline(self, tokens, idx, options, env):
    return f'<span class="math">\\({_html.escape(tokens[idx].content)}\\)</span>'


def _math_block(self, tokens, idx, options, env):
    return f'<div class="math">\\[{_html.escape(tokens[idx].content)}\\]</div>\n'


_md = (
    MarkdownIt("commonmark", {"html": True})
    .enable("table")
    .use(dollarmath_plugin, double_inline=True)
)
_md.add_render_rule("math_inline", _math_inline)
_md.add_render_rule("math_inline_double", _math_inline)
_md.add_render_rule("math_block", _math_block)


def md_convert(text: str) -> str:
    return _md.render(text)


def md_inline(text: str) -> str:
    """Markdown for one-liners (news items): convert and drop the <p> wrapper."""
    out = md_convert(text).strip()
    return re.sub(r"^<p>|</p>$", "", out)


def front_matter(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        return (yaml.safe_load(fm) or {}), body
    return {}, text


def write(url_path: str, text: str) -> None:
    rel = url_path.lstrip("/")
    if url_path.endswith("/") or url_path == "":
        rel += "index.html"
    elif not rel.endswith(".html"):
        rel += ".html"
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)


MATH_DELIM_RE = re.compile(r"(?<!\\)(\$\$?)[\s\S]+?(?<!\\)\1|\\\(|\\\[")


def has_math(text: str) -> bool:
    return bool(text and MATH_DELIM_RE.search(text))


def html_has_math(html: str) -> bool:
    return 'class="math"' in html


def pub_title_has_math(pub: dict) -> bool:
    return has_math(pub["title"])


def rendered_pub_has_math(pub: dict) -> bool:
    return pub_title_has_math(pub)


# --------------------------------------------------------------------------
# Bibliography
# --------------------------------------------------------------------------

ACCENTS = {
    "'": "́", '"': "̈", "`": "̀", "^": "̂",
    "~": "̃", "v": "̌", "c": "̧", "u": "̆",
}

# fields that exist only to drive the website, stripped from displayed bibtex
BIBTEX_FIELD_ORDER = [
    "title", "author", "editor", "journal", "booktitle", "volume", "number",
    "pages", "year", "month", "publisher", "series", "organization",
    "address", "edition", "doi", "url", "eprint", "archiveprefix",
    "primaryclass", "isbn", "issn", "note",
]

FALSEY_BIB_VALUES = {"0", "false", "hide", "hidden", "no", "off", "omit"}


def delatex_light(s: str) -> str:
    """Quote/dash cleanup that is safe even when `s` contains math."""
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("\\&", "&").replace("\\%", "%")
    s = s.replace("``", "“").replace("''", "”")
    return s.replace("---", "—").replace("--", "–")


def delatex(s: str) -> str:
    """Best-effort LaTeX-to-text for titles, names and venues."""
    s = delatex_light(s).replace("~", " ")

    def accent(m: re.Match) -> str:
        ch = m.group(2)
        return unicodedata.normalize("NFC", ch + ACCENTS[m.group(1)])

    s = re.sub(r"\\(['\"`^~vcu])\{?\\?([a-zA-Z])\}?", accent, s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def parse_authors(field: str) -> list[str]:
    field = re.sub(r"\s+", " ", field)
    field = re.sub(r"(\s+and)+\s+", " and ", field)  # tolerate "and and" typos
    names = []
    for raw in field.split(" and "):
        raw = raw.strip().strip(",")
        if not raw:
            continue
        if "," in raw:
            last, first = raw.split(",", 1)
            raw = f"{first.strip()} {last.strip()}"
        names.append(delatex(raw))
    return names


def display_authors(names: list[str]) -> list[dict]:
    objs = [{"name": n, "me": "Amini" in n} for n in names]
    if len(objs) <= 14:
        return objs
    shown = objs[:12]
    mine = [o for o in objs[12:] if o["me"]]
    shown.append({"name": "…", "me": False})
    shown.extend(mine)
    shown.append({"name": "et al.", "me": False})
    return shown


def year_of(e: dict) -> int:
    m = re.search(r"\d{4}", e.get("year", "") or e.get("date", ""))
    return int(m.group()) if m else 0


def include_on_site(e: dict) -> bool:
    """Allow one canonical BibTeX file to carry CV-only entries."""
    return e.get("site", "").strip().lower() not in FALSEY_BIB_VALUES


def include_yaml_record(record: dict) -> bool:
    """Allow shared YAML data files to carry records hidden from the website."""
    return str(record.get("site", "")).strip().lower() not in FALSEY_BIB_VALUES


def asset_or_url(value: str) -> str:
    return value if value.startswith("http") else "/assets/pdf/" + quote(value)


def entry_links(e: dict, arxiv: str | None) -> list[tuple[str, str]]:
    links = []
    if arxiv:
        links.append(("arXiv", f"https://arxiv.org/abs/{arxiv}"))
    if e.get("pdf"):
        links.append(("pdf", asset_or_url(e["pdf"])))
    if e.get("doi"):
        links.append(("doi", f"https://doi.org/{e['doi']}"))
    elif e.get("html"):
        links.append(("link", e["html"]))
    elif e.get("url") and not arxiv:
        links.append(("link", e["url"]))
    if e.get("code"):
        links.append(("code", e["code"]))
    if e.get("supp"):
        links.append(("supplement", asset_or_url(e["supp"])))
    for k in ("slides", "poster"):
        if e.get(k):
            links.append((k, asset_or_url(e[k])))
    for k in ("website", "blog"):
        if e.get(k):
            links.append((k, e[k]))
    return links


def format_bibtex(entry_type: str, key: str, e: dict) -> str:
    lines = [f"@{entry_type}{{{key},"]
    for k in BIBTEX_FIELD_ORDER:
        if e.get(k):
            lines.append(f"  {k} = {{{e[k]}}},")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines)


def load_bib() -> list[dict]:
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    with open(ROOT / "data" / "papers.bib") as f:
        db = parser.parse_file(f)

    pubs = []
    for raw in db.entries:
        e = {k.lower(): re.sub(r"\s+", " ", v.strip())
             for k, v in raw.items() if k not in ("ID", "ENTRYTYPE")}
        if not include_on_site(e):
            continue
        arxiv = e.get("arxiv")
        if not arxiv and e.get("eprint"):
            prefix = (e.get("archiveprefix", "") + e.get("eprinttype", "")).lower()
            if "arxiv" in prefix:
                arxiv = e["eprint"]
        venue = delatex(e.get("journal") or e.get("booktitle")
                        or e.get("publisher") or "")
        abbr = e.get("abbr", "")
        if venue.lower() == "preprint":
            venue = ""
        pubs.append({
            "key": raw["ID"],
            "title": delatex(e.get("title", "")),
            "authors": display_authors(parse_authors(e.get("author", ""))),
            "venue": venue,
            "year": year_of(e),
            "abbr": abbr,
            "preprint": abbr.lower() == "preprint",
            "selected": e.get("selected", "").lower() == "true",
            "abstract": delatex_light(e.get("abstract", "")),
            "links": entry_links(e, arxiv),
            "bibtex": format_bibtex(raw["ENTRYTYPE"], raw["ID"], e),
        })
    pubs.sort(key=lambda p: -p["year"])
    return pubs


def group_by_year(pubs: list[dict]) -> list[tuple[int, list[dict]]]:
    groups: dict[int, list] = {}
    for p in pubs:
        groups.setdefault(p["year"], []).append(p)
    return sorted(groups.items(), reverse=True)


# --------------------------------------------------------------------------
# Page rendering
# --------------------------------------------------------------------------

def render(template: str, **ctx) -> str:
    ctx.setdefault("site", SITE)
    return env.get_template(template).render(**ctx)


def render_markdown_page(meta: dict, body: str, active: str | None = None,
                         template: str = "page.html", **extra) -> str:
    body = body.replace("{{ site.baseurl }}", "")
    content = md_convert(body)
    return render(template, page_title=meta.get("title", ""),
                  content=content, math=html_has_math(content),
                  active=active, **extra)


def build_teaching_tree() -> None:
    src_root = ROOT / "teaching"
    for src in src_root.rglob("*"):
        if src.is_dir() or src.name.startswith("."):
            continue
        rel = src.relative_to(ROOT)
        if src.suffix == ".md":
            meta, body = front_matter(src)
            permalink = meta.get("permalink") or "/" + str(rel.with_suffix(""))
            write(permalink, render_markdown_page(meta, body, active="/teaching/"))
        else:
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def build_notes() -> list[dict]:
    notes = []
    for src in sorted((ROOT / "content" / "notes").glob("*.md")):
        meta, body = front_matter(src)
        slug = meta.get("slug") or src.stem
        date = meta.get("date")
        if isinstance(date, dt.datetime):
            date = date.date()
        html = render_markdown_page(meta, body, active="/notes/",
                                    template="note.html",
                                    date=date.strftime("%B %-d, %Y") if date else "")
        write(f"/notes/{slug}/", html)
        notes.append({"slug": slug, "title": meta.get("title", slug),
                      "date": date,
                      "date_fmt": date.strftime("%b %Y") if date else ""})
    notes.sort(key=lambda n: n["date"] or dt.date.min, reverse=True)
    return notes


def build_dir_index(rel_dir: str, title: str) -> None:
    """GitHub Pages has no directory listings; generate one for linked dirs."""
    d = OUT / rel_dir
    if not d.is_dir() or (d / "index.html").exists():
        return
    files = sorted(p.name for p in d.iterdir() if p.is_file())
    items = "\n".join(
        f'<li><a href="{quote(name)}">{name}</a></li>' for name in files)
    write(f"/{rel_dir}/", render("page.html", page_title=title,
                                 content=f"<ul>{items}</ul>", math=False,
                                 active=None))


REDIRECTS = {
    "/misc": "/notes/",
    "/linux-hacks": "/notes/linux-hacks/",
    "/blog/2020/stat-vpn-guide/": "/notes/stat-vpn-guide/",
    "/blog/2021/git-tips/": "/notes/git-tips/",
    "/blog/2022/tikz-graph/": "/notes/tikz-graph/",
    "/blog/2022/fun_with_numpy_broadcasting/": "/notes/numpy-broadcasting/",
    "/blog/2023/canvas-frontpage/": "/notes/canvas-frontpage/",
    "/blog/2023/canvas-change-course-nickname/": "/notes/canvas-course-nickname/",
}


def build() -> None:
    global SITE
    data = ROOT / "data"
    SITE = yaml.safe_load((data / "site.yml").read_text())
    news = yaml.safe_load((data / "news.yml").read_text()) or []
    classes = yaml.safe_load((data / "classes.yml").read_text()) or []
    students = yaml.safe_load((data / "students.yml").read_text()) or []

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    shutil.copytree(ROOT / "assets", OUT / "assets")

    pubs = load_bib()
    pubs_math = any(rendered_pub_has_math(p) for p in pubs)

    # home
    meta, body = front_matter(ROOT / "content" / "index.md")
    bio_md, _, students_md = body.partition("<!--students-->")
    news_items = [{"date_fmt": n["date"].strftime("%b %Y"),
                   "html": md_inline(n["text"])}
                  for n in sorted(news, key=lambda n: n["date"], reverse=True)]
    selected_pubs = [p for p in pubs if p["selected"]]
    bio_html = md_convert(bio_md)
    students_html = md_convert(students_md)
    home_math = (
        html_has_math(bio_html) or html_has_math(students_html)
        or any(html_has_math(n["html"]) for n in news_items)
        or any(rendered_pub_has_math(p) for p in selected_pubs)
    )
    write("/", render("index.html", page_title="",
                      bio=bio_html,
                      students_note=students_html,
                      news=news_items,
                      selected_groups=group_by_year(
                          selected_pubs),
                      pub_count=len(pubs),
                      year_min=min(p["year"] for p in pubs),
                      year_max=max(p["year"] for p in pubs),
                      math=home_math, active="/"))

    # publications
    write("/publications/", render("publications.html",
                                   page_title="Publications",
                                   years=group_by_year(pubs),
                                   pub_count=len(pubs),
                                   year_min=min(p["year"] for p in pubs),
                                   year_max=max(p["year"] for p in pubs),
                                   math=pubs_math, active="/publications/"))

    # teaching
    write("/teaching/", render("teaching.html", page_title="Teaching",
                               current=[c for c in classes if c.get("active")],
                               past=[c for c in classes if not c.get("active")],
                               math=False, active="/teaching/"))
    build_teaching_tree()

    # students
    visible_students = [s for s in students if include_yaml_record(s)]
    write("/students/", render("students.html", page_title="Students",
                               current=[s for s in visible_students if not s.get("alum")],
                               alumni=[s for s in visible_students if s.get("alum")],
                               math=False, active="/students/"))

    # standalone pages, at their historical URLs
    for name, permalink in [("research-faq.md", "/research-faq"),
                            ("pte-policy.md", "/pte-policy")]:
        meta, body = front_matter(ROOT / "content" / name)
        write(permalink, render_markdown_page(meta, body))

    # notes
    notes = build_notes()
    write("/notes/", render("notes.html", page_title="Notes", notes=notes,
                            math=False, active="/notes/"))

    build_dir_index("assets/datafor100c", "Datasets for STATS 100C")

    for old, new in REDIRECTS.items():
        write(old, render("redirect.html", target=new))

    write("/404", render("page.html", page_title="Page not found",
                         content='<p>Nothing here. Try the <a href="/">homepage</a>.</p>',
                         math=False, active=None))

    n_files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"built {n_files} files -> {OUT}")


# --------------------------------------------------------------------------
# Dev server
# --------------------------------------------------------------------------

SOURCE_DIRS = ["data", "content", "templates", "assets", "teaching"]


def snapshot() -> float:
    latest = (ROOT / "build.py").stat().st_mtime
    for d in SOURCE_DIRS:
        for p in (ROOT / d).rglob("*"):
            if p.is_file():
                latest = max(latest, p.stat().st_mtime)
    return latest


class Handler(http.server.SimpleHTTPRequestHandler):
    """Mimic GitHub Pages: serve /foo from foo.html when /foo has no extension."""

    def translate_path(self, path: str) -> str:
        resolved = super().translate_path(path)
        p = Path(resolved)
        if not p.exists() and not p.suffix and Path(str(p) + ".html").exists():
            return str(p) + ".html"
        return resolved

    def log_message(self, *args):
        pass


def serve(port: int = 8000) -> None:
    import threading

    handler = functools.partial(Handler, directory=str(OUT))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"serving http://127.0.0.1:{port} (Ctrl-C to stop)")
    last = snapshot()
    while True:
        time.sleep(1)
        current = snapshot()
        if current != last:
            last = current
            try:
                build()
            except Exception as exc:  # keep serving on a broken edit
                print(f"build failed: {exc}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serve", action="store_true",
                    help="serve locally and rebuild on changes")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    build()
    if args.serve:
        serve(args.port)
