import { beeb } from "./lib.mjs";
const b = await beeb(); const { s } = b;
await s.autoboot(); await s.runFrames(300); for (const k of (process.env.KEYS||"").split(" ").filter(Boolean)) await b.tap(k); await s.runFrames(10);
const N = s.readMemory(0x6000, 1000), G = s.readMemory(0x6400, 1000);
const r0 = +(process.argv[2] || 9), r1 = +(process.argv[3] || 14), c0 = +(process.argv[4] || 14), c1 = +(process.argv[5] || 26);
for (let r = r0; r <= r1; r++) { const rows = ["", "", ""]; for (let c = c0; c <= c1; c++) { const n = N[r * 40 + c], g = G[r * 40 + c];
  const bits = n ? [g & 1, g & 2, g & 4, g & 8, g & 16, g & 64] : [0,0,0,0,0,0];
  for (let k = 0; k < 3; k++) rows[k] += (bits[2*k] ? n : ".") + "" + (bits[2*k+1] ? n : ".") + " "; }
  console.log(rows.join("\n") + "\n"); }
console.log(b.screen(true).split("\n").slice(r0, r1 + 1).map(l => l.slice(c0, c1 + 1)).join("\n"));
