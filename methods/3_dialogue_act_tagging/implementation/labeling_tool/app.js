let schema = null;
let rows = [];
let total = 0, labeledCount = 0;
let current = 0;

async function loadSchema() {
  schema = await (await fetch('/tag_schema.json')).json();
}

async function loadRows() {
  const data = await (await fetch('/api/rows')).json();
  rows = data.rows;
  total = data.total;
  labeledCount = data.labeled;
}

function firstUnlabeledIndex(fromIndex) {
  const start = fromIndex === undefined ? 0 : fromIndex;
  for (let i = start; i < rows.length; i++) {
    if (!rows[i].human_label || !rows[i].human_label.trim()) return i;
  }
  for (let i = 0; i < start; i++) {
    if (!rows[i].human_label || !rows[i].human_label.trim()) return i;
  }
  return -1; // all labeled
}

function renderProgress() {
  const pct = total ? Math.round((labeledCount / total) * 100) : 0;
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressLabel').textContent = `${labeledCount} / ${total} labeled`;
  document.getElementById('doneBanner').style.display = (labeledCount >= total && total > 0) ? 'block' : 'none';
}

function renderRow() {
  const row = rows[current];
  document.getElementById('rowNum').textContent = `row ${current + 1} / ${rows.length}`;
  document.getElementById('jumpInput').value = current + 1;
  if (!row) {
    document.getElementById('sentenceCard').textContent = '(no rows)';
    document.getElementById('cellBadge').textContent = '-';
    return;
  }
  document.getElementById('cellBadge').textContent = row.cell_name || `cell ${row.cell}`;
  document.getElementById('sentenceCard').textContent = row.text;
  highlightCurrentTag(row.human_label);
}

function highlightCurrentTag(label) {
  document.querySelectorAll('.tag-btn').forEach(b => {
    b.classList.toggle('current', label && b.dataset.tag === label);
  });
}

function flashCard() {
  const card = document.getElementById('sentenceCard');
  card.classList.remove('flash');
  void card.offsetWidth; // restart animation
  card.classList.add('flash');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => t.classList.remove('show'), 900);
}

async function labelCurrent(tag) {
  if (!rows[current]) return;
  const wasUnlabeled = !rows[current].human_label || !rows[current].human_label.trim();
  const resp = await fetch('/api/label', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index: current, label: tag })
  });
  const data = await resp.json();
  rows[current].human_label = tag;
  labeledCount = data.labeled;
  renderProgress();
  flashCard();
  showToast(`Saved: ${tag}`);
  if (wasUnlabeled) {
    const next = firstUnlabeledIndex(current + 1);
    current = next === -1 ? current : next;
  }
  renderRow();
}

function buildClusters() {
  const container = document.getElementById('clusters');
  container.innerHTML = '';
  schema.clusters.forEach(cluster => {
    const panel = document.createElement('div');
    panel.className = 'cluster-panel';
    panel.style.setProperty('--c-color', cluster.color);
    const h3 = document.createElement('h3');
    h3.textContent = cluster.name;
    const sub = document.createElement('div');
    sub.className = 'subtitle';
    sub.textContent = cluster.subtitle || '';
    const btnWrap = document.createElement('div');
    btnWrap.className = 'tag-buttons';
    cluster.tags.forEach(t => {
      const btn = document.createElement('button');
      btn.className = 'tag-btn' + (cluster.id === 'none' ? ' none-btn' : '');
      btn.dataset.tag = t.tag;
      btn.title = t.gloss;
      btn.textContent = t.tag;
      btn.addEventListener('click', () => labelCurrent(t.tag));
      btnWrap.appendChild(btn);
    });
    panel.appendChild(h3);
    panel.appendChild(sub);
    panel.appendChild(btnWrap);
    container.appendChild(panel);
  });
}

function buildSidebar() {
  const list = document.getElementById('refList');
  list.innerHTML = '';
  schema.clusters.forEach(cluster => {
    const block = document.createElement('div');
    block.className = 'ref-cluster';
    const title = document.createElement('div');
    title.className = 'ref-cluster-title';
    title.style.setProperty('--c-color', cluster.color);
    title.style.color = cluster.color;
    title.textContent = cluster.name;
    block.appendChild(title);
    cluster.tags.forEach(t => {
      const row = document.createElement('div');
      row.className = 'ref-tag';
      row.innerHTML = `<span class="name">${t.tag}</span> <span class="short">- ${t.short}</span>`;
      const detail = document.createElement('div');
      detail.className = 'ref-detail';
      detail.innerHTML = `${t.gloss}` +
        (t.example ? `<div class="ex">${t.example}</div>` : '') +
        (t.watchFor ? `<div class="warn">${t.watchFor}</div>` : '');
      row.addEventListener('click', () => detail.classList.toggle('open'));
      block.appendChild(row);
      block.appendChild(detail);
    });
    list.appendChild(block);
  });
}

function wireNav() {
  document.getElementById('btnPrev').addEventListener('click', () => {
    current = Math.max(0, current - 1);
    renderRow();
  });
  document.getElementById('btnNext').addEventListener('click', () => {
    current = Math.min(rows.length - 1, current + 1);
    renderRow();
  });
  document.getElementById('btnNextUnlabeled').addEventListener('click', () => {
    const next = firstUnlabeledIndex(current + 1);
    if (next !== -1) current = next;
    renderRow();
  });
  document.getElementById('btnJump').addEventListener('click', () => {
    const v = parseInt(document.getElementById('jumpInput').value, 10);
    if (!isNaN(v) && v >= 1 && v <= rows.length) {
      current = v - 1;
      renderRow();
    }
  });
  document.addEventListener('keydown', e => {
    if (document.activeElement.tagName === 'INPUT') return;
    if (e.key === 'ArrowLeft') { current = Math.max(0, current - 1); renderRow(); }
    if (e.key === 'ArrowRight') { current = Math.min(rows.length - 1, current + 1); renderRow(); }
  });
}

async function init() {
  await Promise.all([loadSchema(), loadRows()]);
  buildClusters();
  buildSidebar();
  wireNav();
  current = firstUnlabeledIndex(0);
  if (current === -1) current = 0;
  renderProgress();
  renderRow();
}

init();
