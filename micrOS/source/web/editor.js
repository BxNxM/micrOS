/* ============================================================
 * Embedded MicroPython Editor
 * Self-contained, embeddable, dependency-free
 *
 * Public API:
 *   createEditor(container)
 *   openEditor(url, { anchor, list })
 *   destroyEditor()
 * ============================================================ */

let _editor = null;

// 🔹 track original DOM position of editor container
let _host = {
    container: null,
    parent: null,
    next: null
};

/* ---------- Public API ---------- */

window.createEditor = function (container) {
    console.info("editor.js: createEditor");
    injectCSS();

    if (!_editor) {
        _host.container = container;
        _host.parent = container.parentNode;
        _host.next = container.nextSibling;

        _editor = new EmbeddedEditor(container);
    }
    return _editor;
};

window.openEditor = function (url, opts = {}) {
    if (!_editor) {
        console.warn("Editor not active");
        return;
    }
    console.info("editor.js: openEditor");
    const { anchor, list } = opts;
    const c = _host.container;
    // 🔹 editor owns placement logic
    if (anchor) {
        anchor.insertAdjacentElement("afterend", c);
        console.info("editor.js: openEditor.placed after selected element");
    } else if (list) {
        list.insertAdjacentElement("beforebegin", c);
        console.info("editor.js: openEditor.placed before selected element");
    }

    _editor.open(url);
};

window.destroyEditor = function () {
    if (_editor) {
        _editor.close();
        if (_host.container) {
            _host.container.remove();
            console.info("editor.js: destroyEditor - container removed");
        }
        _editor = null;
        _host.container = null;
        _host.parent = null;
        _host.next = null;
        console.info("editor.js: destroyEditor - editor destroyed");
    }
};

/* ---------- CSS (scoped + injected) ---------- */

function injectCSS() {
    if (document.getElementById("mp-editor-css")) return;

    const css = document.createElement("style");
    css.id = "mp-editor-css";
    css.textContent = `
.mp-editor {
    font-family: monospace;
    background: #1e1e1e;
    color: #d4d4d4;
}
.mp-editor .toolbar {
    background: #252526;
    padding: 6px;
    display: flex;
    gap: 6px;
    align-items: center;
}
.mp-editor input {
    background: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #555;
    padding: 4px 6px;
}
.mp-editor button {
    background: #0e639c;
    border: none;
    color: #fff;
    padding: 6px 10px;
    cursor: pointer;
}
.mp-editor button:hover { background: #1177bb; }
.mp-editor .close {
    margin-left: auto;
    background: transparent;
    color: #ccc;
    font-size: 16px;
    padding: 4px 8px;
}
.mp-editor .close:hover { background: #333; color: #fff; }
.mp-editor .status { font-size: 13px; }
.mp-editor .status.ok   { color: #6a9955; }
.mp-editor .status.err  { color: #f44747; }
.mp-editor .status.info { color: #cccccc; }
.mp-editor .editor {
    display: flex;
    height: 400px;
    overflow-y: auto;
    overflow: auto;
}
.mp-editor .lines {
    background: #252526;
    color: #858585;
    padding: 8px;
    text-align: right;
    user-select: none;
    line-height: 1.4em;
    flex-shrink: 0;
}
.mp-editor textarea {
    flex: 1;
    background: #1e1e1e;
    color: #d4d4d4;
    border: none;
    padding: 8px;
    resize: none;
    outline: none;
    font-family: monospace;
    line-height: 1.4em;
    overflow: visible;
}
`;
    document.head.appendChild(css);
}

/* ---------- Editor Implementation ---------- */

class EmbeddedEditor {
    constructor(container) {
        this.container = container;
        this.buildUI();
        this.bindEvents();
        this.loadExample();
    }

    buildUI() {
        console.info("editor.js: EmbeddedEditor.buildUI");
        this.container.innerHTML = `
<div class="mp-editor">
    <div class="toolbar">
        <input class="filename" value="blinky.py">
        <button class="load">Load</button>
        <button class="save">Save</button>
        <button class="syntax">Syntax</button>
        <span class="status info">ready</span>
        <button class="close" title="Close">✕</button>
    </div>
    <div class="editor">
        <div class="lines"></div>
        <textarea class="code"></textarea>
    </div>
</div>`;
        this.codeEl   = this.container.querySelector(".code");
        this.linesEl  = this.container.querySelector(".lines");
        this.fileEl   = this.container.querySelector(".filename");
        this.statusEl = this.container.querySelector(".status");
    }

    bindEvents() {
        this.codeEl.addEventListener("input", () => {
            this.updateLines();
            this.setStatus("edited");
        });
        this.codeEl.addEventListener("scroll", () =>
            this.linesEl.scrollTop = this.codeEl.scrollTop
        );
        this.codeEl.addEventListener("keydown", e => {
            if (e.key === "Tab") {
                e.preventDefault();
                const s = this.codeEl.selectionStart;
                const ePos = this.codeEl.selectionEnd;
                this.codeEl.value =
                    this.codeEl.value.slice(0, s) +
                    "    " +
                    this.codeEl.value.slice(ePos);
                this.codeEl.selectionStart = this.codeEl.selectionEnd = s + 4;
                this.updateLines();
            }
        });
        this.container.querySelector(".load")
            .addEventListener("click", () => this.loadFile());
        this.container.querySelector(".save")
            .addEventListener("click", () => this.save());
        this.container.querySelector(".syntax")
            .addEventListener("click", () => this.syntaxCheck());
        this.container.querySelector(".close")
            .addEventListener("click", () => window.destroyEditor());
    }

    /* ---------- UI helpers ---------- */
    setStatus(text, type = "info") {
        this.statusEl.textContent = text;
        this.statusEl.className = "status " + type;
    }

    updateLines() {
        const count = this.codeEl.value.split("\n").length + 1;
        this.linesEl.innerHTML =
            Array.from({ length: count }, (_, i) => i + 1).join("<br>");
    }

    /* ---------- File ops ---------- */
    open(url) {
        if (!url) return this.loadExample();

        this.setStatus("loading...");
        fetch(url)
            .then(r => r.ok ? r.text() : Promise.reject())
            .then(t => {
                this.codeEl.value = t;
                this.fileEl.value = url;
                this.updateLines();
                this.setStatus("loaded", "ok");
            })
            .catch(() => this.setStatus("load failed", "err"));
    }

    loadFile() {
        if (!this.fileEl.value)
            return this.setStatus("no filename", "err");
        console.info("editor.js: EmbeddedEditor.loadFile: ", this.fileEl.value);
        this.open(this.fileEl.value);
    }

    save() {
        const name = this.fileEl.value;
        if (!name) {
            this.setStatus("no filename", "err");
            return;
        }

        console.info("editor.js: EmbeddedEditor.save (upload): ", name);
        const blob = new Blob([this.codeEl.value], { type: "text/plain" });
        const file = new File([blob], name);
        const fd = new FormData();
        fd.append("file", file);

        fetch("/files", { method: "POST", body: fd })
            .then(r => {
                if (!r.ok) {
                    return r.text().then(t => {
                        console.error("editor.js: upload failed:", r.status, r.statusText, t);
                        throw new Error("upload failed");
                    });
                }
                this.setStatus("saved", "ok");
            })
            .catch(err => {
                console.error("editor.js: upload error:", err);
                this.setStatus("save failed", "err");
            });
    }

    /* ---------- Syntax ---------- */
    syntaxCheck() {
        const r = checkPythonSyntax(this.codeEl.value);
        this.setStatus(
            r.ok ? "syntax OK" : `error @ line ${r.errors[0].line}`,
            r.ok ? "ok" : "err"
        );
    }

    /* ---------- Example ---------- */
    loadExample() {
        console.info("editor.js: EmbeddedEditor.loadExample");
        this.codeEl.value =
`# blinky.py – MicroPython example
# Guide: https://github.com/BxNxM/micrOS/blob/master/APPLICATION_GUIDE.md
import machine
from microIO import bind_pin, pinmap_search
from Common import micro_task

global LED = None

def load(pin=2):
    global LED
    if LED is None:
        LED = machine.Pin(bind_pin("led", pin), machine.Pin.OUT)
    return LED

@micro_task("blinky", _wrap=True)
def blink(tag):
    with micro_task(tag=tag) as my_task:
        if LED is None:
            my_task.out = "LED uninitialized"
            return
        my_task.out = "BlinkyBlink task"
        while True:
           LED.value(not LED.value())
           await my_task.feed(sleep_ms=500)

def pinmap():
    return pinmap_search(['led'])

def help(widgets=False):
    return "load pin=2", "blink", "pinmap"
`;
        this.fileEl.value = "blinky.py";
        this.updateLines();
        this.setStatus("example loaded", "info");
    }

    /* ---------- Close ---------- */
    close() {
        this.container.innerHTML = "";
    }
}

/* ---------- Pure syntax checker ---------- */

function checkPythonSyntax(text) {
    console.info("editor.js: checkPythonSyntax");
    const lines = text.replace(/\t/g, "    ").split("\n");
    const stack = [0];
    const errors = [];

    lines.forEach((l, i) => {
        const ind = l.match(/^ */)[0].length;
        const t = l.trim();
        const n = i + 1;
        if (!t || t.startsWith("#")) return;

        const cur = stack[stack.length - 1];
        if (ind > cur) {
            const p = lines[i - 1]?.trim() || "";
            if (!p.endsWith(":")) errors.push({ line: n });
            stack.push(ind);
            return;
        }

        while (ind < stack[stack.length - 1]) stack.pop();
        if (ind !== stack[stack.length - 1]) errors.push({ line: n });

        if (/^(if|for|while|def|class|try|except|else|elif|finally)\b/.test(t)
            && !t.endsWith(":")) errors.push({ line: n });
    });

    return { ok: errors.length === 0, errors };
}
