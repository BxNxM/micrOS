/* ============================================================
 * Embedded MicroPython Editor
 * Dependency-free editor shell; syntax support lives in editor_plugins.js.
 *
 * Public API:
 *   createEditor(container)
 *   openEditor(url, { anchor, list })
 *   destroyEditor()
 * ============================================================ */

let _editor = null;
let _pluginsPromise = null;
const _host = { container: null };
const _editorSrc = (document.currentScript && document.currentScript.src) || "../editor.js";

window.createEditor = function (container) {
    injectCSS();
    if (!_editor) {
        _host.container = container;
        _editor = new EmbeddedEditor(container);
    }
    return _editor;
};

window.openEditor = function (url, opts = {}) {
    if (!_editor) return console.warn("Editor not active");

    const { anchor, list } = opts;
    if (anchor) anchor.insertAdjacentElement("afterend", _host.container);
    else if (list) list.insertAdjacentElement("beforebegin", _host.container);

    _editor.open(url);
};

window.destroyEditor = function () {
    if (!_editor) return;
    _editor.close();
    if (_host.container) _host.container.remove();
    _editor = null;
    _host.container = null;
};

function injectCSS() {
    if (document.getElementById("mp-editor-css")) return;

    const css = document.createElement("style");
    css.id = "mp-editor-css";
    css.textContent = `
.mp-editor {
    --mp-code-font: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    --mp-code-line: 20px;
    --mp-code-pad: 8px;
    --mp-code-size: 14px;
    background: #1e1e1e;
    color: #d4d4d4;
    font-family: var(--mp-code-font);
}
.mp-editor .toolbar {
    align-items: center;
    background: #252526;
    display: flex;
    gap: 6px;
    padding: 6px;
}
.mp-editor input {
    background: #1e1e1e;
    border: 1px solid #555;
    color: #d4d4d4;
    padding: 4px 6px;
}
.mp-editor button {
    background: #0e639c;
    border: none;
    color: #fff;
    cursor: pointer;
    padding: 6px 10px;
}
.mp-editor button:hover { background: #1177bb; }
.mp-editor .close {
    background: transparent;
    color: #ccc;
    font-size: 16px;
    margin-left: auto;
    padding: 4px 8px;
}
.mp-editor .close:hover { background: #333; color: #fff; }
.mp-editor .status { font-size: 13px; }
.mp-editor .status.ok { color: #6a9955; }
.mp-editor .status.err { color: #f44747; }
.mp-editor .status.info { color: #ccc; }
.mp-editor .editor {
    display: flex;
    height: 500px;
    overflow: hidden;
}
.mp-editor .lines {
    background: #252526;
    color: #858585;
    flex-shrink: 0;
    font-family: var(--mp-code-font);
    font-size: var(--mp-code-size);
    line-height: var(--mp-code-line);
    overflow: hidden;
    padding: var(--mp-code-pad);
    text-align: right;
    user-select: none;
    white-space: pre;
}
.mp-editor .code-wrap {
    background: #1e1e1e;
    cursor: text;
    flex: 1;
    overflow: hidden;
    position: relative;
}
.mp-editor .highlight,
.mp-editor textarea {
    appearance: none;
    border: none;
    border-radius: 0;
    box-sizing: border-box;
    display: block;
    font-family: var(--mp-code-font);
    font-size: var(--mp-code-size);
    font-style: normal;
    font-weight: 400;
    height: 100%;
    inset: 0;
    letter-spacing: 0;
    line-height: var(--mp-code-line);
    margin: 0;
    max-width: none;
    overflow-wrap: normal;
    padding: var(--mp-code-pad);
    position: absolute;
    tab-size: 4;
    white-space: pre;
    width: 100%;
    word-break: normal;
    word-wrap: normal;
}
.mp-editor .highlight {
    background: transparent;
    color: #d4d4d4;
    overflow: visible;
    pointer-events: none;
    z-index: 1;
}
.mp-editor textarea {
    background: transparent;
    caret-color: #d4d4d4;
    color: transparent;
    outline: none;
    overflow: auto;
    resize: none;
    -webkit-text-fill-color: transparent;
    z-index: 2;
}
.mp-editor textarea::selection {
    background: rgba(38, 79, 120, 0.65);
    color: transparent;
    -webkit-text-fill-color: transparent;
}
.mp-editor .lines,
.mp-editor input {
    font-size: 14px;
    line-height: 20px;
}
`;
    document.head.appendChild(css);
}

/* ---------- Plugin bridge ---------- */

function escapeHTML(text) {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return text.replace(/[&<>"']/g, ch => map[ch]);
}

function fileExt(name) {
    const leaf = (name || "").split(/[?#]/)[0].split("/").pop();
    const dot = leaf.lastIndexOf(".");
    return dot >= 0 ? leaf.slice(dot).toLowerCase() : "";
}

function pluginUrl() {
    const src = _editorSrc.replace(/editor\.js([?#].*)?$/, "editor_plugins.js$1");
    return src === _editorSrc ? "../editor_plugins.js" : src;
}

function plugins() {
    return window.EditorPlugins || null;
}

function syntaxFor(name) {
    const api = plugins();
    return api && api.getSyntaxFor ? api.getSyntaxFor(name) : null;
}

function loadPlugins() {
    if (plugins()) return Promise.resolve(plugins());
    if (_pluginsPromise) return _pluginsPromise;

    _pluginsPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = pluginUrl();
        script.onload = () => {
            const api = plugins();
            api ? resolve(api) : reject(new Error("editor_plugins.js did not register EditorPlugins"));
        };
        script.onerror = () => reject(new Error("editor_plugins.js load failed"));
        document.head.appendChild(script);
    }).catch(err => {
        _pluginsPromise = null;
        throw err;
    });

    return _pluginsPromise;
}

/* ---------- Editor ---------- */

class EmbeddedEditor {
    constructor(container) {
        this.container = container;
        this.pluginsLoading = false;
        this.buildUI();
        this.bindEvents();
        this.refresh(false);
    }

    buildUI() {
        this.container.innerHTML = `
<div class="mp-editor">
    <div class="toolbar">
        <input class="filename" value="">
        <button class="load">Load</button>
        <button class="save">Save</button>
        <button class="syntax">Syntax</button>
        <span class="status info">ready</span>
        <button class="close" title="Close">&times;</button>
    </div>
    <div class="editor">
        <div class="lines"></div>
        <div class="code-wrap">
            <pre class="highlight" aria-hidden="true"></pre>
            <textarea class="code" wrap="off" spellcheck="false"></textarea>
        </div>
    </div>
</div>`;
        this.codeEl = this.container.querySelector(".code");
        this.fileEl = this.container.querySelector(".filename");
        this.highlightEl = this.container.querySelector(".highlight");
        this.linesEl = this.container.querySelector(".lines");
        this.statusEl = this.container.querySelector(".status");
        this.syntaxBtn = this.container.querySelector(".syntax");
    }

    bindEvents() {
        this.codeEl.addEventListener("input", () => {
            this.refresh();
            this.setStatus("edited");
        });
        this.codeEl.addEventListener("scroll", () => this.syncScroll());
        this.codeEl.addEventListener("keydown", e => this.handleKeydown(e));
        this.fileEl.addEventListener("input", () => this.refresh());
        this.container.querySelector(".load").addEventListener("click", () => this.loadFile());
        this.container.querySelector(".save").addEventListener("click", () => this.save());
        this.syntaxBtn.addEventListener("click", () => this.syntaxCheck());
        this.container.querySelector(".close").addEventListener("click", () => window.destroyEditor());
    }

    handleKeydown(e) {
        if (e.key !== "Tab") return;
        e.preventDefault();
        const s = this.codeEl.selectionStart;
        const ePos = this.codeEl.selectionEnd;
        this.codeEl.value = this.codeEl.value.slice(0, s) + "    " + this.codeEl.value.slice(ePos);
        this.codeEl.selectionStart = this.codeEl.selectionEnd = s + 4;
        this.refresh();
    }

    setStatus(text, type = "info") {
        this.statusEl.textContent = text;
        this.statusEl.className = "status " + type;
    }

    refresh(loadPlugin = true) {
        this.updateLines();
        this.paint();
        const syntax = syntaxFor(this.fileEl.value);
        this.syntaxBtn.style.display = syntax && syntax.checker ? "" : "none";
        if (loadPlugin) this.ensurePlugins();
    }

    paint() {
        const syntax = syntaxFor(this.fileEl.value);
        const highlighter = syntax && syntax.highlighter;
        const code = this.codeEl.value;
        this.highlightEl.innerHTML = (highlighter ? highlighter(code) : escapeHTML(code)) || " ";
        this.syncScroll();
    }

    ensurePlugins() {
        if (plugins() || this.pluginsLoading || !fileExt(this.fileEl.value)) return;

        this.pluginsLoading = true;
        loadPlugins().then(
            () => {
                this.pluginsLoading = false;
                this.refresh(false);
            },
            err => {
                this.pluginsLoading = false;
                console.warn("editor.js:", err.message);
            }
        );
    }

    syncScroll() {
        this.linesEl.scrollTop = this.codeEl.scrollTop;
        this.highlightEl.style.transform = `translate(${-this.codeEl.scrollLeft}px, ${-this.codeEl.scrollTop}px)`;
    }

    updateLines() {
        const count = this.codeEl.value.split("\n").length;
        this.linesEl.textContent = Array.from({ length: count }, (_, i) => i + 1).join("\n");
        this.linesEl.scrollTop = this.codeEl.scrollTop;
    }

    setValue(file, text, status, type = "info") {
        this.fileEl.value = file || "";
        this.codeEl.value = text || "";
        this.refresh();
        this.setStatus(status, type);
    }

    open(url) {
        const name = (url || "").split("/").pop();
        this.setStatus("loading...");
        fetch(url)
            .then(r => r.ok ? r.text() : Promise.reject(new Error(r.statusText || "load failed")))
            .then(text => this.setValue(url, text, "loaded", "ok"))
            .catch(() => {
                if (name === "LM_blinky.py") this.loadExample(url);
                else this.setValue(url, "", "file not found or unreadable", "err");
            });
    }

    loadFile() {
        this.fileEl.value ? this.open(this.fileEl.value) : this.setStatus("no filename", "err");
    }

    save() {
        const name = this.fileEl.value;
        if (!name) return this.setStatus("no filename", "err");
        if (!window.uploadFile) return this.setStatus("upload unavailable", "err");

        const file = new File([this.codeEl.value], name, { type: "text/plain" });
        window.uploadFile(file)
            .then(ok => this.setStatus(ok ? "saved" : "save failed", ok ? "ok" : "err"))
            .catch(err => this.setStatus("Save failed: " + err.message, "err"));
    }

    syntaxCheck() {
        const syntax = syntaxFor(this.fileEl.value);
        const checker = syntax && syntax.checker;
        if (!checker) {
            if (plugins() || !fileExt(this.fileEl.value)) return this.setStatus("syntax unavailable");
            this.setStatus("loading syntax...");
            return loadPlugins().then(() => this.syntaxCheck(), err => this.setStatus(err.message, "err"));
        }

        const result = checker(this.codeEl.value);
        const error = result.errors && result.errors[0];
        this.setStatus(
            result.ok ? "syntax OK" : Object.entries(error || {}).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(" "),
            result.ok ? "ok" : "err"
        );
    }

    close() {
        const file = this.fileEl ? this.fileEl.value : "";
        this.container.innerHTML = "";
        try {
            window.dispatchEvent(new CustomEvent("micros-editor-close", { detail: { file } }));
        } catch (_) {}
    }

    loadExample(file = "") {
        this.setValue(file, `# LM_blinky.py - MicroPython example
# Guide: https://github.com/BxNxM/micrOS/blob/master/micrOS/MODULE_GUIDE.md
import machine
from microIO import bind_pin, pinmap_search
from Common import micro_task

LED = None

def load(pin=2):
    global LED
    if LED is None:
        LED = machine.Pin(bind_pin("led", pin), machine.Pin.OUT)
    return LED

@micro_task("blinky", _wrap=True)
async def blink(tag):
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
`, "example loaded");
    }
}
