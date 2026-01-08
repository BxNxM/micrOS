let selected = null

function load() {
  fetch('/files')
    .then(r => r.json())
    .then(files => {
      const list = document.getElementById('list')
      list.innerHTML = ''
      selected = null

      files.forEach(f => {
        const name = f.path.split('/').pop()
        const d = document.createElement('div')
        d.textContent = name + '  ' + f.size + 'B'
        d.onclick = () => {
          document.querySelectorAll('#list div').forEach(x => x.className = '')
          d.className = 'sel'
          selected = name
        }
        list.appendChild(d)
      })
    })
}

function upload() {
  const f = file.files[0]
  if (!f) return
  const fd = new FormData()
  fd.append('file', f)
  fetch('/files', { method: 'POST', body: fd }).then(load)
}

function del() {
  if (!selected) return
  fetch('/files', { method: 'DELETE', body: selected }).then(load)
}

function view() {
  if (selected) window.open('/user_data/' + selected)
}

load()
