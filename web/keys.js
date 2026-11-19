// On-screen keys for the jsbeeb iframe (phones, tablets, or
// a mouse). Each button sends the real BBC key: a KeyboardEvent with the host
// key's `code` (jsbeeb maps keys by physical position) is dispatched into the
// same-origin emulator iframe on press and on release.
(() => {
    const iframe = () => document.getElementById("beeb");
    function send(type, code, key) {
        const f = iframe(); const w = f?.contentWindow; const d = f?.contentDocument;
        if (!w || !d) return;
        d.dispatchEvent(new w.KeyboardEvent(type, { code, key, bubbles: true, cancelable: true }));
    }
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    async function tap(code, key, hold = 70) { send("keydown", code, key); await sleep(hold); send("keyup", code, key); await sleep(40); }
    function codeFor(ch) {
        if (/[a-z]/.test(ch)) return ["Key" + ch.toUpperCase(), ch];
        if (/[0-9]/.test(ch)) return ["Digit" + ch, ch];
        return { " ": ["Space", " "], ",": ["Comma", ","], ".": ["Period", "."], "-": ["Minus", "-"], ";": ["Semicolon", ";"] }[ch];
    }
    // buttons: <button data-code="Space" data-key=" ">
    for (const b of document.querySelectorAll("[data-code]")) {
        const down = (e) => { e.preventDefault(); b.classList.add("on"); send("keydown", b.dataset.code, b.dataset.key); b._t = performance.now(); };
        const up = async (e) => {
            e.preventDefault(); if (!b.classList.contains("on")) return;
            const left = 90 - (performance.now() - b._t); if (left > 0) await sleep(left);   // long enough for the OS keyboard scan
            b.classList.remove("on"); send("keyup", b.dataset.code, b.dataset.key);
        };
        b.addEventListener("pointerdown", down); b.addEventListener("pointerup", up);
        b.addEventListener("pointerleave", up); b.addEventListener("pointercancel", up);
        b.addEventListener("contextmenu", (e) => e.preventDefault());
    }
    // no double-tap zoom or long-press menus anywhere on the key pad
    document.addEventListener("dblclick", (e) => { if (e.target.closest(".keys")) e.preventDefault(); }, { passive: false });
})();
