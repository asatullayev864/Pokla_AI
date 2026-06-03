/* ═══════════════════════════════════════════════════════════════
           HalalTracker — Main Application
           ═══════════════════════════════════════════════════════════════ */
        const API = 'http://localhost:8000/api';

        const App = (() => {
            /* ── State ── */
            let state = {
                view: 'list',   // list | cards | countries
                page: 1,
                pageSize: 20,
                totalPages: 1,
                status: '',
                country: '',
                q: '',
                searchTimer: null,
                activeCard: null,     // null | 'active' | 'suspended' | 'withdrawn'
                summary: null,
            };

            /* ── Helpers ── */
            const $ = id => document.getElementById(id);
            const qs = s => document.querySelector(s);

            async function api(path) {
                try {
                    const r = await fetch(API + path);
                    if (!r.ok) throw new Error(r.status);
                    return await r.json();
                } catch { return null; }
            }

            function animNum(el, target) {
                const dur = 1000, start = performance.now();
                const from = parseInt(el.textContent.replace(/\D/g, '')) || 0;
                const tick = now => {
                    const p = Math.min((now - start) / dur, 1);
                    const ease = 1 - Math.pow(1 - p, 3);
                    el.textContent = Math.round(from + (target - from) * ease).toLocaleString();
                    if (p < 1) requestAnimationFrame(tick);
                };
                requestAnimationFrame(tick);
            }

            function statusBadge(s) {
                if (s === 'active') return `<span class="badge b-active">Faol</span>`;
                if (s === 'suspended') return `<span class="badge b-suspended">To'xtatilgan</span>`;
                return `<span class="badge b-withdrawn">Bekor</span>`;
            }

            function statusClass(s) {
                if (s === 'active') return 'b-active';
                if (s === 'suspended') return 'b-suspended';
                return 'b-withdrawn';
            }

            /* ── Summary / stat cards ── */
            async function loadSummary() {
                const d = await api('/countries/summary');
                if (!d) return;
                state.summary = d;
                const total = d.total_certificates || 1;

                animNum($('sv-total'), d.total_certificates);
                animNum($('sv-active'), d.active_certificates);
                animNum($('sv-suspended'), d.suspended_certificates);
                animNum($('sv-withdrawn'), d.withdrawn_certificates);
                animNum($('sv-countries'), d.total_countries);

                setTimeout(() => {
                    $('sf-active').style.width = (d.active_certificates / total * 100) + '%';
                    $('sf-suspended').style.width = (d.suspended_certificates / total * 100) + '%';
                    $('sf-withdrawn').style.width = (d.withdrawn_certificates / total * 100) + '%';
                    $('sh-active').textContent = Math.round(d.active_certificates / total * 100) + '% ulush';
                    $('sh-suspended').textContent = Math.round(d.suspended_certificates / total * 100) + '% ulush';
                    $('sh-withdrawn').textContent = Math.round(d.withdrawn_certificates / total * 100) + '% ulush';
                }, 200);
            }

            async function loadExpiring() {
                const d = await api('/certificates/expiring?days=30');
                if (d && d.length > 0) {
                    $('expiring-bar').style.display = 'flex';
                    $('expiring-txt').textContent = `${d.length} ta sertifikat 30 kun ichida muddati tugaydi!`;
                }
            }

            /* ── Active card highlight ── */
            function highlightCard(key) {
                ['total', 'active', 'suspended', 'withdrawn', 'countries'].forEach(k => {
                    $('sc-' + k).classList.toggle('active', k === key);
                });
                state.activeCard = key;
            }

            /* ── Filter by stat card click ── */
            function filterBy(status) {
                state.status = status || '';
                state.q = '';
                $('q').value = '';
                $('flt-status').value = status || '';
                highlightCard(status || 'total');
                updateFilterBadge(status);
                if (state.view === 'countries') switchView('list');
                load(1);
            }

            function updateFilterBadge(status) {
                const wrap = $('filter-badge-wrap');
                if (!status) { wrap.innerHTML = ''; return; }
                const labels = { active: "Faol", suspended: "To'xtatilgan", withdrawn: "Bekor qilingan" };
                wrap.innerHTML = `<div class="filter-badge">
      🔍 Filtr: <strong>${labels[status]}</strong>
      <button onclick="App.filterBy(null)" title="Tozalash">✕</button>
    </div>`;
            }

            /* ── View switcher ── */
            function switchView(v) {
                state.view = v;
                ['list', 'cards', 'countries'].forEach(name => {
                    $('view-' + name).style.display = name === v ? 'block' : 'none';
                    $('tab-' + name).classList.toggle('on', name === v);
                });
                if (v === 'countries') {
                    highlightCard('countries');
                    loadCountries();
                } else {
                    load(state.page);
                }
            }

            /* ── Main data load ── */
            async function load(page = 1) {
                state.page = page;
                const q = $('q').value.trim();
                const status = $('flt-status').value;
                const country = $('flt-country').value;
                state.status = status;
                state.country = country;
                state.q = q;

                if (state.view === 'list') {
                    $('tbl-body').innerHTML = `<tr><td colspan="6"><div class="state-box"><span class="ico spin">⏳</span></div></td></tr>`;
                    $('tbl-loader').style.display = 'block';
                } else {
                    $('cards-grid').innerHTML = `<div class="state-box" style="grid-column:1/-1"><span class="ico spin">⏳</span></div>`;
                }

                let data, rows;

                if (q.length >= 2) {
                    /* Search endpoint */
                    data = await api(`/search?q=${encodeURIComponent(q)}&limit=50`);
                    rows = data || [];
                    renderTable(rows, null);
                    renderCards(rows);
                    $('tbl-count').textContent = rows.length + ' ta natija';
                    $('pager').style.display = 'none';
                    $('cards-pager').style.display = 'none';
                } else {
                    /* Paginated list */
                    let url = `/certificates?page=${page}&page_size=${state.pageSize}`;
                    if (status) url += `&status=${status}`;
                    if (country) url += `&country=${encodeURIComponent(country)}`;
                    data = await api(url);
                    if (!data) {
                        showError();
                        return;
                    }
                    state.totalPages = data.pages;
                    rows = data.data || [];
                    renderTable(rows, data);
                    renderCards(rows);
                    renderPager(data, 'pager', 'pager-info', 'pager-btns');
                    renderPager(data, 'cards-pager', 'cards-pager-info', 'cards-pager-btns');
                    $('tbl-count').textContent = (data.total || 0).toLocaleString() + ' ta';
                }

                $('tbl-loader').style.display = 'none';
            }

            /* ── Table render ── */
            function renderTable(rows, meta) {
                const tbody = $('tbl-body');
                if (!rows.length) {
                    tbody.innerHTML = `<tr><td colspan="6"><div class="state-box"><span class="ico">📭</span><p>Ma'lumot topilmadi</p></div></td></tr>`;
                    return;
                }
                tbody.innerHTML = rows.map((r, i) => `
      <tr style="animation:slideUp .35s ease ${i * 0.02}s both" onclick="App.openModal('${r.accreditation_number}','${encodeURIComponent(r.country || '')}')">
        <td><span class="acc">${r.accreditation_number || '—'}</span></td>
        <td><div class="org" title="${r.organization_name || ''}">${r.organization_name || '—'}</div></td>
        <td><div class="ctry"><span class="ctry-dot"></span>${r.country || '—'}</div></td>
        <td style="color:var(--text2);font-size:12px">${r.standard || '—'}</td>
        <td>${statusBadge(r.status)}</td>
        <td><span class="date">${r.expiry_date || '—'}</span></td>
      </tr>`).join('');
            }

            /* ── Cards render ── */
            function renderCards(rows) {
                const grid = $('cards-grid');
                if (!rows.length) {
                    grid.innerHTML = `<div class="state-box" style="grid-column:1/-1"><span class="ico">📭</span><p>Ma'lumot topilmadi</p></div>`;
                    return;
                }
                grid.innerHTML = rows.map((r, i) => `
      <div class="ccard" style="animation:slideUp .35s ease ${i * 0.03}s both"
           onclick="App.openModal('${r.accreditation_number}','${encodeURIComponent(r.country || '')}')">
        <div class="ccard-acc">${r.accreditation_number || '—'}</div>
        <div class="ccard-org">${r.organization_name || '—'}</div>
        <div class="ccard-meta">
          ${statusBadge(r.status)}
          <span class="mtag">🌍 ${r.country || '—'}</span>
          ${r.standard ? `<span class="mtag">📋 ${r.standard}</span>` : ''}
          ${r.expiry_date ? `<span class="mtag">📅 ${r.expiry_date}</span>` : ''}
        </div>
      </div>`).join('');
            }

            /* ── Pagination ── */
            function renderPager(meta, panelId, infoId, btnsId) {
                const panel = $(panelId);
                if (!meta || meta.pages <= 1) { panel.style.display = 'none'; return; }
                panel.style.display = 'flex';
                $(infoId).textContent = `${meta.page}-sahifa / ${meta.pages}`;

                let pages = [];
                if (meta.page > 1) pages.push({ l: '‹', p: meta.page - 1 });
                for (let i = Math.max(1, meta.page - 2); i <= Math.min(meta.pages, meta.page + 2); i++) {
                    pages.push({ l: i, p: i, active: i === meta.page });
                }
                if (meta.page < meta.pages) pages.push({ l: '›', p: meta.page + 1 });

                $(btnsId).innerHTML = pages.map(p =>
                    `<button class="pg${p.active ? ' on' : ''}" onclick="App.load(${p.p})">${p.l}</button>`
                ).join('');
            }

            /* ── Countries view ── */
            async function loadCountries() {
                $('ctry-body').innerHTML = `<tr><td colspan="6"><div class="state-box"><span class="ico spin">⏳</span></div></td></tr>`;
                const data = await api('/countries');
                if (!data || !data.length) {
                    $('ctry-body').innerHTML = `<tr><td colspan="6"><div class="state-box"><span class="ico">📭</span><p>Ma'lumot topilmadi</p></div></td></tr>`;
                    return;
                }
                $('ctry-count').textContent = data.length + ' ta';
                const max = Math.max(...data.map(d => d.total_certificates || 0));

                /* Populate country select filter */
                const sel = $('flt-country');
                const existing = new Set(Array.from(sel.options).map(o => o.value));
                data.forEach(d => {
                    if (!existing.has(d.country)) {
                        const o = document.createElement('option');
                        o.value = d.country; o.textContent = d.country;
                        sel.appendChild(o);
                    }
                });

                $('ctry-body').innerHTML = data.map((d, i) => {
                    const pct = max ? Math.round((d.total_certificates || 0) / max * 100) : 0;
                    const color = d.total_certificates > max * .6 ? 'var(--accent)' :
                        d.total_certificates > max * .3 ? 'var(--accent2)' : 'var(--text3)';
                    return `<tr style="animation:slideUp .3s ease ${i * .015}s both;cursor:pointer"
                  onclick="App.filterByCountry('${d.country}')">
        <td><strong>${d.country}</strong></td>
        <td style="font-family:var(--mono);color:${color}">${(d.total_certificates || 0).toLocaleString()}</td>
        <td style="color:var(--success)">${(d.active_certificates || 0).toLocaleString()}</td>
        <td style="color:var(--warn)">${(d.suspended_certificates || 0).toLocaleString()}</td>
        <td style="color:var(--danger)">${(d.withdrawn_certificates || 0).toLocaleString()}</td>
        <td>
          <div class="ctry-bar-wrap">
            <div class="ctry-bar-bg">
              <div class="ctry-bar-fill" style="width:${pct}%;background:${color}"></div>
            </div>
          </div>
        </td>
      </tr>`;
                }).join('');
            }

            function filterByCountry(country) {
                $('flt-country').value = country;
                switchView('list');
                load(1);
            }

            /* ── Expiring shortcut ── */
            function showExpiring() {
                state.status = 'active';
                $('flt-status').value = 'active';
                highlightCard('active');
                updateFilterBadge('active');
                switchView('list');
                load(1);
            }

            /* ── Search debounce ── */
            function onSearch(val) {
                clearTimeout(state.searchTimer);
                state.searchTimer = setTimeout(() => load(1), 380);
            }

            /* ── Error state ── */
            function showError() {
                $('tbl-body').innerHTML = `<tr><td colspan="6"><div class="state-box">
      <span class="ico">⚠️</span>
      <p>API ulanmadi. Server ishlaётganини tekshiring.</p>
    </div></td></tr>`;
                $('tbl-loader').style.display = 'none';
            }

            /* ── Detail Modal ── */
            async function openModal(acc, encodedCountry) {
                const country = decodeURIComponent(encodedCountry);
                $('m-acc').textContent = acc;
                $('m-org').textContent = 'Yuklanmoqda...';
                $('m-body').innerHTML = '';
                $('m-loader').style.display = 'block';
                $('modal-bg').classList.add('show');
                document.body.style.overflow = 'hidden';

                let url = `/certificates/${encodeURIComponent(acc)}`;
                if (country) url += `?country=${encodeURIComponent(country)}`;
                const d = await api(url);
                $('m-loader').style.display = 'none';

                if (!d) {
                    $('m-org').textContent = 'Xatolik yuz berdi';
                    $('m-body').innerHTML = `<div class="state-box"><span class="ico">⚠️</span><p>Ma'lumot topilmadi</p></div>`;
                    return;
                }

                $('m-acc').textContent = d.accreditation_number || acc;
                $('m-org').textContent = d.organization_name || '—';

                const fields = [
                    ['Davlat', d.country],
                    ['Standart', d.standard],
                    ['Manzil', d.address],
                    ['Status', statusBadge(d.status), true],
                    ['Boshlangan', d.initial_date],
                    ['Tugash sanasi', d.expiry_date],
                    ['Scope URL', d.scope_url ? `<a href="${d.scope_url}"   target="_blank">Ko'rish ↗</a>` : '—', true],
                    ['Manba URL', d.source_url ? `<a href="${d.source_url}"  target="_blank">Ko'rish ↗</a>` : '—', true],
                ];

                $('m-body').innerHTML = `
      <div class="info-grid">
        ${fields.map(([label, val, raw]) => `
          <div class="info-item">
            <div class="info-label">${label}</div>
            <div class="info-val">${raw ? val : (val || '—')}</div>
          </div>`).join('')}
      </div>
      ${d.scope_items && d.scope_items.length ? `
        <div class="scope-title">📦 Scope Items (${d.scope_items.length} ta)</div>
        ${d.scope_items.map(s => `
          <div class="scope-item">
            <strong>${s.product_name || s.name || '—'}</strong>
            ${s.description ? `<p>${s.description}</p>` : ''}
          </div>`).join('')}
      ` : ''}`;
            }

            function closeModal(force) {
                if (force === true || force?.target === $('modal-bg')) {
                    $('modal-bg').classList.remove('show');
                    document.body.style.overflow = '';
                }
            }

            /* ── Keyboard ── */
            document.addEventListener('keydown', e => {
                if (e.key === 'Escape') closeModal(true);
            });

            /* ── Init ── */
            async function init() {
                await loadSummary();
                await loadExpiring();
                highlightCard('total');
                load(1);

                /* Load countries for select filter in background */
                const ctryData = await api('/countries');
                if (ctryData) {
                    const sel = $('flt-country');
                    const existing = new Set(Array.from(sel.options).map(o => o.value));
                    ctryData.forEach(d => {
                        if (!existing.has(d.country)) {
                            const o = document.createElement('option');
                            o.value = d.country; o.textContent = d.country;
                            sel.appendChild(o);
                        }
                    });
                }
            }

            init();

            /* ── Public API ── */
            return {
                filterBy, switchView, load, openModal, closeModal,
                onSearch, showExpiring, filterByCountry
            };
        })();