---
title: How to write a post
---
# How to write a post

Every post is one Markdown file. No code needed.

## Add a new post

1. Create a file in **content/posts/**, for example `my-new-post.md`. The file name becomes the page address.
2. Start it with these four lines:

```
---
title: My new post
date: 2026-10-20
tags: lorem, ipsum
summary: One sentence shown in the post lists.
---
```

3. Write your text under the lines, using Markdown (below).
4. Run `python build.py` in the project folder, then open **docs/index.html**.

To hide a post for now, add `draft: true` to the top section. To edit one, change its .md file and run the build again. To delete one, delete its .md file.

## Markdown cheat sheet

- `## Heading` and `### Smaller heading`
- `**bold**`, `*italic*`, and `code` between backticks
- `[link text](https://example.com)`
- `![alt text](/images/photo.png)` for pictures saved in docs/images/
- `- item` for bullet lists, `1. item` for numbered lists
- `> quote` for quotes, `---` for a divider
- Three backticks on their own line start and end a code block

A link that begins with a slash points inside your site, for example `[About](/about.html)` or `[a post](/posts/my-new-post.html)`.

## Pages

The Home, About, Links, Guestbook and Help pages are Markdown too. Edit them in **content/pages/**.

## Changing the look

- Colors and styles: **docs/css/style.css**
- Page frame, menus and sidebar: **templates/layout.html**
- Post header and Older / Newer buttons: **templates/post.html**
- Blog name, email and counts: the top of **build.py**
