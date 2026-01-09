let selected = null
let web_data_dir = 'user_data'; // fallback

function load() {
  fetch('/files')
    .then(r => r.json())
    .then(files => {
      const list = document.getElementById('list')
      list.innerHTML = ''
      selected = null

      // 🔹 update web_data_dir if files exist
      if (Array.isArray(files) && files.length > 0 && files[0].path) {
        web_data_dir = files[0].path.split('/').slice(0, -1).join('/');
        // remove leading slash
        web_data_dir = web_data_dir.replace(/^\/+/, '');
        document.getElementById('folder-path').textContent = '/' + web_data_dir;
      }

      files.forEach(f => {
        const name = f.path.split('/').pop()
        const d = document.createElement('div')
        d.textContent = name + ' ' + f.size + 'B'
        d.onclick = () => {
          document.querySelectorAll('#list div').forEach(x => x.className = '')
          d.className = 'sel'
          selected = name
        }
        list.appendChild(d)
      })
    })
    console.info("Files loaded")
}

function upload() {
  const f = file.files[0]
  if (!f) return
  const fd = new FormData()
  fd.append('file', f)
  console.info("upload: ", f.name)
  fetch('/files', { method: 'POST', body: fd }).then(load)
}

function del() {
  if (!selected) return
  console.info("delete: ", selected)
  fetch('/files', { method: 'DELETE', body: selected }).then(load)
}

async function view() {
  if (!selected) return;
  let resource = `/${web_data_dir}/${selected}`;
  console.info('view: ', resource);
  window.open(resource);
}

load()
