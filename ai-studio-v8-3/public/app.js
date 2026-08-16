const state = {
  rows: [],
  filtered: [],
  selectedIndex: -1,
  referenceImages: [],
  stopRequested: false,
  localStatus: new Map(),
};

const $ = (id) => document.getElementById(id);

async function checkHealth() {
  try {
    const r = await fetch('/api/health');
    const data = await r.json();
    $('health').textContent = data.apiKeyConfigured ? `Gemini ready • ${data.model}` : 'Gemini key missing';
    $('health').classList.toggle('bad', !data.apiKeyConfigured);
  } catch {
    $('health').textContent = 'Server unavailable';
    $('health').classList.add('bad');
  }
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[ch]));
}

function renderQueue() {
  const term = $('filter').value.trim().toLowerCase();
  state.filtered = state.rows.filter((row) => {
    const hay = `${row['Card ID'] || ''} ${row.Subject || ''}`.toLowerCase();
    return !term || hay.includes(term);
  });

  $('queue').innerHTML = state.filtered.map((row, idx) => {
    const blocked = (row._validation || []).length > 0;
    const local = state.localStatus.get(row['Card ID']) || '';
    return `<button class="queue-row ${blocked ? 'blocked' : ''} ${local.toLowerCase()}" data-index="${idx}">
      <span class="qid">${escapeHtml(row['Card ID'])}</span>
      <span class="qsubject">${escapeHtml(row.Subject)}</span>
      <span class="qstatus">${blocked ? `BLOCKED: ${escapeHtml(row._validation.join('; '))}` : (local || 'READY')}</span>
    </button>`;
  }).join('');

  document.querySelectorAll('.queue-row').forEach((el) => {
    el.addEventListener('click', () => {
      state.selectedIndex = Number(el.dataset.index);
      document.querySelectorAll('.queue-row').forEach(x => x.classList.remove('selected'));
      el.classList.add('selected');
      const row = state.filtered[state.selectedIndex];
      $('generateSelected').disabled = !row || row._validation?.length > 0;
    });
  });

  $('runBatch').disabled = state.rows.length === 0;
}

async function parseCsvText(csv) {
  const r = await fetch('/api/parse-csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ csv })
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || 'CSV parse failed');
  state.rows = data.rows;
  state.selectedIndex = -1;
  $('summary').textContent = `${data.count} rows loaded • ${data.valid} pass V8.3 structural validation • ${data.count - data.valid} blocked`;
  renderQueue();
}

$('csvFile').addEventListener('change', async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    await parseCsvText(await file.text());
  } catch (error) {
    $('summary').textContent = error.message;
  }
});

$('filter').addEventListener('input', renderQueue);

$('referenceFiles').addEventListener('change', async (event) => {
  const files = [...(event.target.files || [])].slice(0, 10);
  state.referenceImages = await Promise.all(files.map(fileToDataUrl));
  $('referenceThumbs').innerHTML = state.referenceImages.map(src => `<img src="${src}" alt="reference" />`).join('');
});

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function generateRow(row) {
  if (!row) throw new Error('No card selected');
  if (row._validation?.length) throw new Error(`Blocked: ${row._validation.join('; ')}`);

  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      card: row,
      referenceImages: state.referenceImages,
      model: $('model').value,
      imageSize: $('imageSize').value,
      normalize5x7: $('normalize5x7').checked,
    })
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.validation?.join('; ') || data.error || 'Generation failed');
  showResult(data);
  state.localStatus.set(row['Card ID'], 'GENERATED');
  renderQueue();
  return data;
}

function showResult(data) {
  $('outputEmpty').classList.add('hidden');
  $('output').classList.remove('hidden');
  $('resultImage').src = data.image;
  $('resultMeta').textContent = `${data.cardId} • ${data.subject} • ${data.model}${data.normalized5x7 ? ' • normalized to 5:7' : ''}`;
  $('downloadLink').href = data.image;
  $('downloadLink').download = `${data.cardId}_${String(data.subject).replace(/[^a-z0-9]+/gi, '_')}_V8_3.png`;
  $('output').dataset.cardId = data.cardId;
}

$('generateSelected').addEventListener('click', async () => {
  const row = state.filtered[state.selectedIndex];
  $('generateSelected').disabled = true;
  try {
    await generateRow(row);
  } catch (error) {
    alert(error.message);
    if (row) state.localStatus.set(row['Card ID'], 'FAILED');
    renderQueue();
  } finally {
    $('generateSelected').disabled = false;
  }
});

$('runBatch').addEventListener('click', async () => {
  state.stopRequested = false;
  $('runBatch').disabled = true;
  $('stopBatch').disabled = false;
  try {
    for (const row of state.filtered) {
      if (state.stopRequested) break;
      if (row._validation?.length) {
        state.localStatus.set(row['Card ID'], 'BLOCKED');
        renderQueue();
        alert(`Batch stopped at ${row['Card ID']}: ${row._validation.join('; ')}`);
        break;
      }
      try {
        await generateRow(row);
      } catch (error) {
        state.localStatus.set(row['Card ID'], 'FAILED');
        renderQueue();
        alert(`Batch stopped at ${row['Card ID']}: ${error.message}`);
        break;
      }
    }
  } finally {
    $('runBatch').disabled = false;
    $('stopBatch').disabled = true;
    // Re-evaluate the generate button state based on current selection
    const row = state.filtered[state.selectedIndex];
    $('generateSelected').disabled = !row || row._validation?.length > 0;
  }
});

$('stopBatch').addEventListener('click', () => {
  state.stopRequested = true;
});

$('markApproved').addEventListener('click', () => {
  const id = $('output').dataset.cardId;
  if (!id) return;
  state.localStatus.set(id, 'APPROVED');
  renderQueue();
});

$('markFailed').addEventListener('click', () => {
  const id = $('output').dataset.cardId;
  if (!id) return;
  state.localStatus.set(id, 'FAILED');
  renderQueue();
});

checkHealth();
