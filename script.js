(() => {
    const api = 'https://api.github.com/repos/ZFordDev/Glint/releases',
        search = document.querySelector('#releaseSearch'),
        list = document.querySelector('#releaseList'),
        status = document.querySelector('#releaseStatus'),
        filters = [...document.querySelectorAll('.filter')];
    let releases = [],
        platform = 'all';
    const type = n => {
        n = n.toLowerCase();
        if (/\.exe$|\.msi$|windows|win-/.test(n)) return 'windows';
        if (/\.dmg$|\.pkg$|macos|darwin|osx/.test(n)) return 'macos';
        if (/\.appimage$|\.deb$|\.rpm$|\.snap$|linux/.test(n)) return 'linux';
        return 'other'
    };
    const label = n => n.replace(/^Glint[-_]?/i, '').replace(/[-_]/g, ' ').replace(/\.([^.]+)$/, ' .$1');
    const size = b => b ? `${(b/1048576).toFixed(b>=10485760?0:1)} MB` : '';
    const date = v => new Intl.DateTimeFormat(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(v));

    function row(r, assets) {
        const d = document.createElement('details');
        d.className = 'release';
        const s = document.createElement('summary');
        s.innerHTML = `<div><div class="release-title"></div><div class="release-meta">${date(r.published_at||r.created_at)} · ${assets.length} file${assets.length===1?'':'s'}</div></div><span class="release-action">View downloads +</span>`;
        s.querySelector('.release-title').textContent = r.name || r.tag_name;
        d.append(s);
        const box = document.createElement('div');
        box.className = 'assets';
        assets.forEach(a => {
            const link = document.createElement('a');
            link.className = 'asset';
            link.href = a.browser_download_url;
            link.innerHTML = `<span></span><small>${size(a.size)}</small>`;
            link.querySelector('span').textContent = label(a.name);
            box.append(link)
        });
        const notes = document.createElement('a');
        notes.className = 'asset';
        notes.href = r.html_url;
        notes.innerHTML = '<span>Release notes →</span><small></small>';
        box.append(notes);
        d.append(box);
        return d
    }

    function render() {
        const q = search.value.trim().toLowerCase();
        const matches = releases.map(r => ({
            r,
            assets: r.assets.filter(a => (platform === 'all' || type(a.name) === platform) && (!q || `${r.name||''} ${r.tag_name} ${a.name}`.toLowerCase().includes(q)))
        })).filter(x => x.assets.length);
        list.replaceChildren(...matches.map(x => row(x.r, x.assets)));
        const n = matches.reduce((t, x) => t + x.assets.length, 0);
        status.textContent = matches.length ? `${matches.length} release${matches.length===1?'':'s'} · ${n} file${n===1?'':'s'}` : 'No downloads match these filters.'
    }
    filters.forEach(b => b.addEventListener('click', () => {
        platform = b.dataset.platform;
        filters.forEach(x => x.classList.toggle('active', x === b));
        render()
    }));
    search.addEventListener('input', render);
    (async () => {
        try {
            const res = await fetch(`${api}?per_page=100`, {
                headers: {
                    Accept: 'application/vnd.github+json'
                }
            });
            if (!res.ok) throw Error();
            releases = (await res.json()).filter(r => !r.draft).map(r => ({
                ...r,
                assets: r.assets.filter(a => !/\.yml$|\.blockmap$/i.test(a.name))
            })).filter(r => r.assets.length);
            render()
        } catch (e) {
            status.textContent = 'The release archive could not be loaded right now.';
            const a = document.createElement('a');
            a.href = 'https://github.com/ZFordDev/Glint/releases';
            a.textContent = 'Browse GitHub Releases';
            list.append(a)
        }
    })()
})();