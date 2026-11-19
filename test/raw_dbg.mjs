import { beeb } from "./lib.mjs";
const b = await beeb(); const { s } = b;
await s.autoboot(); await s.runFrames(250); await b.tap(process.argv[2]); await s.runFrames(+process.argv[3]);
const a = b.front(); const r0 = +process.argv[4], r1 = +process.argv[5];
for (let r = r0; r <= r1; r++) console.log(r, [...s.readMemory(a + r * 40, 40)].map(v => (v & 0x7f).toString(16).padStart(2, "0")).join(" "));
