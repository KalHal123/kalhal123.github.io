# Gray Boxes - retro blog

Write posts in Markdown, run one command, get a plain HTML + CSS site.

    content/posts/   one .md file per blog post
    content/pages/   home.md (intro on the front page) and about.md
    templates/       layout.html (the window and menu bar)
    docs/            the finished website. Open docs/index.html. GitHub Pages serves this folder.
    build.py         the builder (Python 3, nothing to install)

## New post
Add a file like `content/posts/my-post.md`:

    ---
    title: My new post
    date: 2026-10-20
    ---
    Your text here, in Markdown.

Then run `python build.py` (on Windows maybe `py build.py`).
To edit a post, change its .md file and run the build again. To delete one, delete the .md file and run it again.
Add `draft: true` under the date to hide a post for now.

## Markdown
`## Heading`, `**bold**`, `*italic*`, `[text](https://example.com)`, `- bullets`, `1. numbers`, `> quote`, `---` divider,
`![alt](/images/pic.png)` for images saved in docs/images/. A link starting with / points inside your site, like `[About](/about.html)`.

## Look
Colors: top of docs/css/style.css. Window and menu: templates/layout.html. Blog name: top of build.py.
Never edit the .html files in docs/ by hand: they are rebuilt every time.
