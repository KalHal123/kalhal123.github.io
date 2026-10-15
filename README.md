# Gray Boxes - retro blog

Write posts in Markdown, run one command, get a plain HTML + CSS site.

    content/posts/   one .md file per blog post
    content/pages/   home, about, links, guestbook, help (also .md)
    templates/       layout.html (page frame) and post.html
    docs/            the finished website: open docs/index.html, upload this folder
    build.py         the builder (Python 3, nothing to install)

New post: add a .md file to content/posts/, then run:

    python build.py

(on Windows you may need `py build.py`). The built pages in docs/ are regenerated every time, so edit the .md files and templates, not the .html files.
Full instructions are on the Help page of the site.
