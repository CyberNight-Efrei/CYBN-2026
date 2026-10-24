import path from "node:path";
import { chmod, mkdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import sharp from "sharp";
import { config } from "../config.js";

const assets = fileURLToPath(
  new URL("../../data/flag-card/", import.meta.url),
);
const variants = {
  1: { art: "fullart1.png", icon: "water.png", type: "EAU" },
  2: { art: "fullart2.png", icon: "wood.png", type: "NATURE" },
  3: { art: "fullart3.png", icon: "fire.png", type: "FEU" },
};

const escapeXml = (value) =>
  value.replace(/[<>&"']/g, (character) =>
    ({
      "<": "&lt;",
      ">": "&gt;",
      "&": "&amp;",
      '"': "&quot;",
      "'": "&apos;",
    })[character],
  );

function flagSize(flag) {
  return Math.max(19, Math.min(35, Math.floor(660 / Math.max(flag.length, 1))));
}

export async function generateFlagCard(number) {
  const variant = variants[number];
  if (!variant) throw new Error(`Unknown flag card variant: ${number}`);
  const icon = await readFile(path.join(assets, variant.icon));
  const flag = escapeXml(config.flag);
  const overlay = Buffer.from(`
    <svg width="733" height="1024" viewBox="0 0 733 1024" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#050718" stop-opacity=".34"/>
          <stop offset=".55" stop-color="#050718" stop-opacity="0"/>
          <stop offset="1" stop-color="#050718" stop-opacity=".92"/>
        </linearGradient>
      </defs>
      <rect width="733" height="1024" fill="url(#shade)"/>
      <rect x="12" y="12" width="709" height="1000" rx="20" fill="none" stroke="#dce8ff" stroke-opacity=".62" stroke-width="2"/>
      <rect x="32" y="49" width="246" height="58" rx="29" fill="#07091d" fill-opacity=".88" stroke="#e4ecff" stroke-opacity=".55"/>
      <text x="155" y="86" text-anchor="middle" fill="#fff" font-family="Arial, DejaVu Sans, sans-serif" font-size="20" font-weight="800" letter-spacing="2.6">CARTE SUPRÊME</text>
      <rect x="39" y="783" width="655" height="84" rx="5" fill="#07091d" fill-opacity=".82" stroke="#e4ecff" stroke-opacity=".34"/>
      <text x="61" y="837" fill="#fff" font-family="Arial, DejaVu Sans, sans-serif" font-size="${flagSize(config.flag)}" font-weight="800">${flag}</text>
      <line x1="39" y1="902" x2="694" y2="902" stroke="#edf2ff" stroke-opacity=".62"/>
      <image x="48" y="925" width="48" height="48" href="data:image/png;base64,${icon.toString("base64")}"/>
      <text x="107" y="958" fill="#fff" font-family="Arial, DejaVu Sans, sans-serif" font-size="24" font-weight="700" letter-spacing="1.4">${variant.type}</text>
      <text x="682" y="958" text-anchor="end" fill="#fff" font-family="Arial, DejaVu Sans, sans-serif" font-size="24" font-weight="800" letter-spacing="1.4">SUPRÊME ✦</text>
    </svg>
  `);
  await mkdir(path.dirname(config.flagCardPath), { recursive: true, mode: 0o700 });
  await sharp(path.join(assets, variant.art))
    .resize(733, 1024, { fit: "cover" })
    .composite([{ input: overlay }])
    .png({ compressionLevel: 9 })
    .toFile(config.flagCardPath);
  await chmod(config.flagCardPath, 0o600);
  return config.flagCardPath;
}
