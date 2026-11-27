#!/usr/bin/env python3
"""Turn the vision document (vision.tex) into the content of /vision/.

    python3 tools/vision_to_site.py path/to/vision.tex

Writes three files, all of which are committed:

    _includes/vision-body.html   the document itself
    _data/vision.json            title, authors, date and section titles
    assets/AIM2027...pdf         a copy of the compiled PDF, for download,
                                 named after PDF_NAME below

The PDF is taken from next to the .tex file unless --pdf says otherwise; this
script does not compile it. GitHub Pages cannot run this script, so rerun it by
hand whenever vision.tex changes.

Only the LaTeX that the document actually uses is understood. Anything else
stops the conversion with a message saying what and where, rather than ending
up on the page garbled. Editorial notes (\\tim{...}, \\christoph{...}) stop it
too, unless --draft is given, which shows them highlighted on the page.
"""

import argparse
import datetime
import html
import json
import re
import shutil
import sys
import unicodedata
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# \"o and friends: the combining character that the accent stands for.
ACCENTS = {'"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302",
           "~": "\u0303"}
# Control symbols that stand for a literal character.
SYMBOLS = {"%": "%", "&": "&amp;", "$": "$", "#": "#", "_": "_", "{": "{",
           "}": "}", " ": " ", "\n": " ", ",": "\u202f", "-": "", "/": "",
           "@": ""}
# Macros that only affect LaTeX's spacing or page breaking.
IGNORED = {"maketitle", "noindent", "smallskip", "medskip", "bigskip",
           "newpage", "clearpage", "par", "theendnotes", "printendnotes"}
WRAPPERS = {"emph": "em", "textit": "em", "textbf": "strong", "texttt": "code"}
FOOTNOTES = {"footnote", "endnote"}
LISTS = {"enumerate": "ol", "itemize": "ul"}
# File name under which the PDF is offered for download. A draft, recognised
# by the word "draft" in the document's \date, carries the day it was compiled.
PDF_NAME = "AIM2027FutureOfMathVision"
PDF_DRAFT_SUFFIX = " - draft {date}"
# How many paragraphs of the introduction stay visible above its fold-out.
LEAD_PARAGRAPHS = 2


class ConversionError(Exception):
    pass


def fail(message, text="", pos=0):
    if text:
        snippet = " ".join(text[max(0, pos - 30):pos + 50].split())
        message += f"\n  near: ...{snippet}..."
    raise ConversionError(message)


# ---------------------------------------------------------------- scanning

def strip_comments(src):
    """Remove comments the way TeX does: from % to the end of the line, plus
    the indentation of the next line. A % inside the URL of \\href or \\url is
    part of the URL, and \\% is a percent sign."""
    out, i = [], 0
    while i < len(src):
        m = re.compile(r"\\(href|url)\s*\{").match(src, i)
        if m:
            end = group_end(src, m.end() - 1)
            out.append(src[i:end])
            i = end
        elif src[i] == "\\" and i + 1 < len(src):
            out.append(src[i:i + 2])
            i += 2
        elif src[i] == "%":
            while i < len(src) and src[i] != "\n":
                i += 1
            i += 1
            while i < len(src) and src[i] in " \t":
                i += 1
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def group_end(s, i):
    """Index just past the group whose opening brace is at s[i]."""
    depth = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    fail("unbalanced braces", s, i)


def skip_space(s, i):
    while i < len(s) and s[i].isspace():
        i += 1
    return i


def read_group(s, i, what):
    """Read a {...} argument starting at or after i. Returns (content, end)."""
    i = skip_space(s, i)
    if i >= len(s) or s[i] != "{":
        fail(f"expected {{...}} after {what}", s, i)
    end = group_end(s, i)
    return s[i + 1:end - 1], end


def read_optional(s, i):
    """Read a [...] argument at i if there is one. Returns (content, end)."""
    j = skip_space(s, i)
    if j < len(s) and s[j] == "[":
        end = s.index("]", j)
        return s[j + 1:end], end + 1
    return None, i


def env_end(s, i, name):
    """s[i:] starts just after \\begin{name}. Returns (start of the matching
    \\end{name}, index just past it)."""
    depth = 1
    for m in re.compile(r"\\(begin|end)\{%s\}" % re.escape(name)).finditer(s, i):
        depth += 1 if m.group(1) == "begin" else -1
        if depth == 0:
            return m.start(), m.end()
    fail(f"\\begin{{{name}}} without \\end{{{name}}}", s, i)


def slugify(text):
    text = unicodedata.normalize("NFKD", html.unescape(re.sub(r"<[^>]+>", "", text)))
    text = text.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# -------------------------------------------------------------- conversion

class Converter:
    def __init__(self, editorial, draft, today):
        self.editorial = editorial  # macro name -> person's name
        self.draft = draft
        self.today = today
        self.notes = []             # footnote HTML, in order of appearance
        self.labels = {}            # label -> (number, anchor)
        self.target = None          # what a \label here would refer to
        self.ids = set()
        self.editorial_seen = 0

    def unique_id(self, text):
        base = slugify(text) or "item"
        candidate, n = base, 2
        while candidate in self.ids:
            candidate, n = f"{base}-{n}", n + 1
        self.ids.add(candidate)
        return candidate

    # -- inline text ------------------------------------------------------

    def inline(self, s):
        out, i = [], 0
        while i < len(s):
            c = s[i]
            if c == "\\":
                i = self.macro(s, i, out)
            elif c == "{":
                end = group_end(s, i)
                out.append(self.inline(s[i + 1:end - 1]))
                i = end
            elif c == "}":
                fail("unmatched }", s, i)
            elif c == "$":
                # A lone symbol such as $L$ is set in italics. Anything more
                # would need a real math renderer.
                m = re.compile(r"\$([A-Za-z0-9]+)\$").match(s, i)
                if not m:
                    fail("math beyond a single symbol is not supported", s, i)
                out.append(f"<i>{m.group(1)}</i>")
                i = m.end()
            elif c == "~":
                out.append("&nbsp;")
                i += 1
            elif s.startswith("---", i):
                out.append("\u2014")
                i += 3
            elif s.startswith("--", i):
                out.append("\u2013")
                i += 2
            elif s.startswith("``", i):
                out.append("\u201c")
                i += 2
            elif s.startswith("''", i):
                out.append("\u201d")
                i += 2
            elif c == "`":
                out.append("\u2018")
                i += 1
            elif c == "'":
                out.append("\u2019")
                i += 1
            else:
                out.append(html.escape(c, quote=False))
                i += 1
        return "".join(out)

    def macro(self, s, i, out):
        """Handle the macro at s[i], append its HTML to out, return the index
        after it."""
        m = re.compile(r"\\([A-Za-z]+)\*?").match(s, i)
        if not m:
            return self.symbol(s, i, out)
        name, j = m.group(1), m.end()

        if name in WRAPPERS:
            arg, j = read_group(s, j, "\\" + name)
            out.append(f"<{WRAPPERS[name]}>{self.inline(arg)}</{WRAPPERS[name]}>")
        elif name == "href":
            url, j = read_group(s, j, "\\href")
            text, j = read_group(s, j, "\\href{...}")
            out.append(f'<a href="{self.url(url)}">{self.inline(text)}</a>')
        elif name == "url":
            url, j = read_group(s, j, "\\url")
            out.append(f'<a href="{self.url(url)}">{html.escape(self.plain_url(url))}</a>')
        elif name in FOOTNOTES:
            arg, j = read_group(s, j, "\\" + name)
            self.notes.append(None)  # claim the number before nested notes
            n = len(self.notes)
            self.notes[n - 1] = self.inline(arg.strip())
            out.append(f'<sup class="noteref"><a href="#note-{n}" id="noteref-{n}" '
                       f'aria-label="Note {n}">{n}</a></sup>')
        elif name == "label":
            label, j = read_group(s, j, "\\label")
            if self.target is None:
                fail(f"\\label{{{label}}} is not attached to a section, "
                     "statement or list item", s, i)
            self.labels[label] = self.target
            j = skip_space(s, j)
        elif name == "ref":
            label, j = read_group(s, j, "\\ref")
            out.append(f"\x00{label}\x00")  # resolved once all labels are known
        elif name in self.editorial:
            arg, j = read_group(s, j, "\\" + name)
            self.editorial_seen += 1
            if not self.draft:
                fail(f"editorial note by {self.editorial[name]} is still in the "
                     "text (use --draft to show such notes on the page)", s, i)
            out.append(f'<mark class="vision-note">{self.editorial[name]}: '
                       f"{self.inline(arg)}</mark>")
        elif name in ("ldots", "dots"):
            out.append("\u2026")
        elif name == "today":
            out.append(self.today)
        elif name in IGNORED:
            j = skip_space(s, j)
        elif name in ("begin", "end"):
            env, _ = read_group(s, j, "\\" + name)
            fail(f"the {env} environment is not supported here", s, i)
        else:
            fail(f"\\{name} is not supported", s, i)

        # TeX swallows the spaces after a control word.
        if name in ("ldots", "dots", "today"):
            j = skip_space(s, j)
        return j

    def symbol(self, s, i, out):
        c = s[i + 1] if i + 1 < len(s) else ""
        if c == "\\":
            out.append("<br>")
            return i + 2
        if c in ACCENTS:
            j = skip_space(s, i + 2)
            if s[j] == "{":
                letter, j = read_group(s, j, "accent")
            else:
                letter, j = s[j], j + 1
            out.append(unicodedata.normalize("NFC", letter + ACCENTS[c]))
            return j
        if c in SYMBOLS:
            out.append(SYMBOLS[c])
            return i + 2
        fail(f"\\{c} is not supported", s, i)

    @staticmethod
    def plain_url(url):
        return re.sub(r"\\([%#_&~])", r"\1", url.strip())

    def url(self, url):
        return html.escape(self.plain_url(url), quote=True)

    # -- paragraphs and lists ---------------------------------------------

    def blocks(self, s):
        """Convert running text with paragraphs and lists to a list of HTML
        blocks."""
        result, i = [], 0
        begin = re.compile(r"\\begin\{(%s)\}" % "|".join(LISTS))
        while True:
            m = begin.search(s, i)
            text = s[i:m.start() if m else len(s)]
            for para in re.split(r"\n\s*\n", text):
                if para.strip():
                    body = self.inline(" ".join(para.split()))
                    if body.strip():
                        result.append(f"<p>{body.strip()}</p>")
            if not m:
                return result
            inner_end, i = env_end(s, m.end(), m.group(1))
            result.append(self.list(s[m.end():inner_end], LISTS[m.group(1)]))

    def list(self, s, tag):
        _, start = read_optional(s, 0)  # enumitem options: layout only
        items, depth, last = [], 0, None
        for m in re.compile(r"\\(begin|end)\{[^}]*\}|\\item\b").finditer(s, start):
            if m.group(1):
                depth += 1 if m.group(1) == "begin" else -1
            elif depth == 0:
                if last is None and s[start:m.start()].strip():
                    fail("text before the first \\item", s, start)
                if last is not None:
                    items.append(s[last:m.start()])
                last = m.end()
        if last is None:
            fail("list without \\item", s, start)
        items.append(s[last:])

        outer, lines = self.target, [f"<{tag}>"]
        for n, item in enumerate(items, 1):
            # A label on an item is cited by the item's number and links to
            # whatever the list sits in.
            self.target = (str(n), outer[1] if outer else None)
            parts = self.blocks(item)
            if len(parts) == 1 and parts[0].startswith("<p>"):
                parts = [parts[0][3:-4]]
            lines.append("<li>" + "\n".join(parts) + "</li>")
        self.target = outer
        lines.append(f"</{tag}>")
        return "\n".join(lines)

    # -- document structure -----------------------------------------------

    def document(self, body):
        """Parse the document body into the introduction and the sections."""
        intro, sections, i = [], [], 0
        block = re.compile(r"\\section(\*?)\s*\{|\\begin\{(\w+)\}")
        while True:
            m = block.search(body, i)
            # A list is part of the running text around it.
            while m and m.group(2) in LISTS:
                _, past = env_end(body, m.end(), m.group(2))
                m = block.search(body, past)
            loose = self.blocks(body[i:m.start() if m else len(body)])
            if sections:
                sections[-1]["blocks"] += [("text", b) for b in loose]
            else:
                intro += loose
            if not m:
                break

            if m.group(2) is None:
                title, i = read_group(body, m.end() - 1, "\\section")
                # \section* is unnumbered, so there is no number to cite and
                # none for statements to build on.
                number = None
                if not m.group(1):
                    number = str(sum(s["number"] is not None for s in sections) + 1)
                title = self.inline(title.strip())
                anchor = self.unique_id(title)
                sections.append({"number": number, "title": title,
                                 "id": anchor, "blocks": []})
                self.target = (number, anchor) if number else None
                continue

            env = m.group(2)
            inner_end, i = env_end(body, m.end(), env)
            inner = body[m.end():inner_end]
            if env not in ("soundbite", "statement", "details", "advice"):
                fail(f"the {env} environment is not supported", body, m.start())
            if not sections:
                fail(f"{env} before the first \\section", body, m.start())
            section = sections[-1]
            statements = [b for kind, b in section["blocks"] if kind == "statement"]

            if env == "soundbite":
                section["blocks"].append(("soundbite", "\n".join(self.blocks(inner))))
            elif env == "statement":
                if section["number"] is None:
                    fail("statement in an unnumbered section", body, m.start())
                title, start = read_group(inner, 0, "\\begin{statement}")
                number = f"{section['number']}.{len(statements) + 1}"
                title = self.inline(title.strip())
                anchor = self.unique_id(title)
                self.target = (number, anchor)
                section["blocks"].append(("statement", {
                    "number": number, "title": title, "id": anchor,
                    "claim": self.blocks(inner[start:]),
                    "details": [], "advice": [], "advice_label": None}))
            else:
                if not statements or section["blocks"][-1][0] != "statement":
                    fail(f"{env} block does not follow a statement", body, m.start())
                statement = statements[-1]
                self.target = (statement["number"], statement["id"])
                if env == "details":
                    statement["details"] += self.blocks(inner)
                else:
                    label, start = read_optional(inner, 0)
                    statement["advice_label"] = self.inline(label or "Recommendations")
                    statement["advice"] += self.blocks(inner[start:])
        return intro, sections

    def resolve(self, text):
        def link(m):
            if m.group(1) not in self.labels:
                fail(f"\\ref{{{m.group(1)}}} refers to a label that does not exist")
            number, anchor = self.labels[m.group(1)]
            return f'<a href="#{anchor}">{number}</a>' if anchor else number
        return re.sub("\x00([^\x00]*)\x00", link, text)


# ---------------------------------------------------------------- rendering

def render_statement(st):
    lines = [f'<section class="statement" id="{st["id"]}">',
             f'<span class="statement__number" aria-hidden="true">{st["number"]}</span>',
             f'<h3 class="statement__title"><span class="visually-hidden">'
             f'{st["number"]} </span>{st["title"]}</h3>',
             '<div class="statement__claim">', *st["claim"], "</div>"]
    if st["details"] or st["advice"]:
        label = st["advice_label"] or ""
        if st["details"] and st["advice"]:
            summary = f"Details and {label[:1].lower()}{label[1:]}"
        else:
            summary = "Details" if st["details"] else label
        lines += ['<details class="fold">', f"<summary>{summary}</summary>",
                  '<div class="fold__body">']
        if st["details"]:
            lines += ['<div class="statement__details">', *st["details"], "</div>"]
        if st["advice"]:
            lines.append('<div class="statement__advice">')
            if st["details"]:  # otherwise the summary already says it
                lines.append(f"<h4>{label}</h4>")
            lines += [*st["advice"], "</div>"]
        lines += ["</div>", "</details>"]
    lines.append("</section>")
    return lines


def render(intro, sections, notes, source_name):
    lines = [f"<!-- Generated from {source_name} by tools/vision_to_site.py. "
             "Do not edit: rerun the script instead. -->",
             "{% raw %}"]
    if intro:
        lines += ['<section class="vision-intro">', *intro[:LEAD_PARAGRAPHS]]
        if len(intro) > LEAD_PARAGRAPHS:
            lines += ['<details class="fold">',
                      "<summary>Read the full introduction</summary>",
                      '<div class="fold__body">', *intro[LEAD_PARAGRAPHS:],
                      "</div>", "</details>"]
        lines.append("</section>")
    for section in sections:
        blocks = section["blocks"]
        if section["number"] is None:
            lines += [f'<section class="vision-section" id="{section["id"]}">',
                      f'<h2>{section["title"]}</h2>']
            # An unnumbered section of plain text, such as the introduction:
            # its opening paragraphs, and the rest behind a fold-out.
            if (len(blocks) > LEAD_PARAGRAPHS
                    and all(kind == "text" for kind, _ in blocks)):
                title = html.unescape(re.sub(r"<[^>]+>", "", section["title"]))
                lines += [*(b for _, b in blocks[:LEAD_PARAGRAPHS]),
                          '<details class="fold">',
                          f"<summary>Read the full {html.escape(title.lower())}</summary>",
                          '<div class="fold__body">',
                          *(b for _, b in blocks[LEAD_PARAGRAPHS:]),
                          "</div>", "</details>"]
                blocks = []
        else:
            lines += [f'<section class="vision-section" id="{section["id"]}">',
                      f'<h2><span class="vision-section__number">{section["number"]}'
                      f'</span> {section["title"]}</h2>']
        for kind, block in blocks:
            if kind == "soundbite":
                lines += ['<div class="vision-soundbite">', block, "</div>"]
            elif kind == "statement":
                lines += render_statement(block)
            else:
                lines.append(block)
        lines.append("</section>")
    if notes:
        lines += ['<section class="vision-notes" id="notes">', "<h2>Notes</h2>", "<ol>"]
        for n, note in enumerate(notes, 1):
            lines.append(f'<li id="note-{n}">{note} <a class="vision-notes__back" '
                         f'href="#noteref-{n}" aria-label="Back to the text">'
                         "\u21a9\ufe0e</a></li>")
        lines += ["</ol>", "</section>"]
    lines.append("{% endraw %}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------- main

def pdf_date(pdf):
    """The day the PDF was compiled: that is what \\today printed in it."""
    m = re.search(rb"/CreationDate\s*\(D:(\d{4})(\d{2})(\d{2})", pdf.read_bytes())
    if m:
        return datetime.date(*(int(g) for g in m.groups()))
    return datetime.date.fromtimestamp(pdf.stat().st_mtime)


def convert(tex, pdf, draft):
    src = strip_comments(tex.read_text(encoding="utf-8"))
    start, end = src.find(r"\begin{document}"), src.find(r"\end{document}")
    if start < 0 or end < 0:
        fail("no \\begin{document} ... \\end{document} found")
    preamble, body = src[:start], src[start + len(r"\begin{document}"):end]

    editorial = dict(re.findall(
        r"\\newcommand\{\\(\w+)\}\[1\]\{\{\\color\{\w+\}(\w+): #1\}\}", preamble))
    day = pdf_date(pdf)
    converter = Converter(editorial, draft, f"{day.day} {MONTHS[day.month - 1]} {day.year}")

    def field(name):
        m = re.search(r"\\%s\s*\{" % name, preamble)
        return read_group(preamble, m.end() - 1, "\\" + name)[0] if m else ""

    def plain(text):
        return html.unescape(converter.inline(" ".join(text.split())))

    title = [plain(part) for part in field("title").split(r"\\")]
    authors = []
    for author in re.split(r"\\and\b", field("author")):
        name, _, role = author.partition(r"\\")
        if name.strip():
            authors.append({"name": plain(name), "role": plain(role)})
    meta = {"title": title[0], "subtitle": " ".join(title[1:]),
            "authors": authors, "date": plain(field("date"))}
    name = PDF_NAME
    if "draft" in meta["date"].lower():
        name += PDF_DRAFT_SUFFIX.format(date=day.strftime("%d-%m-%Y"))
    # The name has spaces in it, so the page needs it escaped for its link.
    meta["pdf"] = name + ".pdf"
    meta["pdf_url"] = urllib.parse.quote(meta["pdf"])

    intro, sections = converter.document(body)
    # The numbered sections, for the list of topics on the front page.
    meta["sections"] = [
        {"number": s["number"], "id": s["id"],
         "title": html.unescape(re.sub(r"<[^>]+>", "", s["title"]))}
        for s in sections if s["number"] is not None]
    body_html = converter.resolve(
        render(intro, sections, converter.notes, tex.name))
    return meta, body_html, converter, sections


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("tex", type=Path, help="path to vision.tex")
    parser.add_argument("--pdf", type=Path,
                        help="compiled PDF (default: next to the .tex file)")
    parser.add_argument("--draft", action="store_true",
                        help="show editorial notes on the page instead of stopping")
    args = parser.parse_args()
    pdf = args.pdf or args.tex.with_suffix(".pdf")
    for path in (args.tex, pdf):
        if not path.is_file():
            sys.exit(f"error: {path} does not exist")

    try:
        meta, body_html, converter, sections = convert(args.tex, pdf, args.draft)
    except ConversionError as error:
        sys.exit(f"error: {error}")

    (ROOT / "_includes").mkdir(exist_ok=True)
    (ROOT / "_includes/vision-body.html").write_text(body_html, encoding="utf-8")
    (ROOT / "_data/vision.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Only one version is on offer at a time: clear out earlier copies.
    for old in [*(ROOT / "assets").glob(PDF_NAME + "*.pdf"), ROOT / "assets/vision.pdf"]:
        old.unlink(missing_ok=True)
    shutil.copyfile(pdf, ROOT / "assets" / meta["pdf"])

    statements = sum(kind == "statement" for s in sections for kind, _ in s["blocks"])
    print(f"{meta['title']} ({meta['date']})")
    print(f"{len(sections)} sections, {statements} statements, "
          f"{len(converter.notes)} notes")
    if pdf.stat().st_mtime < args.tex.stat().st_mtime:
        print(f"warning: {pdf.name} is older than {args.tex.name}; recompile "
              "it and run this again", file=sys.stderr)
    if converter.editorial_seen:
        print(f"warning: {converter.editorial_seen} editorial note(s) are shown "
              "on the page; do not publish this version", file=sys.stderr)


if __name__ == "__main__":
    main()
