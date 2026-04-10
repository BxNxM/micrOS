/* Editor language plugins: extension registry, checkers, highlighters. */
(function () {
    if (window.EditorPlugins) return;

    const escMap = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    const words = s => new Set(s.split(/\s+/));
    const esc = s => s.replace(/[&<>"']/g, ch => escMap[ch]);
    const span = (cls, s) => `<span class="tok-${cls}">${esc(s)}</span>`;
    const id0 = ch => /[A-Za-z_]/.test(ch);
    const id = ch => /[A-Za-z0-9_]/.test(ch);

    function injectCSS() {
        if (document.getElementById("mp-editor-plugins-css")) return;
        const css = document.createElement("style");
        css.id = "mp-editor-plugins-css";
        css.textContent = `
.mp-editor .tok-keyword { color: #569cd6; }
.mp-editor .tok-builtin { color: #4ec9b0; }
.mp-editor .tok-special { color: #9cdcfe; }
.mp-editor .tok-string { color: #ce9178; }
.mp-editor .tok-comment { color: #6a9955; }
.mp-editor .tok-number { color: #b5cea8; }
.mp-editor .tok-decorator { color: #dcdcaa; }
`;
        document.head.appendChild(css);
    }

    function ext(name) {
        const leaf = (name || "").split(/[?#]/)[0].split("/").pop();
        const dot = leaf.lastIndexOf(".");
        return dot >= 0 ? leaf.slice(dot).toLowerCase() : "";
    }

    function stringStart(src, i) {
        const m = src.slice(i).match(/^([rRuUbBfF]{0,2})(['"]{3}|['"])/);
        if (!m || (m[1] && !/^(?:[rRuUbBfF]|[rR][fFbB]|[fF][rR]|[bB][rR])$/.test(m[1]))) return null;
        return { end: m[2], len: m[0].length };
    }

    function readString(src, i, mark) {
        let j = i + mark.len;
        while (j < src.length) {
            if (src.startsWith(mark.end, j)) return src.slice(i, j + mark.end.length);
            if (mark.end.length === 1 && src[j] === "\n") break;
            j += src[j] === "\\" && j + 1 < src.length ? 2 : 1;
        }
        return src.slice(i, j);
    }

    function highlight(src, scheme) {
        let out = "";
        for (let i = 0; i < src.length;) {
            const ch = src[i];
            const str = stringStart(src, i);
            if (scheme.comment && src.startsWith(scheme.comment, i)) {
                const j = src.indexOf("\n", i);
                const end = j < 0 ? src.length : j;
                out += span("comment", src.slice(i, end));
                i = end;
            } else if (str) {
                const s = readString(src, i, str);
                out += span("string", s);
                i += s.length;
            } else if (scheme.decorators && ch === "@" && id0(src[i + 1] || "")) {
                let j = i + 2;
                while (j < src.length && (id(src[j]) || src[j] === ".")) j++;
                out += span("decorator", src.slice(i, j));
                i = j;
            } else if (/[0-9]/.test(ch)) {
                let j = i + 1;
                while (j < src.length && /[A-Za-z0-9_.]/.test(src[j])) j++;
                out += span("number", src.slice(i, j));
                i = j;
            } else if (id0(ch)) {
                let j = i + 1;
                while (j < src.length && id(src[j])) j++;
                const w = src.slice(i, j);
                out += scheme.keywords.has(w) ? span("keyword", w) :
                    scheme.builtins.has(w) ? span("builtin", w) :
                    scheme.specials.has(w) ? span("special", w) : esc(w);
                i = j;
            } else {
                out += esc(ch);
                i++;
            }
        }
        return out;
    }

    const PY = {
        comment: "#",
        decorators: true,
        keywords: words("False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield"),
        builtins: words("abs all any bool bytes callable chr dict dir enumerate eval Exception filter float getattr hasattr int isinstance len list map max min object open print property range repr reversed round set setattr slice sorted str sum super tuple type zip"),
        specials: words("self cls")
    };

    function codeLines(src) {
        const out = [""];
        for (let i = 0; i < src.length;) {
            const str = stringStart(src, i);
            if (str) {
                const s = readString(src, i, str);
                for (const ch of s) if (ch === "\n") out.push("");
                i += s.length;
            } else if (src[i] === "#") {
                while (i < src.length && src[i] !== "\n") i++;
            } else {
                if (src[i] === "\n") out.push("");
                else out[out.length - 1] += src[i];
                i++;
            }
        }
        return out;
    }

    function checkPython(src) {
        const clean = src.replace(/\t/g, "    ").replace(/\s+$/, "");
        const lines = clean.split("\n");
        const codes = codeLines(clean);
        const blocks = /^(async\s+)?(def|with|class|for|if|elif|else|while|try|except|finally)\b/;
        const indents = [0], errors = [];
        let depth = 0, pending = null;

        const lastCode = i => {
            while (i >= 0) {
                const code = codes[i].trim();
                if (code) return code;
                i--;
            }
            return "";
        };

        lines.forEach((line, i) => {
            const code = codes[i].trim();
            const before = depth;
            for (const ch of code) {
                if ("([{".includes(ch)) depth++;
                else if (")]}".includes(ch)) depth = Math.max(0, depth - 1);
            }
            if (!code) return;

            const n = i + 1;
            const indent = line.match(/^ */)[0].length;
            if (before === 0) {
                let popped = false;
                while (indents.length > 1 && indent < indents[indents.length - 1]) {
                    indents.pop();
                    popped = true;
                }
                if (pending && indent <= pending.indent) {
                    const prev = pending;
                    pending = null;
                    return errors.push({ line: n, error: "indent", prev: prev.text, got: indent, expected: ">" + prev.indent });
                }
                if (indent > indents[indents.length - 1]) {
                    if (!pending) return errors.push({ line: n, error: popped ? "dedent" : "indent", prev: lastCode(i - 1), got: indent, expected: indents[indents.length - 1] });
                    indents.push(indent);
                }
                if (indent !== indents[indents.length - 1]) return errors.push({ line: n, error: "dedent", got: indent, expected: indents[indents.length - 1] });
                pending = null;
            }
            if (blocks.test(code) && !code.includes(":")) {
                errors.push({ line: n, error: "colon", lineText: code });
            } else if (before === 0 && blocks.test(code) && code.endsWith(":")) {
                pending = { line: n, indent, text: code };
            }
        });

        if (pending && !errors.length) errors.push({ line: pending.line, error: "indent", prev: pending.text, got: "EOF", expected: ">" + pending.indent });
        return { ok: errors.length === 0, errors };
    }

    const registry = {
        ".py": {
            checker: checkPython,
            highlighter: src => highlight(src, PY)
        }
    };

    injectCSS();
    window.EditorPlugins = {
        getExt: ext,
        has: name => !!registry[ext(name)],
        getSyntaxFor: name => registry[ext(name)] || null,
        escapeHTML: esc
    };
})();
