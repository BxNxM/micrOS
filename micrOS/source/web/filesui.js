let selected = null;
let selectedEl = null;              // DOM element of selected file row
let selectedDir = 'user_data';     // fallback
let _editorScriptLoaded = false;
let editorFile = null;             // 🔹 track what's currently opened in editor

// 🔹 Simple root message output
let _msgTimer, _fadeTimer;
function popUpMsg(msg) {
  let el = document.getElementById('root-message');
  if (!el) {
    el = document.createElement('div');
    el.id = 'root-message';
    Object.assign(el.style, {
      position: 'fixed',
      top: '8px',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'rgba(220, 60, 60, 0.9)',     // warm UI red
      color: '#fff',
      padding: '6px 12px',
      borderRadius: '4px',
      fontSize: '12px',
      zIndex: '99999',
      transition: 'opacity 0.4s ease',
      opacity: '0'
    });
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.display = 'block';
  requestAnimationFrame(() => el.style.opacity = '1');
  // Clean timers
  clearTimeout(_msgTimer);
  clearTimeout(_fadeTimer);
  // Start timer
  _msgTimer = setTimeout(() => {
    el.style.opacity = '0';
    _fadeTimer = setTimeout(() => el.style.display = 'none', 400);
  }, 5000);
}

// 🔹 centralized selection clear
function clearSelection() {
  document
    .querySelectorAll('#list .file-item')
    .forEach(x => x.className = 'file-item');

  selected = null;
  selectedEl = null;
}

function load() {
  console.info('load.loadDirs');

  loadDirs().then(() => {
    console.info('load.loadFiles:', selectedDir);
    loadFiles();
  });
  console.info('load.loadDiskUsage');
  updateDiskUsage();
}

function loadFiles() {
  const contentList = document.getElementById('list');

  // 🔹 Enter loading state
  contentList.classList.add('loading');

  fetch('/fs/list', {
    method: 'POST',
    headers: {
      'Content-Type': 'text/plain'
    },
    body: selectedDir || '/'
  })
    .then(r => r.json())
    .then(files => {
      list.innerHTML = '';
      clearSelection();

      files.forEach(f => {
        const name = f.path.split('/').pop();
        const d = document.createElement('div');
        d.className = 'file-item';
        d.textContent = `${name} ${f.size}B`;

        d.onclick = (e) => {
          e.stopPropagation();

          if (selectedEl === d) {
            clearSelection();
            return;
          }

          clearSelection();
          d.className = 'file-item sel';
          selected = name;
          selectedEl = d;
        };

        list.appendChild(d);
      });

      console.info("Files loaded");
    })
    .catch(err => {
      console.error("load failed:", err);
      popUpMsg("Failed to load files: " + err.message);
    })
    .finally(() => {
      // 🔹 Exit loading state (success or error)
      contentList.classList.remove('loading');
    });
}

function loadDirs() {
  return fetch('/fs/dirs')
    .then(r => r.json())
    .then(dirs => {
      const container = document.getElementById('folder-path');
      container.innerHTML = '';

      if (!Array.isArray(dirs) || !dirs.length) return;

      dirs.forEach(dir => {
        const normalized = dir.replace(/^\/+/, '');
        const d = document.createElement('div');
        d.className = 'dir-item';
        d.textContent = normalized;

        d.onclick = () => {
          document
            .querySelectorAll('#folder-path .dir-item')
            .forEach(x => x.className = 'dir-item');

          d.className = 'dir-item sel';
          selectedDir = normalized;
          console.info('dirChange.loadFiles:', selectedDir);
          loadFiles();
        };

        // 🔹 Selection logic
        if (!selectedDir) {
          selectedDir = normalized;
          d.className = 'dir-item sel';
        }
        else if (normalized === selectedDir) {
          d.className = 'dir-item sel';
        }

        container.appendChild(d);
        console.info("Folders loaded");
      });

      // 🔹 Fallback if folder vanished
      if (
        !container.querySelector('.dir-item.sel') &&
        container.firstChild
      ) {
        selectedDir = container.firstChild.textContent;
        container.firstChild.classList.add('sel');
      }
    })
    .catch(err => {
      console.error("dirs load failed:", err);
      popUpMsg("Failed to load folders: " + err.message);
    })
}

function uploadFile() {
  const f = file.files[0];
  if (!f) return;

  const fd = new FormData();
  const targetPath = `${selectedDir}/${f.name}`;
  // This sets filename="selectedDir/file.txt" in multipart
  fd.append('file', f, targetPath);

  console.info("uploadFile:", targetPath);
  fetch('/fs/files', { method: 'POST', body: fd })
    .then(async r => {
      if (!r.ok) {
        const resp = (await r.text()) || r.statusText;
        throw new Error(`${r.status} - ${resp}`);
      }
      return r;
    })
    .then(load)
    .catch(err => {
      console.error("uploadFile error:", err);
      popUpMsg("Upload failed: " + err.message);
    });
}

function openFile() {
  if (!selected) return;
  const resource = `/${selectedDir}/${selected}`;
  console.info('openFile:', resource);
  window.open(resource);
}

function download() {
  if (!selected) return;

  const resource = `/${selectedDir}/${selected}`;
  console.info('download:', resource);

  const a = document.createElement('a');
  a.href = resource;
  a.download = selected;
  a.click();
}

function deleteFile() {
  if (!selected) return;

  const toDelete = `/${selectedDir}/${selected}`;
  console.info("deleteFile:", toDelete);

  fetch('/fs/files', { method: 'DELETE', body: toDelete })
    .then(async r => {
      if (!r.ok) {
        const resp = (await r.text()) || r.statusText;
        throw new Error(`${r.status} - ${resp}`);
      }
      return r;
    })
    .then(() => {
      // 🔹 If the deleted file is open in editor → DESTROY editor
      if (_editorScriptLoaded && editorFile === toDelete) {
        window.destroyEditor?.();
        editorFile = null;
        console.info("deleteFile: editor destroyed");
      }
    })
    .then(load)
    .catch(err => {
      console.error("deleteFile failed:", err);
      popUpMsg("Delete failed: " + err.message);
    });
}

function loadEditorScript() {
  if (_editorScriptLoaded) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = '../editor.js';
    s.onload = () => {
      _editorScriptLoaded = true;
      resolve();
    };
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

async function editor() {
  const filename = selected ?? `LM_blinky.py`;
  const resource = `/${selectedDir}/${filename}`;
  console.info('editor:', resource);

  await loadEditorScript();

  let container = document.getElementById('editor');
  if (!container) {
    container = document.createElement('div');
    container.id = 'editor';
  }

  window.createEditor(container);

  // 🔹 placement delegated to editor.js
  window.openEditor(resource, {
    anchor: selectedEl,
    list: document.getElementById('list')
  });

  editorFile = resource; // 🔹 track currently opened file
}

function updateDiskUsage() {
  fetch('/fs/usage')
    .then(r => r.json())
    .then(data => {
      const usedMB = (data.used / (1024 * 1024)).toFixed(1);
      const freeMB = (data.free / (1024 * 1024)).toFixed(1);
      const total = data.used + data.free;
      const percent = total ? (data.used / total) * 100 : 0;

      document.getElementById('disktext').textContent =
        `Disk: ${usedMB} MB used / ${freeMB} MB free`;

      document.getElementById('diskused').style.width =
        `${percent.toFixed(1)}%`;

      console.info("DiskUsage: update");
    })
    .catch(err => {
      console.error("disk usage failed:", err);
      popUpMsg("Disk usage unavailable: " +  err.message);
    })
}

// 🔹 Global outside-click handler
document.addEventListener('click', (e) => {
  // Ignore toolbar / editor buttons
  if (e.target.closest('button')) return;

  // If editor is open, keep selection locked
  if (_editorScriptLoaded && editorFile) return;

  const list = document.getElementById('list');
  const editor = document.getElementById('editor');

  if (
    list &&
    !list.contains(e.target) &&
    (!editor || !editor.contains(e.target))
  ) {
    clearSelection();
  }
});

load();
