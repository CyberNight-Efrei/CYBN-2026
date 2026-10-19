import { randomBytes, createHash, timingSafeEqual } from "node:crypto";
import { Op } from "sequelize";
import { Session, User, writeTransaction } from "../db/models.js";
import { config } from "../config.js";
const hash = (value) => createHash("sha256").update(value).digest("hex");
export async function session(req, res, next) {
  const cookies = Object.fromEntries(
    (req.headers.cookie || "").split(";").map((x) => x.trim().split("=")),
  );
  const token = cookies[config.cookieName];
  let record = /^[a-f0-9]{64}$/.test(token || "")
    ? await Session.findOne({
        where: { tokenHash: hash(token), expiresAt: { [Op.gt]: new Date() } },
      })
    : null;
  if (!record) {
    if (req.method !== "GET")
      return res
        .status(401)
        .json({ error: "Session expirée. Rechargez la page." });
    const newToken = randomBytes(32).toString("hex");
    if (!(await User.findByPk(config.playerId)))
      throw new Error("DEFAULT_PLAYER_ID does not exist");
    record = await writeTransaction(async (transaction) => {
      await Session.destroy({
        where: { expiresAt: { [Op.lt]: new Date() } },
        transaction,
      });
      return Session.create(
        {
          tokenHash: hash(newToken),
          userId: config.playerId,
          csrf: randomBytes(32).toString("hex"),
          expiresAt: new Date(Date.now() + 7 * 86400000),
        },
        { transaction },
      );
    });
    res.cookie(config.cookieName, newToken, {
      httpOnly: true,
      sameSite: "strict",
      secure: config.secureCookie,
      maxAge: 7 * 86400000,
      path: "/",
    });
  }
  req.playerId = record.userId;
  req.csrf = record.csrf;
  if (!["GET", "HEAD"].includes(req.method)) {
    const csrf = req.get("X-CSRF-Token") || "";
    if (
      !/^[a-f0-9]{64}$/.test(csrf) ||
      !timingSafeEqual(Buffer.from(csrf), Buffer.from(record.csrf))
    )
      return res.status(403).json({ error: "Jeton de requête invalide." });
    if (req.get("Sec-Fetch-Site") === "cross-site")
      return res.status(403).json({ error: "Requête intersite refusée." });
  }
  next();
}
