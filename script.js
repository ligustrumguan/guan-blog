// script.js — 纯前端博客系统逻辑（文章列表 + 详情页 + 主题切换）

let allPosts = [];

document.addEventListener('DOMContentLoaded', () => {
	initNav();
	initTheme();
	fillYear();

	const page = document.body.dataset.page;
	if (page === 'index') {
		initIndexPage();
	} else if (page === 'post') {
		initPostPage();
	}
});

function initNav(){
	const nav = document.getElementById('nav');
	const toggle = document.getElementById('navToggle');
	if(!nav || !toggle) return;
	toggle.addEventListener('click', ()=>{
		nav.classList.toggle('open');
		const expanded = toggle.getAttribute('aria-expanded') === 'true';
		toggle.setAttribute('aria-expanded', String(!expanded));
	});
}

function initTheme(){
	const root = document.documentElement;
	const btn = document.getElementById('themeToggle');
	const icon = btn ? btn.querySelector('.theme-icon') : null;
	const stored = window.localStorage.getItem('theme');
	const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
	const initial = stored || (prefersDark ? 'dark' : 'light');
	applyTheme(initial, root, icon);

	if(btn){
		btn.addEventListener('click', ()=>{
			const current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
			const next = current === 'dark' ? 'light' : 'dark';
			applyTheme(next, root, icon);
			window.localStorage.setItem('theme', next);
		});
	}
}

function applyTheme(theme, root, icon){
	root.setAttribute('data-theme', theme);
	if(icon){
		icon.textContent = theme === 'dark' ? '🌙' : '☀️';
	}
}

function fillYear(){
	const yearEl = document.getElementById('year');
	if(yearEl) yearEl.textContent = new Date().getFullYear();
}

// 首页逻辑：加载文章列表 + 标签过滤
async function initIndexPage(){
	const postList = document.getElementById('postList');
	if(!postList) return;

	try{
		const res = await fetch('posts/posts.json');
		if(!res.ok) throw new Error('无法加载文章列表');
		const json = await res.json();
		allPosts = Array.isArray(json) ? json.slice() : [];
		// 按日期从新到旧排序
		allPosts.sort((a,b)=> (b.date || '').localeCompare(a.date || ''));
		buildTagFilters(allPosts);
		renderPostList(allPosts);
	}catch(e){
		postList.innerHTML = '<p class="post-excerpt">文章列表加载失败，请检查 posts/posts.json。</p>';
		console.error(e);
	}
}

function buildTagFilters(posts){
	const tagList = document.getElementById('tagList');
	if(!tagList) return;
	const tags = new Set();
	posts.forEach(p=>{
		(p.tags || []).forEach(t=> tags.add(String(t)));
	});
	
	tagList.innerHTML = '';
	tags.forEach(tag=>{
		const btn = document.createElement('button');
		btn.className = 'tag-pill';
		btn.textContent = tag;
		btn.dataset.tag = tag;
		btn.addEventListener('click', ()=>{
			setActiveTag(tag);
		});
		tagList.appendChild(btn);
	});

	const allBtn = document.querySelector('.tag-pill[data-tag="all"]');
	if(allBtn){
		allBtn.addEventListener('click', ()=>{
			setActiveTag('all');
		});
	}
}

function setActiveTag(tag){
	const buttons = document.querySelectorAll('.tag-pill');
	buttons.forEach(b=>{
		if(b.dataset.tag === tag || (tag === 'all' && b.dataset.tag === 'all')){
			b.classList.add('active');
		}else{
			if(tag === 'all' && b.dataset.tag !== 'all'){
				b.classList.remove('active');
			}else if(b.dataset.tag !== 'all'){
				b.classList.toggle('active', b.dataset.tag === tag);
			}else{
				b.classList.remove('active');
			}
		}
	});

	if(!Array.isArray(allPosts) || allPosts.length === 0) return;
	const list = tag === 'all' ? allPosts : allPosts.filter(p => (p.tags || []).includes(tag));
	renderPostList(list);
}

function renderPostList(posts){
	const postList = document.getElementById('postList');
	if(!postList) return;
	postList.innerHTML = '';
	if(!posts.length){
		postList.innerHTML = '<p class="post-excerpt">当前标签下还没有文章。</p>';
		return;
	}
	posts.forEach(p=>{
		const card = document.createElement('article');
		card.className = 'post-card';
		const url = `post.html?id=${encodeURIComponent(p.id)}`;
		const tagsHtml = (p.tags || []).map(t=>`<span class="post-tag">${escapeHtml(t)}</span>`).join('');
		card.innerHTML = `
			<h3><a href="${url}">${escapeHtml(p.title || '')}</a></h3>
			<div class="post-meta">${escapeHtml(p.date || '')}</div>
			<p class="post-excerpt">${escapeHtml(p.summary || '')}</p>
			<div class="post-tags">${tagsHtml}</div>
			<a class="read" href="${url}">阅读全文 →</a>
		`;
		postList.appendChild(card);
	});
}

// 文章详情页逻辑：根据 URL 参数加载对应 Markdown
async function initPostPage(){
	const params = new URLSearchParams(window.location.search);
	const id = params.get('id');
	const titleEl = document.getElementById('postTitle');
	const metaEl = document.getElementById('postMeta');
	const tagsEl = document.getElementById('postTags');
	const contentEl = document.getElementById('postContent');

	if(!id){
		if(titleEl) titleEl.textContent = '未找到文章';
		if(contentEl) contentEl.textContent = '缺少文章 ID 参数。';
		return;
	}

	try{
		const res = await fetch('posts/posts.json');
		if(!res.ok) throw new Error('无法加载文章列表');
		const list = await res.json();
		const post = (Array.isArray(list) ? list : []).find(p=> String(p.id) === id);
		if(!post){
			if(titleEl) titleEl.textContent = '未找到文章';
			if(contentEl) contentEl.textContent = '这篇文章可能已经被删除或 ID 不正确。';
			return;
		}

		if(titleEl) titleEl.textContent = post.title || '';
		if(metaEl) metaEl.textContent = post.date || '';
		if(tagsEl){
			tagsEl.innerHTML = (post.tags || []).map(t=>`<span class="post-tag">${escapeHtml(t)}</span>`).join('');
		}

		const mdRes = await fetch(`posts/${post.file}`);
		if(!mdRes.ok) throw new Error('无法加载 Markdown 文件');
		const md = await mdRes.text();
		const body = stripFrontMatter(md);
		const html = window.marked ? window.marked.parse(body) : escapeHtml(body).replace(/\n/g,'<br />');
		if(contentEl) contentEl.innerHTML = html;
	}catch(e){
		console.error(e);
		if(contentEl) contentEl.textContent = '加载文章时出现错误，请稍后再试。';
	}
}

function stripFrontMatter(md){
	if(md.startsWith('---')){
		const end = md.indexOf('\n---');
		if(end !== -1){
			return md.slice(end + 4);
		}
	}
	return md;
}

function escapeHtml(s){
	return String(s || '').replace(/[&<>"']/g, function(c){
		return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c];
	});
}

