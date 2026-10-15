#!/usr/bin/env python3
"""Tiny static site builder. No installs needed, just Python 3.

    python build.py

Reads Markdown from content/, fills templates/layout.html, writes plain HTML into docs/.
"""
import html, re
from datetime import datetime, date
from pathlib import Path

SITE_NAME = "Gray Boxes"     # shown in every title bar

ROOT = Path(__file__).parent
CONTENT, TEMPLATES, SITE = ROOT / "content", ROOT / "templates", ROOT / "docs"


def parse(path):
    """Split a .md file into (front matter dict, body text)."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    meta = {}
    if text.startswith("---\n"):
        head, _, text = text[4:].partition("\n---")
        for line in head.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
    return meta, text.strip()


def inline(t, root):
    """Bold, italic, `code`, links, images. A leading / in a link means 'site root'."""
    t = html.escape(t, quote=False)
    codes = []
    def stash(m):
        codes.append("<code>" + m.group(1) + "</code>")
        return "\x00%d\x00" % (len(codes) - 1)
    t = re.sub(r"`([^`]+)`", stash, t)
    fix = lambda u: root + u[1:] if u.startswith("/") and not u.startswith("//") else u
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", lambda m: '<img src="%s" alt="%s">' % (fix(m[2]), m[1]), t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: '<a href="%s">%s</a>' % (fix(m[2]), m[1]), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m[1])], t)


LIST_RE = re.compile(r"([-*]|\d+\.) ")


def markdown(src, root=""):
    out, lines, i = [], src.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("```"):                       # code block
            i, code = i + 1, []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            out.append("<pre>" + html.escape("\n".join(code)) + "</pre>")
        elif re.match(r"#{1,3} ", line):                   # headings
            n = len(line.split(" ")[0])
            out.append("<h%d>%s</h%d>" % (n, inline(line[n + 1:], root), n)); i += 1
        elif re.fullmatch(r"-{3,}|\*{3,}", line.strip()):  # divider
            out.append("<hr>"); i += 1
        elif line.startswith(">"):                         # quote
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i][1:].strip()); i += 1
            out.append("<blockquote>" + inline(" ".join(q), root) + "</blockquote>")
        elif LIST_RE.match(line):                          # lists
            tag = "ol" if line[0].isdigit() else "ul"
            items = []
            while i < len(lines) and LIST_RE.match(lines[i]):
                items.append("<li>" + inline(LIST_RE.sub("", lines[i], 1), root) + "</li>"); i += 1
            out.append("<%s>%s</%s>" % (tag, "".join(items), tag))
        elif line.startswith("<"):                         # raw HTML passes through
            raw = []
            while i < len(lines) and lines[i].strip():
                raw.append(lines[i]); i += 1
            out.append("\n".join(raw))
        else:                                              # paragraph
            para = [line]; i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"(#{1,3} |```|>|<)|([-*]|\d+\.) ", lines[i]):
                para.append(lines[i]); i += 1
            out.append("<p>" + inline(" ".join(para), root) + "</p>")
    return "\n".join(out)


def fill(content, **values):
    t = (TEMPLATES / "layout.html").read_text(encoding="utf-8")
    for k, v in values.items():
        t = t.replace("{{%s}}" % k, str(v))
    return t.replace("{{content}}", content)   # content last


def main():
    posts = []
    for f in sorted((CONTENT / "posts").glob("*.md")):
        meta, body = parse(f)
        if meta.get("draft", "").lower() in ("true", "yes"):
            continue
        d = datetime.strptime(meta.get("date") or date.today().isoformat(), "%Y-%m-%d")
        posts.append(dict(url="posts/%s.html" % f.stem, body=body, date=d, date_str=d.strftime("%d %b %Y"),
                          title=meta.get("title") or f.stem.replace("-", " ").title()))
    if not posts:
        raise SystemExit("No posts found in content/posts/")
    posts.sort(key=lambda p: p["date"], reverse=True)

    # clear old pages (css/ and images/ are left alone)
    for old in list(SITE.glob("*.html")) + list((SITE / "posts").glob("*.html")):
        old.unlink()

    def write(path, title, content):
        page = fill(content, title=html.escape(title), site_name=SITE_NAME,
                    root="../" * path.count("/"), latest=posts[0]["url"])
        out = SITE / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")

    # home page = all posts (optional intro text from content/pages/home.md)
    intro = ""
    if (CONTENT / "pages" / "home.md").exists():
        intro = markdown(parse(CONTENT / "pages" / "home.md")[1]) + "\n"
    rows = "\n".join('<li><a href="%s">%s</a><time>%s</time></li>' % (p["url"], html.escape(p["title"]), p["date_str"])
                     for p in posts)
    write("index.html", "All posts", intro + "<h2>All posts</h2>\n<ul class=\"post-list\">\n" + rows + "\n</ul>")

    # other pages, e.g. content/pages/about.md -> docs/about.html
    for f in sorted((CONTENT / "pages").glob("*.md")):
        if f.stem != "home":
            meta, body = parse(f)
            write(f.stem + ".html", meta.get("title", f.stem.title()), markdown(body))

    # each post
    for p in posts:
        write(p["url"], p["title"], "<h1>%s</h1>\n<p class=\"meta\">%s</p>\n%s" % (
            html.escape(p["title"]), p["date_str"], markdown(p["body"], "../")))

    print("Built %d posts into docs/  (open docs/index.html)" % len(posts))


if __name__ == "__main__":
    main()
