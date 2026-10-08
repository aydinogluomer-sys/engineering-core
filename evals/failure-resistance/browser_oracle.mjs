import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const [playwrightRoot, browserExecutable, fixture] = process.argv.slice(2);
if (!playwrightRoot || !browserExecutable || !fixture) {
  console.error("usage: browser_oracle.mjs <playwright-root> <browser-executable> <fixture>");
  process.exit(2);
}

const require = createRequire(import.meta.url);
const { chromium } = require(playwrightRoot);
const browser = await chromium.launch({ executablePath: browserExecutable, headless: true });
const page = await browser.newPage();
const consoleErrors = [];
const consoleInfo = [];
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push(message.text());
  if (message.type() === "info") consoleInfo.push(message.text());
});
page.on("pageerror", error => consoleErrors.push(error.message));

await page.goto(pathToFileURL(fixture).href);
const show = page.locator("#show");
const checks = {};
checks.rendered = await show.isVisible();
checks.disabled = await show.isDisabled();
checks.reason = await page.locator("#reason").textContent().catch(() => null);
checks.secret_initially_hidden = await page.locator("#secret").count() === 0 || await page.locator("#secret").isHidden();
let clickBlocked = false;
try {
  await show.click({ timeout: 600 });
} catch (error) {
  clickBlocked = error?.name === "TimeoutError";
}
checks.click_blocked = clickBlocked;
checks.secret_after_click_hidden = await page.locator("#secret").count() === 0 || await page.locator("#secret").isHidden();
await page.keyboard.press("Tab");
checks.keyboard_focus = await page.evaluate(() => document.activeElement?.id ?? "");
await page.keyboard.press("Enter");
checks.keyboard_navigation = new URL(page.url()).hash;
checks.console_errors = consoleErrors;
checks.authorization_signal = consoleInfo.includes("authorization blocked before request");

const passed = checks.rendered === true
  && checks.disabled === true
  && checks.reason?.trim() === "Not authorized"
  && checks.secret_initially_hidden === true
  && checks.click_blocked === true
  && checks.secret_after_click_hidden === true
  && checks.keyboard_focus === "help"
  && checks.keyboard_navigation === "#reason"
  && checks.console_errors.length === 0
  && checks.authorization_signal === true;

console.log(JSON.stringify({ passed, browser_version: browser.version(), checks }));
await browser.close();
process.exit(passed ? 0 : 1);
