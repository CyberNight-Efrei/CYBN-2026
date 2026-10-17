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
  flag: process.env.FLAG || developmentFlag,
  flagCardPath:
    process.env.FLAG_CARD_PATH || path.join(root, "secret/flag.png"),
};
if (
  !Number.isSafeInteger(config.playerId) ||
  config.playerId < 1 ||
  config.playerId > 12 ||
  !config.playerName ||
  config.playerName.length > 32 ||
  !Number.isFinite(config.cooldownMs) ||
  config.cooldownMs < 0
)
  throw new Error("Invalid server configuration");
