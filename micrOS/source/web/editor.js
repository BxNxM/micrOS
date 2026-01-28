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
    height: 500px;
    overflow: hidden;
}
.mp-editor .lines {
    background: #252526;
    color: #858585;
    padding: 8px;
    text-align: right;
    user-select: none;
    line-height: 20px;
    flex-shrink: 0;
    overflow: hidden;
    white-space: pre;
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
    line-height: 20px;
    overflow: auto;
}
.mp-editor .lines,
.mp-editor input,
.mp-editor textarea {
    font-size: 14px;
}
`;
    document.head.appendChild(css);
}

/* ---------- Syntax registry ---------- */

// 🔹 NEW
const SYNTAX_CHECKERS = {
    ".py": checkPythonSyntax,
    // ".js": checkJSSyntax,
    // ".html": checkHTMLSyntax,
};

// 🔹 NEW
function getCheckerFor(name) {
    const ext = "." + name.split(".").pop().toLowerCase();
    return SYNTAX_CHECKERS[ext] || null;
}

/* ---------- Editor Implementation ---------- */

class EmbeddedEditor {
    constructor(container) {
        this.container = container;
        this.buildUI();
        this.bindEvents();
    }

    buildUI() {
        console.info("editor.js: EmbeddedEditor.buildUI");
        this.container.innerHTML = `
<div class="mp-editor">
    <div class="toolbar">
        <input class="filename" value="">
        <button class="load">Load</button>
        <button class="save">Save</button>
        <button class="syntax">Syntax</button>
        <span class="status info">ready</span>
        <button class="close" title="Close">✕</button>
    </div>
    <div class="editor">
        <div class="lines"></div>
        <textarea class="code" wrap="off"></textarea>
    </div>
</div>`;
        this.codeEl = this.container.querySelector(".code");
        this.linesEl = this.container.querySelector(".lines");
        this.fileEl = this.container.querySelector(".filename");
        this.statusEl = this.container.querySelector(".status");
        this.syntaxBtn = this.container.querySelector(".syntax"); // 🔹 NEW
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
        this.fileEl.addEventListener("input", () => // 🔹 NEW
            this.updateSyntaxAvailability()
        );
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

    updateSyntaxAvailability() { // 🔹 NEW
        this.syntaxBtn.style.display =
            getCheckerFor(this.fileEl.value) ? "" : "none";
    }

    updateLines() {
        const scroll = this.codeEl.scrollTop;
        const count = this.codeEl.value.split("\n").length;
        this.linesEl.textContent =
            Array.from({ length: count }, (_, i) => i + 1).join("\n");
        this.linesEl.scrollTop = scroll;
    }

    /* ---------- File ops ---------- */
    open(url) {
        const name = url?.split("/").pop();
        this.setStatus("loading...");
        fetch(url)
            .then(r => r.ok ? r.text() : Promise.reject())
            .then(t => {
                // 🔹 Success → show file content + path
                this.codeEl.value = t;
                this.fileEl.value = url;
                this.updateLines();
                this.updateSyntaxAvailability();
                this.setStatus("loaded", "ok");
            })
            .catch(() => {
                // 🔹 Failure → special case for LM_blinky.py
                if (name === "LM_blinky.py") {
                    this.fileEl.value = url || ""; // 🔹 show path in input
                    this.loadExample();
                } else {
                    // 🔹 Empty editor, but still show file path
                    this.codeEl.value = "";
                    this.fileEl.value = url || "";
                    this.updateLines();
                    this.updateSyntaxAvailability();
                    this.setStatus("file not found or unreadable", "err");
                }
            });
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

        fetch("/fs/files", { method: "POST", body: fd })
          .then(async r => {
            if (!r.ok) {
              const t = (await r.text()) || r.statusText;
              console.error("editor.js: upload failed:", r.status, r.statusText, t);
              throw new Error(`${r.status} - ${t}`);
            }
            this.setStatus("saved", "ok");
          })
          .catch(err => {
              console.error("editor.js: upload error:", err);
              this.setStatus("Save failed: " + err.message, "err");
          });
    }

    /* ---------- Syntax ---------- */
    syntaxCheck() { // 🔹 MODIFIED
        const checker = getCheckerFor(this.fileEl.value);
        if (!checker) return;

        const r = checker(this.codeEl.value);
        this.setStatus(
            r.ok ? "syntax OK" : Object.entries(r.errors[0]).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(" "),
            r.ok ? "ok" : "err"
        );
    }

    /* ---------- Close ---------- */
    close() {
        this.container.innerHTML = "";
    }

    /* ---------- Example ---------- */

    loadExample() {
      console.info("editor.js: EmbeddedEditor.loadExample");
      this.codeEl.value =
`# LM_blinky.py – MicroPython example
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
      this.updateLines();
      this.updateSyntaxAvailability();
      this.setStatus("example loaded", "info");
    }

}

/* ----------  Syntax checker(s) ---------- */

function checkPythonSyntax(text) {
    const lines = text
        .replace(/\t/g, "    ")
        .replace(/\s+$/, "")
        .split("\n");
    const stack = [0];
    const errors = [];
    const colonRE = /^(async\s+)?(def|with|class)\s+/;
    let depth = 0;
    function lastCodeLine(i) {
        while (i >= 0) {
            const t = lines[i].trim();
            if (t && !t.startsWith("#")) return t;
            i--;
        }
        return "";
    }
    function updateDepth(d, line) {
        for (const c of line.replace(/#.*$/, "")) {
            if ("([{".includes(c)) d++;
            else if (")]}".includes(c)) d = Math.max(0, d - 1);
        }
        return d;
    }
    lines.forEach((line, i) => {
        const n = i + 1;
        const t = line.trim();
        const depthBefore = depth;
        depth = updateDepth(depth, line);
        const topLevel = depthBefore === 0 && depth === 0;
        if (!t || t.startsWith("#")) return;
        const ind = line.match(/^ */)[0].length;
        const cur = stack[stack.length - 1];
        // Indentation check (only at top level)
        if (topLevel) {
            if (ind > cur) {
                const prev = lastCodeLine(i - 1);
                if (!prev.endsWith(":")) {
                    errors.push({ line: n, error: "indent", prev, got: ind, expected: cur });
                    return;
                }
                stack.push(ind);
            }
            while (stack.length > 1 && ind < stack[stack.length - 1]) {
                stack.pop();
            }
            if (ind !== stack[stack.length - 1]) {
                errors.push({ line: n, error: "dedent", got: ind, expected: stack[stack.length - 1] });
                return;
            }
        }
        // Colon check
        if (colonRE.test(t) && !t.endsWith(":")) {
            errors.push({ line: n, error: "colon", lineText: t });
        }
    });
    return { ok: errors.length === 0, errors };
}
