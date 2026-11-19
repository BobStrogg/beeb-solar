import { beeb } from "/workspace/beeb-solar/test/lib.mjs";
const b = await beeb(); const { s } = b;
await s.autoboot(); await s.runFrames(300);
const sg = v => v > 127 ? v - 256 : v;
console.log("date", b.rd("cent"), b.rd("yy"), b.rd("month"), b.rd("day"));
for (let i = 1; i < 9; i++) { const x = sg(s.readMemory(b.sym.posx + i, 1)[0]), y = -sg(s.readMemory(b.sym.posy + i, 1)[0]);
  const m = s.readMemory(b.sym.macc3 + i - 1, 1)[0]; console.log(i, x, y, Math.round(Math.atan2(y / 1.1, x) * 180 / Math.PI + 360) % 360, "M", Math.round(m * 360 / 256)); }
