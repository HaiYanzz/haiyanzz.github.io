#!/usr/bin/env python3
"""极简静态博客生成器：Markdown -> 纯静态 HTML，仅使用 Python 标准库。"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
POSTS_SRC = CONTENT / "posts"
POSTS_OUT = ROOT / "posts"

SITE_TITLE = "haiyanzz"
SITE_DESCRIPTION = "随手写下的想法、笔记和正在做的事。"
SITE_AUTHOR = "haiyanzz"
YEAR = "2026"


def safe_url(url: str) -> str:
    """只允许常见安全协议与相对路径，避免注入 javascript: 之类的链接。"""
    url = url.strip()
    if re.match(r"^(https?://|mailto:|/|\./|\.\./|#)", url, re.I):
        return html.escape(url, quote=True)
    return "#"


def inline(text: str) -> str:
    """行内 Markdown：代码、图片、链接、粗体、斜体。"""
    result = html.escape(text, quote=False)
    codes: list[str] = []

    def stash_code(match: re.Match) -> str:
        codes.append("<code>" + match.group(1) + "</code>")
        return f"\x00CODE{len(codes) - 1}\x00"

    result = re.sub(r"`([^`]+)`", stash_code, result)

    result = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda m: (
            f'<img src="{safe_url(m.group(2))}" '
            f'alt="{html.escape(m.group(1), quote=True)}" loading="lazy">'
        ),
        result,
    )
    result = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{safe_url(m.group(2))}">{m.group(1)}</a>',
        result,
    )
    result = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", result)
    result = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", result)

    for index, code in enumerate(codes):
        result = result.replace(f"\x00CODE{index}\x00", code)
    return result


def is_block_start(line: str) -> bool:
    line = line.strip()
    return bool(
        line.startswith("```")
        or line.startswith(">")
        or re.match(r"^#{1,3}\s+", line)
        or re.match(r"^[-*]\s+", line)
        or re.match(r"^\d+\.\s+", line)
        or re.match(r"^---+$", line)
    )


def render_markdown(text: str) -> str:
    """渲染博客用到的 Markdown 小子集，不追求完整 CommonMark。"""
    lines = text.splitlines()
    output: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        if line.startswith("```"):
            language = line[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            css_class = f' class="language-{html.escape(language, quote=True)}"' if language else ""
            output.append(
                f"<pre><code{css_class}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if re.match(r"^---+$", line.strip()):
            output.append("<hr>")
            i += 1
            continue

        if line.startswith(">"):
            quoted: list[str] = []
            while i < len(lines) and lines[i].startswith(">"):
                quoted.append(lines[i].lstrip(">").strip())
                i += 1
            output.append("<blockquote>" + inline(" ".join(quoted)) + "</blockquote>")
            continue

        if re.match(r"^[-*]\s+", line):
            items: list[str] = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append("<li>" + inline(re.sub(r"^[-*]\s+", "", lines[i])) + "</li>")
                i += 1
            output.append("<ul>" + "".join(items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\d+\.\s+", "", lines[i])) + "</li>")
                i += 1
            output.append("<ol>" + "".join(items) + "</ol>")
            continue

        paragraph = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not is_block_start(lines[i]):
            paragraph.append(lines[i].strip())
            i += 1
        output.append("<p>" + inline(" ".join(paragraph)) + "</p>")

    return "\n".join(output)


def format_date(date_text: str) -> str:
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", date_text)
    if not match:
        return date_text
    return f"{match.group(1)}年{int(match.group(2))}月{int(match.group(3))}日"


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.*)$", line.strip())
        if match:
            return re.sub(r"[*`_]", "", match.group(1)).strip() or fallback
    return fallback


def extract_summary(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("```") or line.startswith("!"):
            continue
        clean = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", line)
        clean = re.sub(r"[*`_>]", "", clean).strip()
        if clean:
            return clean[:80] + ("…" if len(clean) > 80 else "")
    return "暂无摘要。"


def nav_html(active: str, base: str) -> str:
    items = [
        ("index.html", "随笔", "home"),
        ("works.html", "作品", "works"),
        ("about.html", "关于", "about"),
    ]
    links = []
    for href, label, key in items:
        current = ' aria-current="page"' if key == active else ""
        links.append(f'<a href="{base}{href}"{current}>{label}</a>')
    return "\n      ".join(links)


def page(title: str, body: str, active: str = "home", base: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{html.escape(SITE_DESCRIPTION, quote=True)}">
  <title>{html.escape(title)} · {SITE_TITLE}</title>
  <link rel="stylesheet" href="{base}assets/css/style.css">
  <script src="{base}assets/js/main.js" defer></script>
</head>
<body>
  <main>
    <nav class="site-nav" aria-label="主导航">
      {nav_html(active, base)}
    </nav>
{body}
    <footer>© {YEAR} {SITE_AUTHOR}</footer>
  </main>
</body>
</html>
"""


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def load_posts() -> list[dict]:
    posts: list[dict] = []
    for source in sorted(POSTS_SRC.glob("*.md")):
        match = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)$", source.stem)
        if match:
            date, slug = match.group(1), match.group(2)
        else:
            date, slug = "1970-01-01", source.stem

        text = source.read_text(encoding="utf-8")
        body = re.sub(r"(?m)^#\s+.*\n?", "", text, count=1)
        posts.append(
            {
                "date": date,
                "slug": slug,
                "title": extract_title(text, slug),
                "summary": extract_summary(body),
                "body": body,
            }
        )

    posts.sort(key=lambda item: (item["date"], item["slug"]), reverse=True)
    return posts


def build_index(posts: list[dict]) -> None:
    items = [
        f"""    <article class="list-item">
      <time datetime="{post['date']}">{format_date(post['date'])}</time>
      <h2><a href="posts/{post['slug']}.html">{html.escape(post['title'])}</a></h2>
      <p>{html.escape(post['summary'])}</p>
    </article>"""
        for post in posts
    ]
    if not items:
        items.append('    <article class="list-item"><p>还没有随笔，先写一篇吧。</p></article>')

    body = f"""    <p class="kicker">Personal blog</p>
    <h1>{SITE_TITLE}</h1>
    <p class="lead">{SITE_DESCRIPTION}</p>

{chr(10).join(items)}
"""
    write(ROOT / "index.html", page("随笔", body, "home"))


def build_posts(posts: list[dict]) -> None:
    if POSTS_OUT.exists():
        for old in POSTS_OUT.glob("*.html"):
            old.unlink()
    else:
        POSTS_OUT.mkdir(parents=True)

    for index, post in enumerate(posts):
        newer = posts[index - 1] if index > 0 else None
        older = posts[index + 1] if index < len(posts) - 1 else None
        nav_parts = []
        if newer:
            nav_parts.append(
                f'<a href="{newer["slug"]}.html" '
                f'title="{html.escape(newer["title"], quote=True)}">← 上一篇</a>'
            )
        else:
            nav_parts.append("<span></span>")
        if older:
            nav_parts.append(
                f'<a href="{older["slug"]}.html" '
                f'title="{html.escape(older["title"], quote=True)}">下一篇 →</a>'
            )
        else:
            nav_parts.append("<span></span>")

        body = f"""    <article class="post">
      <a class="back" href="../index.html">← 返回随笔</a>
      <time datetime="{post['date']}">{format_date(post['date'])}</time>
      <h1>{html.escape(post['title'])}</h1>
      <div class="post-content">
{render_markdown(post['body'])}
      </div>
      <nav class="post-nav" aria-label="文章导航">
        {' '.join(nav_parts)}
      </nav>
    </article>"""
        write(POSTS_OUT / f"{post['slug']}.html", page(post["title"], body, "home", "../"))


def build_works() -> None:
    source = CONTENT / "works.md"
    text = source.read_text(encoding="utf-8") if source.exists() else ""
    blocks = re.split(r"(?m)^##\s+", text)[1:]
    cards = [
        f"""      <article class="work-card">
        <h2>{inline(title.strip())}</h2>
        {render_markdown(rest)}
      </article>"""
        for title, _, rest in (block.partition("\n") for block in blocks)
    ]
    if not cards:
        cards.append('      <article class="work-card"><h2>暂无作品</h2><p>以后慢慢补上。</p></article>')

    body = f"""    <p class="kicker">Selected works</p>
    <h1>作品</h1>
    <p class="lead">一些做过的东西，想到就放上来。</p>
    <div class="works">
{chr(10).join(cards)}
    </div>"""
    write(ROOT / "works.html", page("作品", body, "works"))


def build_about() -> None:
    source = CONTENT / "about.md"
    text = source.read_text(encoding="utf-8") if source.exists() else "还没有写自我介绍。"
    body = f"""    <p class="kicker">About</p>
    <h1>关于</h1>
    <div class="post-content">
{render_markdown(text)}
    </div>"""
    write(ROOT / "about.html", page("关于", body, "about"))


def main() -> None:
    posts = load_posts()
    build_index(posts)
    build_posts(posts)
    build_works()
    build_about()
    print(f"生成完成：{len(posts)} 篇随笔，首页 / 作品 / 关于各 1 页。")


if __name__ == "__main__":
    main()
