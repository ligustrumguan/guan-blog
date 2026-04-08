# guan-blog

一个使用纯前端 + Markdown 的个人博客系统，页面托管在 GitHub Pages，上线访问地址类似：

- `https://ligustrumguan.github.io/guan-blog/`

## 文章存储结构

- 所有文章以 Markdown 文件的形式存放在 `posts/` 目录下（例如 `posts/post1.md`）。
- `posts/posts.json` 是文章列表的“索引”，前端会从这里读取元数据（id、标题、日期、摘要、标签、对应的 Markdown 文件名）。

前端页面（`index.html` / `post.html` + `style.css` + `script.js`）是纯静态的，可以直接部署在 GitHub Pages。

## 发文方式一：命令行脚本（已存在）

在项目根目录运行：

```bash
python3 new_post.py
```

按照提示输入标题、简介、标签等信息，脚本会自动：

- 在 `posts/` 下生成一篇新的 Markdown 文件；
- 更新 `posts/posts.json`，加入一条新的文章记录。

完成后，用本地静态服务器预览：

```bash
python3 -m http.server 8000
```

浏览器打开 `http://localhost:8000/` 查看效果，再通过 git 提交并推送到 GitHub。

## 发文方式二：Flask 后台（网页管理）

如果你不想每次都在终端里输入，可以启动一个简单的 Flask 后台，在浏览器中直接新建和编辑文章。

### 安装依赖

在项目根目录执行（建议使用 Python 3.10+）：

```bash
pip install -r requirements.txt
```

### 启动后台服务

在项目根目录运行：

```bash
python3 app.py
```

默认会在本地启动一个开发服务器：

- 后台管理地址：`http://127.0.0.1:5000/` 或 `http://localhost:5000/`

> 注意：这个后台目前只适合**本地使用**，默认没有做登录/鉴权，请不要直接暴露在公网环境。

### 后台能做什么？

- 查看现有文章列表；
- 新建文章：填写标题 / id / 日期 / 简介 / 标签 / Markdown 文件名 / 正文内容；
- 编辑文章：
  - 修改上述元信息；
  - 直接在网页上编辑 Markdown 正文并保存。

所有改动都会直接写入本地的 `posts/` 目录和 `posts/posts.json`，因此：

- 你可以在本地预览；
- 然后像平时一样 `git add . && git commit && git push`，就能把更新同步到 GitHub Pages。

## 部署到 GitHub Pages 的注意事项

- 仓库根目录有一个 `.nojekyll` 文件，用来关闭 GitHub Pages 的 Jekyll 处理，这样 `posts/*.md` 能被原样提供，前端才能通过 `fetch` 访问。
- 每次发文或修改后，记得：

```bash
git status
git add .
git commit -m "发布新文章：XXX"
git push
```

等待 GitHub Pages 部署完成（通常几分钟内），然后访问你的博客地址即可看到最新内容。

---

如果以后要把 Flask 后台部署到线上（例如 Render、Railway 等），建议再补充：

- 简单登录保护；
- 对提交内容做更多校验。

当前版本主要面向「本地写作 + GitHub Pages 静态展示」的工作流。
