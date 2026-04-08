from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Any

from flask import Flask, flash, redirect, render_template, request, url_for

# 复用 new_post.py 里的工具和路径配置
from new_post import POSTS_DIR, load_posts_json, save_posts_json, slugify

BASE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = BASE_DIR / "profile.json"

app = Flask(__name__)
# 本地使用的简单密钥，用于 flash 消息；如果对外部署请改成更安全的随机值
app.secret_key = "dev-secret-key-change-me"


def parse_tags(raw: str) -> list[str]:
    raw = (raw or "").strip()
    if not raw:
        return []
    sep = ";" if ";" in raw else ","
    return [t.strip() for t in raw.split(sep) if t.strip()]


def default_profile() -> dict[str, str]:
    """默认个人资料，用于还没有配置文件时。"""
    return {
        "display_name": "你好，我是 关",
        "avatar_text": "G",
        "intro_lead": "喜欢豚鼠 / 写日记用",
        "intro_meta": "位于 — 东京 · 喜欢睡觉、大嘴吉与豚鼠",
        "email": "1515046922@qq.com",
    }


def load_profile() -> dict[str, str]:
    if not PROFILE_PATH.exists():
        return default_profile()
    try:
        data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**default_profile(), **data}
    except Exception:
        pass
    return default_profile()


def save_profile(profile: dict[str, str]) -> None:
    PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )


@app.route("/")
@app.route("/admin/")
def admin_index() -> str:
    """后台首页：列出所有文章，提供新建和编辑入口。"""
    posts = load_posts_json()
    posts_sorted = sorted(posts, key=lambda p: str(p.get("date", "")), reverse=True)
    return render_template("admin_index.html", posts=posts_sorted)


@app.route("/admin/profile", methods=["GET", "POST"])
def admin_profile() -> str:
    """编辑个人资料（名字、简介、头像字母、邮箱等）。"""
    profile = load_profile()
    if request.method == "POST":
        display_name = (request.form.get("display_name") or "").strip() or profile["display_name"]
        avatar_text = (request.form.get("avatar_text") or "").strip() or profile["avatar_text"]
        intro_lead = (request.form.get("intro_lead") or "").strip() or profile["intro_lead"]
        intro_meta = (request.form.get("intro_meta") or "").strip() or profile["intro_meta"]
        email = (request.form.get("email") or "").strip() or profile["email"]

        new_profile = {
            "display_name": display_name,
            "avatar_text": avatar_text,
            "intro_lead": intro_lead,
            "intro_meta": intro_meta,
            "email": email,
        }
        save_profile(new_profile)
        flash("个人资料已保存。", "success")
        return redirect(url_for("admin_profile"))

    return render_template("admin_profile.html", profile=profile)


@app.route("/admin/new", methods=["GET", "POST"])
def admin_new() -> str:
    """创建新文章。"""
    if request.method == "POST":
        title = (request.form.get("title") or "").strip() or "新文章"
        post_id = (request.form.get("post_id") or "").strip() or slugify(title)
        post_date = (request.form.get("date") or "").strip() or date.today().isoformat()
        summary = (request.form.get("summary") or "").strip()
        tags_raw = (request.form.get("tags") or "").strip()
        tags = parse_tags(tags_raw)
        filename = (request.form.get("filename") or "").strip() or f"{post_id}.md"
        content = (request.form.get("content") or "").strip()

        if not content:
            content = f"# {title}\n\n日期：{post_date}\n\n在这里开始写正文内容……\n"

        POSTS_DIR.mkdir(parents=True, exist_ok=True)
        md_path = POSTS_DIR / filename
        md_path.write_text(content, encoding="utf-8")

        posts = load_posts_json()
        new_entry: dict[str, Any] = {
            "id": post_id,
            "title": title,
            "date": post_date,
            "summary": summary,
            "tags": tags,
            "file": filename,
        }

        replaced = False
        for i, p in enumerate(posts):
            if str(p.get("id")) == post_id:
                posts[i] = new_entry
                replaced = True
                break
        if not replaced:
            posts.append(new_entry)

        save_posts_json(posts)
        flash(f"已创建/更新文章：{title}", "success")
        return redirect(url_for("admin_index"))

    today = date.today().isoformat()
    return render_template("admin_form.html", mode="new", today=today, post=None, content="")


@app.route("/admin/edit/<post_id>", methods=["GET", "POST"])
def admin_edit(post_id: str) -> str:
    """编辑已有文章。"""
    posts = load_posts_json()
    post = next((p for p in posts if str(p.get("id")) == post_id), None)
    if post is None:
        flash("未找到该文章", "error")
        return redirect(url_for("admin_index"))

    filename = str(post.get("file"))
    md_path = POSTS_DIR / filename if filename else None

    if request.method == "POST":
        title = (request.form.get("title") or "").strip() or str(post.get("title") or "")
        new_post_id = (request.form.get("post_id") or "").strip() or post_id
        post_date = (request.form.get("date") or "").strip() or str(post.get("date") or "")
        summary = (request.form.get("summary") or "").strip()
        tags_raw = (request.form.get("tags") or "").strip()
        tags = parse_tags(tags_raw)
        filename_form = (request.form.get("filename") or "").strip() or filename
        content = (request.form.get("content") or "").strip()

        if not content and md_path and md_path.exists():
            content = md_path.read_text(encoding="utf-8")

        # 如果修改了文件名，更新路径
        if filename_form != filename:
            new_md_path = POSTS_DIR / filename_form
            if md_path and md_path.exists():
                new_md_path.write_text(content, encoding="utf-8")
                md_path.unlink()
            md_path_local = new_md_path
        else:
            md_path_local = md_path or (POSTS_DIR / filename_form)
            POSTS_DIR.mkdir(parents=True, exist_ok=True)
            md_path_local.write_text(content, encoding="utf-8")

        updated_entry: dict[str, Any] = {
            "id": new_post_id,
            "title": title,
            "date": post_date,
            "summary": summary,
            "tags": tags,
            "file": filename_form,
        }

        for i, p in enumerate(posts):
            if str(p.get("id")) == post_id:
                posts[i] = updated_entry
                break

        save_posts_json(posts)
        flash(f"已保存修改：{title}", "success")
        return redirect(url_for("admin_index"))

    # GET: 读取当前 Markdown 内容
    content = ""
    if md_path and md_path.exists():
        content = md_path.read_text(encoding="utf-8")

    return render_template("admin_form.html", mode="edit", today=None, post=post, content=content)


if __name__ == "__main__":
    # 开发阶段使用 debug=True，方便自动重载
    app.run(debug=True)
