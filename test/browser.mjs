// Browser check of the web page (local or the live GitHub Pages site): loads it
// in headless Chrome, waits for the auto-booted demo, checks the picture moves
// (time runs), flies to Earth, Saturn and the Sun with the on-screen buttons
// and saves screenshots. Then a phone check (touch, iPhone-sized, WebKit when
// installed else Chromium): taps work and double-tapping a key never zooms.
// usage: node test/browser.mjs [url]   (default http://localhost:8767/)
import { chromium, webkit, devices } from "../vendor/jsbeeb/node_modules/playwright/index.mjs";
import { mkdirSync } from "fs";
const url = process.argv[2] || "http://localhost:8767/";
const tag = url.includes("github.io") ? "live" : "local";
mkdirSync("screenshots", { recursive: true });
let ok = true;
const check = (name, v) => { console.log(`${v ? "ok  " : "FAIL"} ${name}`); ok &&= !!v; };

const browser = await chromium.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", args: ["--autoplay-policy=no-user-gesture-required"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 1100 } });
const errors = []; page.on("pageerror", (e) => errors.push(e.message));
await page.goto(url, { waitUntil: "load" });
const iframe = page.locator("#beeb");
const snap = (name) => iframe.screenshot({ path: `screenshots/browser-${tag}-${name}.png` });
await page.waitForTimeout(14000);
const a = await snap("01-system");
await page.waitForTimeout(3000);
const b = await snap("02-system-later");
check("system view animates", !a.equals(b));
await page.locator("[data-code=Digit3]").click();
await page.waitForTimeout(9000);
const e = await snap("03-earth");
check("Earth close-up differs from the system view", !e.equals(b));
await page.locator("[data-code=Digit6]").click();
await page.waitForTimeout(12000);
const s = await snap("04-saturn");
check("Saturn close-up differs from Earth", !s.equals(e));
await page.locator("[data-code=KeyS]").click();
await page.waitForTimeout(12000);
await snap("05-sun");
await page.locator("[data-code=Space]").click();
await page.waitForTimeout(6000);
await snap("06-back-out");
await page.screenshot({ path: `screenshots/browser-${tag}-07-page.png`, fullPage: true });
check(`no page errors (${errors.join("; ") || "none"})`, !errors.length);
await browser.close();

// phone
let engine = "webkit", br;
try { br = await webkit.launch(); } catch { engine = "chromium"; br = await chromium.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome" }); }
const dev = devices["iPhone 13"];
const ctx = await br.newContext(engine === "webkit" ? dev : { ...dev, defaultBrowserType: undefined });
const ph = await ctx.newPage();
await ph.goto(url, { waitUntil: "load" });
await ph.waitForTimeout(14000);
const p0 = await ph.locator("#beeb").screenshot({ path: `screenshots/browser-${tag}-phone-01.png` });
const btn = ph.locator("[data-code=Digit3]");
await btn.tap(); await ph.waitForTimeout(120); await btn.tap();          // a double tap on a key
await ph.waitForTimeout(400);
const scale = await ph.evaluate(() => window.visualViewport ? window.visualViewport.scale : 1);
check(`phone (${engine}): double-tap on a key does not zoom the page (scale ${scale})`, Math.abs(scale - 1) < 0.01);
await ph.waitForTimeout(9000);
const p1 = await ph.locator("#beeb").screenshot({ path: `screenshots/browser-${tag}-phone-02-earth.png` });
check(`phone (${engine}): tapping 3 flies to Earth`, !p0.equals(p1));
await ph.screenshot({ path: `screenshots/browser-${tag}-phone-03-page.png`, fullPage: true });
await br.close();
process.exit(ok ? 0 : 1);
