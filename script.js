/* =====================================================
   КОНФИГ
===================================================== */
const CONFIG = {
    githubUsername: 'Kivipups',
    resumeRepo: 'Resume',
    pinnedFirst: ['Resume', 'PracticeSite', 'DocProgram'],
    exclude: [],
    contactEmail: 'upupsi@inbox.ru',

    devCode: [
        ['class', 'c-key'], [' ', ''], ['Developer', 'c-cls'], [':', ''], ['\n', ''],
        ['    def', 'c-key'], [' ', ''], ['__init__', 'c-fn'], ['(', ''], ['self', 'c-arg'], ['):', ''], ['\n', ''],
        ['        self', 'c-arg'], ['.name = ', ''], ['"Кирилл"', 'c-str'], ['\n', ''],
        ['        self', 'c-arg'], ['.nick = ', ''], ['"Kivipups"', 'c-str'], ['\n', ''],
        ['        self', 'c-arg'], ['.role = ', ''], ['"Python Dev"', 'c-str'], ['\n', ''],
        ['        self', 'c-arg'], ['.stack = [', ''], ['"Python"', 'c-str'], [',', ''], ['\n', ''],
        ['                      ', ''], ['"PostgreSQL"', 'c-str'], [',', ''], ['\n', ''],
        ['                      ', ''], ['"OpenCV"', 'c-str'], [',', ''], ['\n', ''],
        ['                      ', ''], ['"Git"', 'c-str'], [']', ''], ['\n\n', ''],
        ['    def', 'c-key'], [' ', ''], ['say_hi', 'c-fn'], ['(', ''], ['self', 'c-arg'], ['):', ''], ['\n', ''],
        ['        return', 'c-key'], [' ', ''], ['"Готов к работе!"', 'c-str'],
    ],

    aiProjects: [
        { name: 'FilterAI', folder: 'FilterAI', description: 'Нейросетевые фильтры для обработки изображений (контраст, ч/б, шум, стилизация). Результаты работы алгоритма — ниже.', tags: ['Python', 'OpenCV', 'AI', 'Image Filter'], script: 'image_filter_ai.py' },
        { name: 'KiviPupsFaceRecognize', folder: 'KiviPupsFaceRecognize', description: 'Распознавание лиц на изображениях с использованием компьютерного зрения и нейросетей.', tags: ['Python', 'CV', 'Face Recognition', 'AI'] },
        { name: 'TextAnalyzer', folder: 'TextAnalyzer', description: 'Анализ и обработка текстовых данных: частотность, ключевые слова, статистика.', tags: ['Python', 'NLP', 'Text'] },
        { name: 'FilterMobileApp', folder: 'FilterMobileApp', description: 'Мобильное приложение с AI-фильтрами для обработки фотографий на устройстве.', tags: ['Mobile', 'AI', 'Filter'] },
        { name: 'Desktop', folder: 'Desktop', description: 'Десктопные приложения: утилиты, интерфейсы и вспомогательные инструменты.', tags: ['Desktop', 'GUI', 'Python'] },
    ],

    projectImages: {},
    languageColors: {
        Python: '#3776ab', JavaScript: '#f1e05a', HTML: '#e34c26', CSS: '#563d7c',
        TypeScript: '#3178c6', Java: '#b07219', 'C++': '#f34b7d', 'C#': '#178600',
        Go: '#00ADD8', Rust: '#dea584', PHP: '#4F5D95', Ruby: '#701516',
        Shell: '#89e051', Kotlin: '#A97BFF', Swift: '#F05138',
    }
};

const GITHUB_API = `https://api.github.com/users/${CONFIG.githubUsername}/repos?sort=updated&per_page=100`;
const container = document.getElementById('projects-container');
const tabsWrap = document.getElementById('project-tabs');

let ALL_REPOS = [];
let ACTIVE_FILTER = 'ai';
const IMAGE_CACHE = new Map();
const AI_FOLDER_CACHE = new Map();

/* =====================================================
   💾 КЭШ (localStorage)
===================================================== */
const CACHE_PREFIX = 'kivi_v1_';
const REPOS_TTL   = 60 * 60 * 1000;       // 1 час
const IMG_TTL     = 24 * 60 * 60 * 1000;  // 24 часа
const FOLDER_TTL  = 24 * 60 * 60 * 1000;  // 24 часа

function cacheGet(key) {
    try {
        const raw = localStorage.getItem(CACHE_PREFIX + key);
        if (!raw) return null;
        return JSON.parse(raw);
    } catch { return null; }
}
function cacheSet(key, value) {
    try {
        localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ t: Date.now(), v: value }));
    } catch {}
}
function cacheFresh(entry, ttl) {
    return entry && (Date.now() - entry.t) < ttl;
}

/* =====================================================
   ⌨️ АНИМАЦИЯ ПЕЧАТАНИЯ КОДА
===================================================== */
function startCodeTyping(el, tokens) {
    if (el.dataset.typed === '1') return;
    el.dataset.typed = '1';
    el.innerHTML = '';

    const cursor = document.createElement('span');
    cursor.className = 'type-cursor';

    const chars = [];
    tokens.forEach(([text, cls]) => {
        for (const ch of text) chars.push({ ch, cls });
    });

    let i = 0;
    let currentSpan = null;
    let currentCls = '__init__';

    function ensureSpan(cls) {
        if (cls === currentCls && currentSpan) return;
        currentCls = cls;
        if (cls) {
            currentSpan = document.createElement('span');
            currentSpan.className = cls;
        } else {
            currentSpan = document.createTextNode('');
        }
        el.appendChild(currentSpan);
    }
    function appendChar(ch, cls) {
        ensureSpan(cls);
        currentSpan.textContent += ch;
        el.appendChild(cursor);
    }
    function tick() {
        if (i >= chars.length) {
            setTimeout(() => cursor.classList.add('hidden'), 3000);
            return;
        }
        const { ch, cls } = chars[i++];
        appendChar(ch, cls);
        let delay = 18;
        if (ch === '\n') delay = 90;
        else if (ch === ' ') delay = 12;
        else if ('.,:()[]{}'.includes(ch)) delay = 30;
        setTimeout(tick, delay);
    }
    setTimeout(tick, 400);
}

function initCodeTyping() {
    const codeEl = document.getElementById('dev-code');
    const windowEl = document.getElementById('code-window');
    if (!codeEl || !windowEl) return;

    if (!('IntersectionObserver' in window)) {
        startCodeTyping(codeEl, CONFIG.devCode);
        return;
    }
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                startCodeTyping(codeEl, CONFIG.devCode);
                io.disconnect();
            }
        });
    }, { threshold: 0.25 });
    io.observe(windowEl);
}

/* =====================================================
   📬 ФОРМА
===================================================== */
function initContactForm() {
    const form = document.getElementById('contact-form');
    const status = document.getElementById('form-status');
    const submitBtn = document.getElementById('form-submit');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            name: form.name.value.trim(),
            email: form.email.value.trim(),
            message: form.message.value.trim(),
        };

        let hasError = false;
        ['name', 'email', 'message'].forEach(key => {
            const field = form[key];
            field.classList.remove('error');
            if (!data[key]) { field.classList.add('error'); hasError = true; }
        });
        if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
            form.email.classList.add('error');
            hasError = true;
        }
        if (hasError) {
            setStatus('Заполните все поля аккуратно.', 'error');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.classList.add('is-loading');
        setStatus('Отправляю...', '');

        try {
            const res = await fetch(`https://formsubmit.co/ajax/${CONFIG.contactEmail}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({
                    name: data.name, email: data.email, message: data.message,
                    _subject: `Сообщение с сайта-резюме от ${data.name}`,
                    _template: 'table', _captcha: 'false',
                }),
            });
            if (res.ok) {
                setStatus('✓ Сообщение отправлено! Я отвечу в течение дня.', 'success');
                form.reset();
                submitBtn.disabled = false;
                submitBtn.classList.remove('is-loading');
                return;
            }
            throw new Error('FormSubmit status ' + res.status);
        } catch (err) {
            console.warn('FormSubmit не сработал, открываю mailto:', err);
        }

        const subject = encodeURIComponent(`Сообщение с сайта от ${data.name}`);
        const body = encodeURIComponent(`Имя: ${data.name}\nEmail: ${data.email}\n\n${data.message}`);
        window.location.href = `mailto:${CONFIG.contactEmail}?subject=${subject}&body=${body}`;
        setStatus('Открыл почтовый клиент. Если он не открылся — напишите мне на ' + CONFIG.contactEmail, '');
        submitBtn.disabled = false;
        submitBtn.classList.remove('is-loading');
    });

    form.querySelectorAll('input, textarea').forEach(field => {
        field.addEventListener('input', () => field.classList.remove('error'));
    });

    function setStatus(text, type) {
        status.textContent = text;
        status.classList.remove('success', 'error');
        if (type) status.classList.add(type);
    }
}

/* =====================================================
   🖱️ КЛИК ПО ПЛИТКЕ
===================================================== */
function initCardClick() {
    container.addEventListener('click', (e) => {
        if (e.target.closest('a, button, .ai-thumbs__item')) return;
        const card = e.target.closest('.project-card');
        if (!card) return;
        const href = card.dataset.href;
        if (href) window.open(href, '_blank', 'noopener');
    });
}

/* =====================================================
   GITHUB API (с кэшем)
===================================================== */

/* Картинка-превью проекта (из README или og:image) — с кэшем */
async function fetchRepoImage(repoName) {
    if (IMAGE_CACHE.has(repoName)) return IMAGE_CACHE.get(repoName);
    if (CONFIG.projectImages[repoName]) {
        IMAGE_CACHE.set(repoName, CONFIG.projectImages[repoName]);
        return CONFIG.projectImages[repoName];
    }

    const key = 'img_' + repoName;
    const cached = cacheGet(key);
    if (cacheFresh(cached, IMG_TTL)) {
        IMAGE_CACHE.set(repoName, cached.v);
        return cached.v;
    }

    const fallback = `https://opengraph.githubassets.com/1/${CONFIG.githubUsername}/${repoName}`;

    try {
        const res = await fetch(`https://api.github.com/repos/${CONFIG.githubUsername}/${repoName}/readme`);
        if (res.ok) {
            const data = await res.json();
            const content = atob(data.content.replace(/\s/g, ''));
            let m = content.match(/!\[[^\]]*\]\(\s*(https?:\/\/[^\s)]+)\s*\)/);
            if (!m) m = content.match(/<img[^>]+src=["'](https?:\/\/[^"']+)["']/);
            if (m) {
                IMAGE_CACHE.set(repoName, m[1]);
                cacheSet(key, m[1]);
                return m[1];
            }
        }
    } catch { /* ignore */ }

    IMAGE_CACHE.set(repoName, fallback);
    return fallback;
}

/* Картинки из папки AI-проекта — с кэшем */
async function fetchFolderImages(folder) {
    if (AI_FOLDER_CACHE.has(folder)) return AI_FOLDER_CACHE.get(folder);

    const key = 'folder_' + folder;
    const cached = cacheGet(key);
    if (cacheFresh(cached, FOLDER_TTL)) {
        AI_FOLDER_CACHE.set(folder, cached.v);
        return cached.v;
    }

    try {
        const res = await fetch(`https://api.github.com/repos/${CONFIG.githubUsername}/${CONFIG.resumeRepo}/contents/${folder}`);
        if (res.ok) {
            const files = await res.json();
            const images = files
                .filter(f => f.type === 'file' && /\.(png|jpe?g|gif|webp|bmp)$/i.test(f.name))
                .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }))
                .map(f => ({ name: f.name, url: f.download_url, path: f.path }));
            AI_FOLDER_CACHE.set(folder, images);
            cacheSet(key, images);
            return images;
        }
    } catch { /* ignore */ }

    // сеть упала — используем устаревший кэш, если есть
    if (cached) {
        AI_FOLDER_CACHE.set(folder, cached.v);
        return cached.v;
    }
    AI_FOLDER_CACHE.set(folder, []);
    return [];
}

function sortRepos(repos) {
    return repos
        .filter(r => !r.fork && !CONFIG.exclude.includes(r.name))
        .sort((a, b) => {
            const aP = CONFIG.pinnedFirst.indexOf(a.name);
            const bP = CONFIG.pinnedFirst.indexOf(b.name);
            if (aP !== -1 && bP !== -1) return aP - bP;
            if (aP !== -1) return -1;
            if (bP !== -1) return 1;
            if (b.stargazers_count !== a.stargazers_count)
                return b.stargazers_count - a.stargazers_count;
            return new Date(b.updated_at) - new Date(a.updated_at);
        });
}

async function loadProjects() {
    const cacheKey = 'repos';
    const cached = cacheGet(cacheKey);

    // 1. Свежий кэш — рендерим сразу, без сетевых запросов
    if (cacheFresh(cached, REPOS_TTL)) {
        ALL_REPOS = sortRepos(cached.v);
        updateCounters();
        renderAIProjects();
        return;
    }

    // 2. Пробуем API
    try {
        const res = await fetch(GITHUB_API);
        if (!res.ok) throw new Error('GitHub API ' + res.status);
        const repos = await res.json();
        cacheSet(cacheKey, repos);
        ALL_REPOS = sortRepos(repos);
        updateCounters();
        renderAIProjects();
    } catch (err) {
        console.error('Ошибка загрузки проектов:', err);
        // 3. Устаревший кэш — тоже сгодится
        if (cached) {
            ALL_REPOS = sortRepos(cached.v);
            updateCounters();
            renderAIProjects();
            return;
        }
        // 4. Совсем ничего нет — показываем заглушку
        container.innerHTML = `
            <div class="empty-state">
                <p>Не удалось загрузить проекты с GitHub.<br><br>
                Посмотрите их напрямую в моём
                <a href="https://github.com/${CONFIG.githubUsername}" target="_blank" rel="noopener" style="color:var(--accent)">профиле →</a></p>
            </div>`;
    }
}

function updateCounters() {
    const counts = { all: ALL_REPOS.length, ai: CONFIG.aiProjects.length, Python: 0, JavaScript: 0, HTML: 0, CSS: 0, other: 0 };
    ALL_REPOS.forEach(r => {
        if (counts[r.language] !== undefined && r.language !== 'ai') counts[r.language]++;
        else if (r.language !== 'ai') counts.other++;
    });
    Object.entries(counts).forEach(([k, v]) => {
        const el = document.getElementById('count-' + k);
        if (el) el.textContent = v;
    });
}

/* =====================================================
   РЕНДЕР
===================================================== */
function renderProjects(repos) {
    if (!repos.length) {
        container.innerHTML = `<div class="empty-state"><p>В этой категории пока нет проектов.</p></div>`;
        return;
    }
    container.innerHTML = '';
    repos.forEach((repo, i) => {
        const card = document.createElement('article');
        card.className = 'project-card';
        card.style.animationDelay = (i * 0.08) + 's';
        card.dataset.href = repo.html_url;
        card.title = 'Открыть ' + repo.name + ' на GitHub';

        const langColor = CONFIG.languageColors[repo.language] || 'var(--accent)';
        const stars = repo.stargazers_count ? `<span class="project-card__stars">★ ${repo.stargazers_count}</span>` : '';
        const homepageLink = repo.homepage ? `<a href="${repo.homepage}" target="_blank" rel="noopener" title="Живая демо">🌐</a>` : '';
        // Показываем сразу fallback-картинку (og:image, без API), потом лениво подменим на картинку из README
        const fallback = `https://opengraph.githubassets.com/1/${CONFIG.githubUsername}/${repo.name}`;
        const imgSrc = IMAGE_CACHE.get(repo.name) || fallback;

        card.innerHTML = `
            <div class="project-card__image">
                <img src="${imgSrc}" alt="Превью проекта ${repo.name}" loading="lazy"
                     onerror="this.onerror=null;this.src='https://opengraph.githubassets.com/1/${CONFIG.githubUsername}/${repo.name}'">
            </div>
            <div class="project-card__body">
                <div class="project-card__head">
                    <span class="project-card__icon">📁</span>
                    <div class="project-card__links">
                        <a href="${repo.html_url}" target="_blank" rel="noopener" title="Открыть на GitHub">↗</a>
                        ${homepageLink}
                    </div>
                </div>
                <h3>${repo.name}</h3>
                <p>${repo.description || 'Описание пока не добавлено.'}</p>
                <div class="project-card__footer">
                    <span class="project-card__lang" style="--lang-color:${langColor}">${repo.language || 'Прочее'}</span>
                    ${stars}
                </div>
            </div>
        `;

        const img = card.querySelector('img');
        img.addEventListener('load', () => img.classList.add('loaded'));
        if (img.complete) img.classList.add('loaded');

        // Лениво подтягиваем «настоящую» картинку из README (только 1 запрос, закэшируется на сутки)
        if (!IMAGE_CACHE.has(repo.name)) {
            fetchRepoImage(repo.name).then(realSrc => {
                if (!realSrc || realSrc === fallback) return;
                const temp = new Image();
                temp.onload = () => { img.src = realSrc; };
                temp.src = realSrc;
            });
        }

        container.appendChild(card);
    });
}

async function renderAIProjects() {
    container.innerHTML = '';

    // параллельно тянем картинки из папок (первый раз — с API, дальше — из кэша)
    const data = await Promise.all(CONFIG.aiProjects.map(async (project, i) => {
        const images = await fetchFolderImages(project.folder);
        return { project, images, i };
    }));

    data.forEach(({ project, images, i }) => {
        const hasImages = images.length > 0;
        const folderUrl = `https://github.com/${CONFIG.githubUsername}/${CONFIG.resumeRepo}/tree/main/${project.folder}`;

        const card = document.createElement('article');
        card.className = 'project-card project-card--ai';
        card.style.animationDelay = (i * 0.1) + 's';
        card.dataset.href = folderUrl;
        card.title = 'Открыть ' + project.name + ' на GitHub';

        const imageBlock = hasImages
            ? `<div class="project-card__image">
                   <span class="ai-badge">🤖 AI</span>
                   <img class="ai-main-img" src="${images[0].url}" alt="${project.name}" loading="lazy">
               </div>`
            : `<div class="project-card__image project-card__image--placeholder">
                   <span class="ai-badge">🤖 AI</span>
                   <div class="ai-placeholder"><span>🧠</span><p>Исходники в репозитории</p></div>
               </div>`;

        const thumbsHTML = hasImages && images.length > 1
            ? `<div class="ai-thumbs">
                   ${images.map((img, idx) => `
                       <button class="ai-thumbs__item ${idx === 0 ? 'active' : ''}"
                               type="button" data-src="${img.url}" title="${img.name}">
                           <img src="${img.url}" alt="${img.name}" loading="lazy">
                       </button>`).join('')}
               </div>` : '';

        const tagsHTML = `<div class="ai-tags">${project.tags.map(t => `<span>${t}</span>`).join('')}</div>`;
        const scriptName = project.script || 'AI Project';
        const imgCount = hasImages ? `${images.length} img` : '—';

        card.innerHTML = `
            ${imageBlock}
            ${thumbsHTML}
            <div class="project-card__body">
                <div class="project-card__head">
                    <span class="project-card__icon">🧠</span>
                    <div class="project-card__links">
                        <a href="${folderUrl}" target="_blank" rel="noopener" title="Открыть папку на GitHub">↗</a>
                    </div>
                </div>
                <h3>${project.name}</h3>
                <p>${project.description}</p>
                ${tagsHTML}
                <div class="project-card__footer" style="margin-top:auto">
                    <span class="project-card__lang" style="--lang-color:var(--accent-2)">${scriptName}</span>
                    <span style="opacity:0.7">${imgCount}</span>
                </div>
            </div>
        `;

        const mainImageEl = card.querySelector('.ai-main-img');
        if (mainImageEl) {
            mainImageEl.addEventListener('load', () => mainImageEl.classList.add('loaded'));
            if (mainImageEl.complete) mainImageEl.classList.add('loaded');
        }

        card.querySelectorAll('.ai-thumbs__item').forEach(btn => {
            btn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                const newSrc = btn.dataset.src;
                if (!newSrc || !mainImageEl) return;
                mainImageEl.classList.remove('loaded');
                const temp = new Image();
                temp.onload = () => { mainImageEl.src = newSrc; mainImageEl.classList.add('loaded'); };
                temp.src = newSrc;
                card.querySelectorAll('.ai-thumbs__item').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        container.appendChild(card);
    });
}

/* =====================================================
   ФИЛЬТРАЦИЯ
===================================================== */
function initTabs() {
    tabsWrap.addEventListener('click', (e) => {
        const tab = e.target.closest('.tab');
        if (!tab) return;
        tabsWrap.querySelectorAll('.tab').forEach(t => t.classList.remove('tab--active'));
        tab.classList.add('tab--active');
        ACTIVE_FILTER = tab.dataset.filter;
        applyFilter();
    });
}

function applyFilter() {
    if (ACTIVE_FILTER === 'all') return renderProjects(ALL_REPOS);
    if (ACTIVE_FILTER === 'ai') return renderAIProjects();
    if (ACTIVE_FILTER === 'other') {
        const known = ['Python', 'JavaScript', 'HTML', 'CSS'];
        return renderProjects(ALL_REPOS.filter(r => !known.includes(r.language)));
    }
    renderProjects(ALL_REPOS.filter(r => r.language === ACTIVE_FILTER));
}

/* =====================================================
   ТЕМА / REVEAL / БУРГЕР / СКРОЛЛ / ВРЕМЯ
===================================================== */
function initTheme() {
    const btn = document.getElementById('theme-toggle');
    const icon = btn.querySelector('.theme-toggle__icon');
    const root = document.documentElement;

    const saved = localStorage.getItem('theme');
    const prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
    applyTheme(saved || (prefersLight ? 'light' : 'dark'));

    btn.addEventListener('click', () => {
        const current = root.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });

    function applyTheme(theme) {
        root.setAttribute('data-theme', theme);
        icon.textContent = theme === 'light' ? '☀️' : '🌙';
        localStorage.setItem('theme', theme);
    }
}

function initReveal() {
    const els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) {
        els.forEach(el => el.classList.add('is-visible'));
        return;
    }
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const parent = entry.target.parentElement;
                const siblings = parent ? Array.from(parent.querySelectorAll('.reveal')) : [];
                const idx = siblings.indexOf(entry.target);
                entry.target.style.transitionDelay = (Math.max(0, idx) * 0.08) + 's';
                entry.target.classList.add('is-visible');
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    els.forEach(el => io.observe(el));
}

function initBurger() {
    const burger = document.getElementById('burger');
    const navList = document.querySelector('.nav__list');
    burger.addEventListener('click', () => {
        burger.classList.toggle('active');
        navList.classList.toggle('active');
    });
    navList.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            burger.classList.remove('active');
            navList.classList.remove('active');
        });
    });
}

function initHeaderScroll() {
    const header = document.querySelector('.header');
    window.addEventListener('scroll', () => {
        header.classList.toggle('scrolled', window.scrollY > 20);
    }, { passive: true });
}

function initLocalTime() {
    const el = document.getElementById('local-time');
    if (!el) return;
    function tick() {
        const now = new Date();
        const utc3 = new Date(now.getTime() + (now.getTimezoneOffset() * 60000) + (3 * 3600000));
        const hh = String(utc3.getHours()).padStart(2, '0');
        const mm = String(utc3.getMinutes()).padStart(2, '0');
        el.textContent = `${hh}:${mm} (UTC +03:00)`;
    }
    tick();
    setInterval(tick, 30000);
}

function initYear() {
    document.getElementById('year').textContent = new Date().getFullYear();
}

/* =====================================================
   ЗАПУСК
===================================================== */
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initBurger();
    initHeaderScroll();
    initYear();
    initLocalTime();
    initTabs();
    initCardClick();
    initReveal();
    initCodeTyping();
    initContactForm();
    loadProjects();
});
