# haiyanzz 的个人博客

纯静态博客。没有后端、没有框架、没有构建依赖，只有 Markdown 和一个 Python 脚本。推送到 GitHub 后由 Pages 直接托管。

## 目录说明

```
index.html / works.html / about.html / posts/   # 生成产物，不用手改
assets/css/style.css                            # 全部样式都在这里
assets/js/main.js                               # 唯一的 JS：代码块复制按钮
content/posts/                                  # 随笔原文（.md）
content/works.md                                # 作品清单
content/about.md                                # 自我介绍
scripts/build.py                                # 生成脚本
```

## 写一篇随笔

在 `content/posts/` 新建文件，命名格式 `YYYY-MM-DD-标题.md`，例如 `2026-11-26-博客开始了.md`。文件内容：

````markdown
# 文章标题

正文第一段会自动成为首页显示的摘要。

## 小标题

- 一条列表
- 另一条列表

> 引用一句话

这里可以有 **粗体**、*斜体*、`行内代码` 和 [链接](https://example.com)。

```python
print("代码块")
```
````

文件名决定日期和网址，正文第一行 `#` 决定标题，不需要填任何额外信息。

## 生成静态页面

```bash
python3 scripts/build.py
```

生成后直接双击 `index.html` 就能看效果。只有改动了 `content/` 里的内容或样式时才需要重新运行。

## 发布

```bash
git add .
git commit -m "更新博客"
git push
```

GitHub Pages 会自动更新，不需要配置 Actions。

## 支持的 Markdown 语法

标题（`#` / `##` / `###`）、段落、无序与有序列表、引用、分割线、代码块（带语言标记）、行内代码、链接、图片、粗体、斜体。其他复杂语法不支持，也不需要。

## 改样式

所有样式集中在 `assets/css/style.css`，颜色变量在文件开头的 `:root` 里。页面默认跟随系统的浅色/深色模式。
