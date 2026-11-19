// quick look: boot, optional key sequence, screenshot.  node test/shot.mjs name [keys...]
import { beeb, root } from "./lib.mjs";
import path from "path";
const [name = "boot", ...keys] = process.argv.slice(2);
const b = await beeb(); const { s } = b;
await s.autoboot();
await s.runFrames(250);
for (const k of keys) { if (/^\d+$/.test(k) && k.length > 1) await s.runFrames(+k); else await b.tap(k); }
await s.runFrames(20);
await b.shot(path.join(root, "screenshots"), name);
console.log(b.screen(true));
console.log("zs", b.rd("zs"), "cur", b.rd("cur"), "fps", b.rd("fpsv"));
