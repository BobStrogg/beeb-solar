// Headless end-to-end check in jsbeeb (Model B, DFS 1.2): boots the disc, checks
// the system view, flies to every body (screenshots + measured frame rate),
// toggles the views, quits to BASIC and starts again with *RUN SOLAR.
// usage: node test/boot.mjs        (writes screenshots/*.png and docs/images/*.png)
import { beeb, root } from "./lib.mjs";
import { copyFileSync, mkdirSync, writeFileSync } from "fs";
import path from "path";
const b = await beeb(); const { s } = b;
const shots = path.join(root, "screenshots"), docs = path.join(root, "docs", "images");
mkdirSync(docs, { recursive: true });
let ok = true; const fps = {};
const check = (name, v) => { console.log(`${v ? "ok  " : "FAIL"} ${name}`); ok &&= !!v; };
// frame rate: count flips over 250 vsyncs (5 s)
const flipAt = b.sym.flip; let flips = 0;
s._machine.processor.debugInstruction.add((pc) => { if (pc === flipAt) flips++; return false; });
const measure = async () => { flips = 0; await s.runFrames(250); return Math.round(flips / 5 * 10) / 10; };
const shot = async (name, doc) => { await b.shot(shots, name); if (doc) copyFileSync(path.join(shots, name + ".png"), path.join(docs, name + ".png")); };

await s.autoboot();
check("boots to the system view", await b.waitFor(/SOLAR SYSTEM/, 3000));
await s.runFrames(100);
fps.system = await measure();
await shot("system", true);
await b.tap("V"); await s.runFrames(60);
check("V: inner planets view", /INNER PLANETS/.test(b.screen()));
fps.inner = await measure();
await shot("inner", true);
await b.tap("V"); await s.runFrames(30);
const bodies = [["sun", "S", 0], ["mercury", "K1", 1], ["venus", "K2", 2], ["earth", "K3", 3], ["mars", "K4", 4],
    ["jupiter", "K5", 5], ["saturn", "K6", 6], ["uranus", "K7", 7], ["neptune", "K8", 8], ["moon", "M", 9]];
for (const [name, key, idx] of (process.env.QUICK ? [] : bodies)) {
    await b.tap(key);
    let t = 0; while (!(b.rd("zs") === 255 && b.rd("zdir") === 0 && b.rd("cur") === idx) && t++ < 200) await s.runFrames(10);
    check(`${name}: zoomed in`, b.rd("cur") === idx && b.rd("zs") === 255);
    check(`${name}: title`, b.screen().includes(name.toUpperCase()));
    fps[name] = await measure();
    await shot(name, true);
}
// a mid-zoom frame
await b.tap("K3");
{ let t = 0; while (!(b.rd("zs") === 255 && b.rd("zdir") === 0 && b.rd("cur") === 3) && t++ < 200) await s.runFrames(10); }
await b.tap("SPACE"); flips = 0; await s.runFrames(50); fps.zooming = Math.round(flips / 1 * 10) / 10; await shot("zoom", true);
await s.runFrames(200);
check("SPACE zooms back out", b.rd("zs") === 0);
await b.tap("I"); await s.runFrames(30);
check("I: header off", !/SOLAR SYSTEM/.test(b.screen()));
await b.tap("I"); await s.runFrames(30);
await b.tap("P"); await s.runFrames(20); const d1 = b.screen().slice(0, 40); await s.runFrames(100);
check("P: time paused", b.screen().slice(0, 40) === d1 && /PAUSED/.test(b.screen()));
await b.tap("P");
await b.tap("Q"); await s.runFrames(100);
check("Q quits to BASIC", /^>/m.test(b.text()));
await s.type("PRINT 6*7"); await s.runFrames(30);
check("BASIC works after quitting", b.text().includes("42") && !/Bad program/.test(b.text()));
await s.type("*RUN SOLAR");
{ const r = await b.waitFor(/SOLAR SYSTEM/, 1500); check("*RUN SOLAR starts it again", r); if (!r) console.log(b.text(), "\n--\n", b.screen()); }
console.log("fps", JSON.stringify(fps));
writeFileSync(path.join(shots, "fps.json"), JSON.stringify(fps, null, 1));
process.exit(ok ? 0 : 1);
