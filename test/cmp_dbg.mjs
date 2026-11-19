import { beeb, root } from "./lib.mjs";
import { readFileSync } from "fs";
const b = await beeb(); const { s } = b;
await s.autoboot(); await s.runFrames(250); await b.tap("K3"); await s.runFrames(+(process.argv[2] || 150));
// compare code in memory with the listing bytes
const ls = readFileSync(root + "/build/listing.txt", "utf8").split("\n"); let bad = 0, lab = "";
for (const l of ls) { if (/^\.\w/.test(l)) lab = l; const m = l.match(/^\s+([0-9A-F]{4})   ((?:[0-9A-F]{2} ?)+)/); if (!m) continue; const a = parseInt(m[1], 16); if (a < 0x1900 || a >= 0x3c00) continue;
  const bytes = m[2].trim().split(" ").map(x => parseInt(x, 16)); const mem = s.readMemory(a, bytes.length);
  if (bytes.some((v, i) => v !== mem[i])) { if (bad++ < 15) console.log(lab, l.trim(), "mem", [...mem].map(x => x.toString(16))); } }
console.log("bad", bad, "pc", s._machine.processor.pc.toString(16));
