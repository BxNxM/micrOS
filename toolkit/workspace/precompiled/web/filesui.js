let selected = null;
let selectedEl = null;              // DOM element of selected file row
let web_data_dir = 'user_data';     // fallback
let _editorScriptLoaded = false;
let editorFile = null;             // 🔹 track what's currently opened in editor

function load() {
  fetch('/files')
    .then(r => r.json())
    .then(files => {
      const list = document.getElementById('list');

      list.innerHTML = '';
      selected = null;
      selectedEl = null;

      // update web_data_dir from first file
      if (Array.isArray(files) && files[0]?.path) {
        web_data_dir = files[0].path
          .split('/')
          .slice(0, -1)
          .join('/')
          .replace(/^\/+/, '');
        document.getElementById('folder-path').textContent = '/' + web_data_dir;
      }

      files.forEach(f => {
        const name = f.path.split('/').pop();
        const d = document.createElement('div');
        d.className = 'file-item';                 // ✅ mark as selectable row
        d.textContent = `${name} ${f.size}B`;

        d.onclick = () => {
          // clicking same item toggles selection OFF
          if (selectedEl === d) {
            d.className = 'file-item';
            selected = null;
            selectedEl = null;
            return;
          }

          // only clear selection on file rows (NOT editor internal divs)
          document
            .querySelectorAll('#list .file-item')
            .forEach(x => x.className = 'file-item');

          d.className = 'file-item sel';
          selected = name;
          selectedEl = d;
        };

        list.appendChild(d);
      });

      console.info("Files loaded");
    })
    .catch(err => console.error("load failed:", err));
}

function upload() {
  const f = file.files[0];
  if (!f) return;

  const fd = new FormData();
  fd.append('file', f);

  console.info("upload:", f.name);
  //fetch('/files', { method: 'POST', body: fd }).then(load);

  fetch('/files', { method: 'POST', body: fd })
  .then(r => {
    if (!r.ok) {
      return r.text().then(t => {
        console.error("upload failed:", r.status, r.statusText, t);
        throw new Error("upload failed");
      });
    }
    return r;
  })
  .then(load)
  .catch(err => console.error("upload error:", err));
}

function view() {
  if (!selected) return;
  const resource = `/${web_data_dir}/${selected}`;
  console.info('view:', resource);
  window.open(resource);
}

function download() {
  if (!selected) return;

  const resource = `/${web_data_dir}/${selected}`;
  console.info('download:', resource);

  const a = document.createElement('a');
  a.href = resource;
  a.download = selected;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function del() {
  if (!selected) return;

  const toDelete = selected;
  console.info("delete:", toDelete);

  fetch('/files', { method: 'DELETE', body: toDelete })
    .then(() => {
      // 🔹 If the deleted file is open in editor → DESTROY editor
      if (_editorScriptLoaded && editorFile === toDelete) {
        if (window.destroyEditor) {
          window.destroyEditor();
        }
        editorFile = null;
        console.info("editor: destroyed (file deleted)");
      }
    })
    .then(load)
    .catch(err => console.error("delete failed:", err));
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
  const resource = `/${web_data_dir}/${filename}`;
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

load();
