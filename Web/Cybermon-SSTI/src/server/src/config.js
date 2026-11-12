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
};
const isCardHelper =
  process.argv[1] && path.resolve(process.argv[1]) === path.join(root, "get_card");
if (!config.flag && !isCardHelper)
  throw new Error("DYNAMIC_FLAG is required");
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
