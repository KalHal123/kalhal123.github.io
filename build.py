#!/usr/bin/env python3
"""Tiny static site builder. No installs needed, just Python 3.

    python build.py

Reads Markdown from content/, fills templates/, writes plain HTML into docs/.
"""
import html, re
from datetime import datetime, date
from pathlib import Path

# ---- settings -------------------------------------------------------------
SITE_NAME = "Gray Boxes"
SITE_URL = "http://grayboxes.example"   # only shown in the fake address bar
EMAIL = "you@example.com"
HOME_POSTS = 5        # posts listed on the home page
SIDEBAR_POSTS = 6     # posts listed in the File Cabinet window
# ---------------------------------------------------------------------------

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


def tpl(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def fill(t, content=None, **values):
    for k, v in values.items():
        t = t.replace("{{%s}}" % k, str(v))
    return t if content is None else t.replace("{{content}}", content)  # content last


def post_list(posts, root, tags=False):
    rows = []
    for p in posts:
        extra = ("<br><small>filed under: %s</small>" % ", ".join(p["tags"])) if tags and p["tags"] else ""
        rows.append('<li><a href="%s%s">%s</a><span class="post-date">%s</span><br>'
                    '<span class="post-summary">%s</span>%s</li>'
                    % (root, p["url"], html.escape(p["title"]), p["date_str"], html.escape(p["summary"]), extra))
    return '<ul class="post-list">\n' + "\n".join(rows) + "\n</ul>"


def main():
    # ---- load posts ----
    posts = []
    for f in sorted((CONTENT / "posts").glob("*.md")):
        meta, body = parse(f)
        if meta.get("draft", "").lower() in ("true", "yes"):
            continue
        d = datetime.strptime(meta.get("date") or date.today().isoformat(), "%Y-%m-%d")
        posts.append(dict(
            url="posts/%s.html" % f.stem, body=body, date=d, date_str=d.strftime("%d %b %Y"),
            title=meta.get("title") or f.stem.replace("-", " ").title(),
            tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            summary=meta.get("summary", "")))
    if not posts:
        raise SystemExit("No posts found in content/posts/")
    posts.sort(key=lambda p: p["date"], reverse=True)

    # ---- clear old output (css/ and images/ are left alone) ----
    for old in list(SITE.glob("*.html")) + list((SITE / "posts").glob("*.html")):
        old.unlink()

    def write(path, title, content):
        path = Path(path).as_posix()
        root = "../" * path.count("/")
        recent = "\n".join(
            '<li><span>%s<a href="%s%s">%s</a></span><time>%s</time></li>'
            % ('<span class="new">NEW</span> ' if n == 0 else "", root, p["url"],
               html.escape(p["title"]), p["date"].strftime("%d %b"))
            for n, p in enumerate(posts[:SIDEBAR_POSTS]))
        page = fill(tpl("layout.html"), content=content,
                    title=html.escape(title), site_name=SITE_NAME, root=root, path=path,
                    address="%s/%s" % (SITE_URL, "" if path == "index.html" else path),
                    latest=posts[0]["url"], email=EMAIL, post_count=len(posts), recent_posts=recent)
        out = SITE / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")

    # ---- pages (content/pages/*.md -> docs/<name>.html; home.md -> index.html) ----
    pages = 0
    for f in sorted((CONTENT / "pages").glob("*.md")):
        meta, body = parse(f)
        body = markdown(body)
        if f.stem == "home":
            body += "\n<h2>Latest posts</h2>\n" + post_list(posts[:HOME_POSTS], "") + \
                    '\n<p><a class="btn raised" href="archive.html">All posts</a></p>'
            write(Path("index.html"), meta.get("title", "Home"), body)
        else:
            write(Path(f.stem + ".html"), meta.get("title", f.stem.title()), body)
        pages += 1

    # ---- archive ----
    write(Path("archive.html"), "Archive",
          "<h1>Archive</h1>\n<p class=\"meta\">%d posts, newest first</p>\n" % len(posts) + post_list(posts, "", tags=True))

    # ---- posts ----
    def nav(label, p, root):
        if p is None:
            return '<span class="btn raised disabled">%s</span>' % label
        return '<a class="btn raised" href="%s%s" title="%s">%s</a>' % (root, p["url"], html.escape(p["title"]), label)

    for n, p in enumerate(posts):
        newer = posts[n - 1] if n > 0 else None
        older = posts[n + 1] if n + 1 < len(posts) else None
        words = len(p["body"].split())
        inner = fill(tpl("post.html"), content=markdown(p["body"], "../"),
                     title=html.escape(p["title"]), date=p["date_str"], read_time=max(1, round(words / 200)),
                     tags=(" &middot; filed under: " + html.escape(", ".join(p["tags"]))) if p["tags"] else "",
                     newer=nav("&lt; Newer post", newer, "../"), older=nav("Older post &gt;", older, "../"))
        write(Path(p["url"]), p["title"], inner)

    print("Built %d posts and %d pages into docs/  (open docs/index.html)" % (len(posts), pages + 1))


if __name__ == "__main__":
    main()
