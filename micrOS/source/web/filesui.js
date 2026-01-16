let selected = null;
let selectedEl = null;              // DOM element of selected file row
let selectedDir = 'user_data';     // fallback
let _editorScriptLoaded = false;
let editorFile = null;             // 🔹 track what's currently opened in editor

// 🔹 centralized selection clear
function clearSelection() {
  document
    .querySelectorAll('#list .file-item')
    .forEach(x => x.className = 'file-item');

  selected = null;
  selectedEl = null;
}

function load() {
  fetch('/fs/files')
    .then(r => r.json())
    .then(files => {
      const list = document.getElementById('list');

      list.innerHTML = '';
      clearSelection();

      files.forEach(f => {
        const name = f.path.split('/').pop();
        const d = document.createElement('div');
        d.className = 'file-item';                 // ✅ mark as selectable row
        d.textContent = `${name} ${f.size}B`;

        d.onclick = (e) => {
          e.stopPropagation(); // 🔹 prevent outside-click handler

          // clicking same item toggles selection OFF
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
    .catch(err => console.error("load failed:", err));

  loadDirs();
  updateDiskUsage();
}

function loadDirs() {
  fetch('/fs/dirs')
    .then(r => r.json())
    .then(dirs => {
      const container = document.getElementById('folder-path');
      container.innerHTML = '';

      if (!Array.isArray(dirs) || !dirs.length) return;

      let first = true;

      dirs.forEach(dir => {
        const d = document.createElement('div');
        d.className = 'dir-item';
        d.textContent = dir;

        d.onclick = () => {
          document
            .querySelectorAll('#folder-path .dir-item')
            .forEach(x => x.className = 'dir-item');

          d.className = 'dir-item sel';
          selectedDir = dir.replace(/^\/+/, '');
        };

        container.appendChild(d);

        // auto-select first dir
        if (first) {
          first = false;
          d.className = 'dir-item sel';
          selectedDir = dir.replace(/^\/+/, '');
        }

        console.info("Folders loaded");
      });
    })
    .catch(err => console.error("dirs load failed:", err));
}

function uploadFile() {
  const f = file.files[0];
  if (!f) return;

  const fd = new FormData();
  fd.append('file', f);

  console.info("uploadFile:", f.name);
  fetch('/fs/files', { method: 'POST', body: fd })
    .then(r => {
      if (!r.ok) {
        return r.text().then(t => {
          console.error("uploadFile failed:", r.status, r.statusText, t);
          throw new Error("uploadFile failed");
        });
      }
    })
    .then(load)
    .catch(err => console.error("uploadFile error:", err));
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

  const toDelete = selected;
  console.info("deleteFile:", toDelete);

  fetch('/fs/files', { method: 'DELETE', body: toDelete })
    .then(() => {
      // 🔹 If the deleted file is open in editor → DESTROY editor
      if (_editorScriptLoaded && editorFile === toDelete) {
        window.destroyEditor?.();
        editorFile = null;
        console.info("deleteFile: editor destroyed");
      }
    })
    .then(load)
    .catch(err => console.error("deleteFile failed:", err));
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
  const filename = selected ?? "blinky.py";
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

  editorFile = filename; // 🔹 track currently opened file
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
    .catch(err => console.error("disk usage failed:", err));
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
