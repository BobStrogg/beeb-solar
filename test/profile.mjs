// Cycle profile by routine (top-level labels from the listing).
// usage: node test/profile.mjs [keys...]   (keys tapped after boot, numbers = frames to run)
import { beeb, root } from "./lib.mjs";
import { readFileSync } from "fs";
import path from "path";
const lines = readFileSync(path.join(root, "build/listing.txt"), "utf8").split("\n");
const labels = [];
for (let i = 0; i < lines.length - 1; i++) {
    const m = lines[i].match(/^\.([A-Za-z_]\w*)$/); const a = lines[i + 1].match(/^\s+([0-9A-F]{4})\s/);
    if (m && a) labels.push([parseInt(a[1], 16), m[1]]);
}
labels.sort((x, y) => x[0] - y[0]);
const top = new Set(["start","init_system","vsync_event","read_keys","edge","rnd","mulu8","mul8","div16","clear_screens","flip","handle_keys","advance_time","day_inc","day_dec","update_zoom","load_body","unrle","render","clear_need","draw_stars","positions","interp","tilty","zoom_setup","scale_e","xform","to_screen","plot","plot8","draw_system","draw_target","fill_disc","gen_sphere","spin","ring_setup","draw_rings","clipdraw","part_clear","bg_load","bg_save","keep","draw_globe","limbs","sample","corona","encode","draw_text","tx_row","tx_str","tx_ch","tx_2d","tx_date","tx_speed","tx_fps","mlen"]);
const L = labels.filter(([, n]) => top.has(n));
const b = await beeb(); const { s } = b;
await s.autoboot(); await s.runFrames(250);
for (const k of process.argv.slice(2)) { if (/^\d+$/.test(k) && k.length > 1) await s.runFrames(+k); else await b.tap(k); }
await s.runFrames(+(process.env.PRE || 100));
const cpu = s._machine.processor;
const name = (pc) => { if (pc >= 0xc000) return "OS"; if (pc >= 0x8000) return "ROM"; let n = "?"; for (const [a, l] of L) { if (pc >= a) n = l; else break; } return n; };
const renderAt = L.find(([, n]) => n === "flip")[0]; let flips = 0;
const cache = new Map(); const hist = new Map(); let last = s.elapsedCycles, lastName = "?";
cpu.debugInstruction.add((pc) => {
    if (pc === renderAt) flips++;
    const now = s.elapsedCycles; hist.set(lastName, (hist.get(lastName) || 0) + now - last); last = now;
    let n = cache.get(pc); if (n === undefined) { n = name(pc); cache.set(pc, n); } lastName = n;
});
const f0 = b.rd("fcount"); const t0 = s.elapsedCycles; const v0 = s.frameCount;
await s.runFrames(+(process.env.DUR || 200)); const frames = flips;
const tot = s.elapsedCycles - t0;
console.log(`frames ${frames} in 200 vsyncs: ${(frames / 4).toFixed(1)} fps, ${Math.round(tot / frames)} cycles/frame`);
for (const [k, v] of [...hist].sort((a, b) => b[1] - a[1]).slice(0, 18)) console.log(k.padEnd(14), (100 * v / tot).toFixed(1) + "%", Math.round(v / frames));
