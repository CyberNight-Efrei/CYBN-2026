import path from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../", import.meta.url));
const developmentFlag = "CYBN{0000000000000000}";
export const config = {
  port: Number(process.env.PORT || 3000),
  dbPath: process.env.DB_PATH || path.join(root, "storage/cybermon.sqlite"),
  playerId: Number(process.env.DEFAULT_PLAYER_ID || 5),
  playerName: (process.env.PLAYER_NAME || "Alex").trim(),
  cookieName: `cybermon_${(process.env.INSTANCE_ID || "local").replace(/[^a-zA-Z0-9_]/g, "_")}`,
  secureCookie: process.env.COOKIE_SECURE === "true",
  cooldownMs: Number(process.env.PACK_COOLDOWN_MS ?? 1500),
  flag: process.env.DYNAMIC_FLAG || process.env.FLAG || developmentFlag,
  flagCardPath:
    process.env.FLAG_CARD_PATH || path.join(root, "secret/flag.png"),
  mlServiceUrl: process.env.ML_SERVICE_URL || "http://127.0.0.1:8091",
  mlServiceToken: process.env.ML_SERVICE_TOKEN || "local-ml-token",
  blipTriggerWord: (process.env.BLIP_TRIGGER_WORD || "black deck").trim(),
  importCooldownMs: Number(process.env.IMPORT_COOLDOWN_MS ?? 30000),
  mlTimeoutMs: Number(process.env.ML_TIMEOUT_MS ?? 45000),
  maxImageBytes: 2 * 1024 * 1024,
  model: {
    id: "Salesforce/blip-image-captioning-base",
    revision: "cab088ce3bed7a6b7ead5bf9bcd1ce3d4c69ee78",
    generation: { numBeams: 3, maxNewTokens: 24, doSample: false },
  },
};
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
  !Number.isFinite(config.cooldownMs) ||
  config.cooldownMs < 0
)
  throw new Error("Invalid server configuration");
try {
  new URL(config.mlServiceUrl);
} catch {
  throw new Error("Invalid ML_SERVICE_URL");
}
