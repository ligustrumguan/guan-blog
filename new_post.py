#!/usr/bin/env python3
"""简单的新文章生成脚本

功能：
- 交互式输入标题、摘要、标签等信息
- 自动生成 posts/*.md 的 Markdown 文件（带 front-matter 模板）
- 自动更新 posts/posts.json，追加一条新的文章配置

使用方法（在项目根目录 guan-blog/ 运行）：
    python3 new_post.py
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
POSTS_DIR = BASE_DIR / "posts"
POSTS_JSON = POSTS_DIR / "posts.json"


def slugify(title: str) -> str:
    """把标题转成比较适合当 id 的字符串（简单版）。"""
    title = title.strip().lower()
    # 替换空白为 -
    title = re.sub(r"\s+", "-", title)
    # 保留中英文、数字和 - _，其它去掉
    title = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fa5_-]", "", title)
    if not title:
        # 兜底：用日期做一个 id
        return f"post-{date.today().isoformat()}"
    return title


def prompt(msg: str, default: str | None = None) -> str:
    if default:
        raw = input(f"{msg} [{default}]: ").strip()
        return raw or default
    return input(f"{msg}: ").strip()


def load_posts_json() -> list[dict]:
    if not POSTS_JSON.exists():
        return []
    try:
        data = json.loads(POSTS_JSON.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_posts_json(posts: list[dict]) -> None:
    POSTS_JSON.write_text(
        json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    print("=== 创建一篇新的博客文章 ===")

    today = date.today().isoformat()

    title = prompt("标题", "新文章")
    default_id = slugify(title)
    post_id = prompt("文章 id（用于 URL，如 my-first-post）", default_id)
    post_date = prompt("发布日期 (YYYY-MM-DD)", today)
    summary = prompt("文章简介 (summary)", "一篇新的博客文章。")
    tags_raw = prompt("标签（用逗号分隔）", "随笔")
    tags = [t.strip() for t in tags_raw.split(";") if t.strip()] if ";" in tags_raw else [t.strip() for t in tags_raw.split(",") if t.strip()]

    default_filename = f"{post_id}.md"
    filename = prompt("Markdown 文件名（位于 posts/ 目录下）", default_filename)

    # 确保 posts 目录存在
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    md_path = POSTS_DIR / filename
    if md_path.exists():
        overwrite = prompt(f"文件 {filename} 已存在，是否覆盖？(y/N)", "N")
        if overwrite.lower() not in {"y", "yes"}:
            print("已取消创建文章。")
            return

    # 生成 Markdown 模板
    front_matter = (
        "---\n"
        f"Title: {title}\n"
        f"Date: {post_date}\n"
        f"Tags: {', '.join(tags)}\n"
        f"Summary: {summary}\n"
        "---\n\n"
    )
    body = (
        f"# {title}\n\n"
        f"日期：{post_date}\n\n"
        "在这里开始写正文内容……\n\n"
        "可以使用 Markdown 语法：**加粗**、`代码`、列表等。\n"
    )

    md_path.write_text(front_matter + body, encoding="utf-8")
    print(f"已生成 Markdown 文件: posts/{filename}")

    # 更新 posts.json
    posts = load_posts_json()

    new_entry = {
        "id": post_id,
        "title": title,
        "date": post_date,
        "summary": summary,
        "tags": tags,
        "file": filename,
    }

    # 如果已有同 id 条目，则替换
    replaced = False
    for i, p in enumerate(posts):
        if str(p.get("id")) == post_id:
            posts[i] = new_entry
            replaced = True
            break

    if not replaced:
        posts.append(new_entry)

    save_posts_json(posts)
    print("已更新 posts/posts.json 中的文章列表。")
    print("\n完成！你现在可以在浏览器里访问：")
    print(f"  post.html?id={post_id}")


if __name__ == "__main__":
    main()
