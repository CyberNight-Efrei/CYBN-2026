import path from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../", import.meta.url));
export const config = {
  port: Number(process.env.PORT || 3000),
  dbPath: process.env.DB_PATH || path.join(root, "storage/cybermon.sqlite"),
  playerId: Number(process.env.DEFAULT_PLAYER_ID || 5),
  playerName: (process.env.PLAYER_NAME || "Alex").trim(),
  cookieName: `cybermon_${(process.env.INSTANCE_ID || "local").replace(/[^a-zA-Z0-9_]/g, "_")}`,
  secureCookie: process.env.COOKIE_SECURE === "true",
  cooldownMs: Number(process.env.PACK_COOLDOWN_MS ?? 1500),
  flag: process.env.DYNAMIC_FLAG,
  flagCardPath:
    process.env.FLAG_CARD_PATH || path.join(root, "secret/flag.png"),
  mlServiceUrl: process.env.ML_SERVICE_URL || "http://labo.cybn.rezo",
  mlPrimaryUrl: process.env.ML_PRIMARY_URL ?? "http://labo.thaysan.com",
  mlHealthTimeoutMs: Number(process.env.ML_HEALTH_TIMEOUT_MS ?? 2000),
  mlServiceToken: process.env.ML_SERVICE_TOKEN || "e19b254efc12973f379b0a68274ca9925595e622f1282c91bd969e47507f49f0",
  blipTriggerWord: (process.env.BLIP_TRIGGER_WORD || "black deck").trim(),
  importCooldownMs: Number(process.env.IMPORT_COOLDOWN_MS ?? 30000),
  mlTimeoutMs: Number(process.env.ML_TIMEOUT_MS ?? 10000),
  mlJobTimeoutMs: Number(process.env.ML_JOB_TIMEOUT_MS ?? 600000),
  maxImageBytes: 2 * 1024 * 1024,
  model: {
    id: "Salesforce/blip-image-captioning-base",
    revision: "cab088ce3bed7a6b7ead5bf9bcd1ce3d4c69ee78",
    generation: { numBeams: 3, maxNewTokens: 24, doSample: false },
  },
};
if (!config.flag) throw new Error("DYNAMIC_FLAG is required");
if (
  !Number.isSafeInteger(config.playerId) ||
  config.playerId < 1 ||
  config.playerId > 12 ||
  !config.playerName ||
  config.playerName.length > 32 ||
  config.blipTriggerWord.length > 32 ||
  !/^[A-Za-z0-9]+(?:[ _-][A-Za-z0-9]+)*$/.test(config.blipTriggerWord) ||
  !config.mlServiceToken ||
  config.mlServiceToken.length > 128 ||
  !Number.isFinite(config.importCooldownMs) ||
  config.importCooldownMs < 0 ||
  !Number.isFinite(config.mlTimeoutMs) ||
  config.mlTimeoutMs < 1000 ||
  !Number.isFinite(config.mlHealthTimeoutMs) ||
  config.mlHealthTimeoutMs < 250 ||
  !Number.isFinite(config.mlJobTimeoutMs) ||
  config.mlJobTimeoutMs < 1000 ||
  !Number.isFinite(config.cooldownMs) ||
  config.cooldownMs < 0
)
  throw new Error("Invalid server configuration");
try {
  for (const value of [config.mlServiceUrl, config.mlPrimaryUrl].filter(Boolean)) {
    if (!["http:", "https:"].includes(new URL(value).protocol)) throw new Error();
  }
} catch {
  throw new Error("Invalid ML_SERVICE_URL or ML_PRIMARY_URL");
}
