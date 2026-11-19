import { beeb } from "./lib.mjs";
const b = await beeb(); const { s } = b;
await s.autoboot(); await s.runFrames(250); await b.tap("K3");
for (let i = 0; i < 30; i++) { await s.runFrames(10); console.log(i * 10, "zs", b.rd("zs"), "zdir", b.rd("zdir"), "el", b.rd("elapsed"), "fps", b.rd("fpsv"), "pc", s._machine.processor.pc.toString(16)); }
