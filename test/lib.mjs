// Shared helpers for the headless jsbeeb tests.
import { MachineSession } from "../vendor/jsbeeb/src/machine-session.js";
import { BBC } from "../vendor/jsbeeb/src/keymap.js";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import path from "path";

export const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
export function symbols() {
    const sym = {};
    const ls = readFileSync(path.join(root, "build/listing.txt"), "utf8").split("\n");
    for (let i = 0; i < ls.length - 1; i++) {   // every top-level label: ".name" then its address
        const m = ls[i].match(/^\.([A-Za-z_]\w*)$/), a = ls[i + 1].match(/^\s+([0-9A-F]{4})\b/);
        if (m && a && !(m[1] in sym)) sym[m[1]] = parseInt(a[1], 16);
    }
    for (const l of ls) {
        const m = l.match(/^(?:SYM|VAR) (\w+)\s*&([0-9A-F]+)/); if (m) sym[m[1]] = parseInt(m[2], 16);
    }
    return sym;
}
const CODES = { 0x11: "r", 0x12: "g", 0x13: "y", 0x14: "b", 0x15: "m", 0x16: "c", 0x17: "w", 0x01: "R", 0x02: "G", 0x03: "Y", 0x04: "B", 0x05: "M", 0x06: "C", 0x07: "W", 0x1e: "H", 0x1c: "K", 0x1d: "N", 0x0d: "D", 0x0c: "d" };
export async function beeb(opts = {}) {
    const s = new MachineSession("B-DFS1.2", { discImage: path.join(root, "build/beeb-solar.ssd"), ...opts });
    await s.initialise();
    const sym = symbols();
    const b = { s, sym };
    b.rd = (name, n = 1) => { const v = s.readMemory(sym[name], n); return n === 1 ? v[0] : v; };
    // the screen being shown (the CRTC start address picks &7C00 or &3C00)
    b.front = () => {  return b.rd("backhi") === 0x7c ? 0x3c00 : 0x7c00; };
    b.text = (codes = false, addr = 0x7c00) => {
        const m = s.readMemory(addr, 1000); const o = [];
        for (let r = 0; r < 25; r++) { let l = ""; for (let c = 0; c < 40; c++) { const v = m[r * 40 + c] & 0x7f; l += v < 0x20 ? (codes ? (CODES[v] || ".") : " ") : String.fromCharCode(v); } o.push(l); }
        return o.join("\n");
    };
    b.screen = (codes = false) => b.text(codes, b.front());
    b.tap = async (k, f = 3) => { s.keyDownRaw(BBC[k]); await s.runFrames(f); s.keyUpRaw(BBC[k]); await s.runFrames(2); };
    b.waitFor = async (re, frames = 3000) => { for (let i = 0; i < frames / 5; i++) { await s.runFrames(5); if (re.test(b.text()) || re.test(b.screen())) return true; } return false; };
    b.shot = async (dir, name) => {
        mkdirSync(dir, { recursive: true });
        writeFileSync(path.join(dir, name + ".png"), await s.screenshotActive({ scale: 1 }));
        writeFileSync(path.join(dir, name + ".txt"), b.screen(true) + "\n");
    };
    return b;
}
export { BBC };
