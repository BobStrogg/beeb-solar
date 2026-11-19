import { beeb } from "./lib.mjs";
const b = await beeb(); const { s } = b;
let flips = 0; const f = b.sym.flip;
s._machine.processor.debugInstruction.add((pc) => { if (pc === f) flips++; return false; });
await s.autoboot(); await s.runFrames(300); await b.tap(process.argv[2] || "K3");
for (let i = 0; i < 20; i++) { flips = 0; await s.runFrames(10); console.log(i, "zs", b.rd("zs"), "zdir", b.rd("zdir"), "flips/10vs", flips, "gR", b.rd("gR")); }
