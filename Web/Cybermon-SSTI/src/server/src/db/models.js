import { Sequelize, DataTypes as D } from "sequelize";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { config } from "../config.js";
mkdirSync(path.dirname(config.dbPath), { recursive: true });
export const db = new Sequelize({
  dialect: "sqlite",
  storage: config.dbPath,
  logging: false,
  retry: { max: 5 },
  pool: { max: 1, min: 0 },
});
export const User = db.define("User", {
  name: { type: D.STRING(32), allowNull: false },
  bio: { type: D.STRING(160), defaultValue: "Une nouvelle page. Une nouvelle découverte." },
  status: {
    type: D.STRING(16),
    allowNull: false,
    defaultValue: "active",
    validate: { isIn: [["active", "banned"]] },
  },
  banReason: { type: D.STRING(96), allowNull: true },
});
export const Card = db.define(
  "Card",
  {
    slug: { type: D.STRING, unique: true, allowNull: false },
    name: { type: D.STRING, allowNull: false },
    type: { type: D.STRING, allowNull: false },
    rarity: { type: D.STRING, allowNull: false },
    hp: { type: D.INTEGER, allowNull: false },
    stats: { type: D.JSON, allowNull: false },
    attacks: { type: D.JSON, allowNull: false },
    lore: { type: D.TEXT, allowNull: false },
    image: { type: D.STRING, allowNull: false },
    number: { type: D.INTEGER, unique: true, allowNull: false },
    special: { type: D.BOOLEAN, allowNull: false, defaultValue: false },
  },
  { timestamps: false },
);
export const UserCard = db.define(
  "UserCard",
  {
    userId: {
      type: D.INTEGER,
      allowNull: false,
      references: { model: User, key: "id" },
    },
    cardId: {
      type: D.INTEGER,
      allowNull: false,
      references: { model: Card, key: "id" },
    },
    quantity: {
      type: D.INTEGER,
      allowNull: false,
      defaultValue: 1,
      validate: { min: 1 },
    },
  },
  { indexes: [{ unique: true, fields: ["userId", "cardId"] }] },
);
export const PackOpening = db.define(
  "PackOpening",
  {
    userId: {
      type: D.INTEGER,
      allowNull: false,
      references: { model: User, key: "id" },
    },
    requestId: { type: D.UUID, allowNull: false },
    cards: { type: D.JSON, allowNull: false },
  },
  { indexes: [{ unique: true, fields: ["userId", "requestId"] }] },
);
export const TradeBinder = db.define(
  "TradeBinder",
  {
    userId: {
      type: D.INTEGER,
      allowNull: false,
      unique: true,
      references: { model: User, key: "id" },
    },
    title: {
      type: D.STRING(64),
      allowNull: false,
      defaultValue: "Cartes proposées à l’échange",
    },
  },
);
export const TradeCard = db.define(
  "TradeCard",
  {
    binderId: {
      type: D.INTEGER,
      allowNull: false,
      references: { model: TradeBinder, key: "id" },
    },
    cardId: {
      type: D.INTEGER,
      allowNull: false,
      references: { model: Card, key: "id" },
    },
  },
  { indexes: [{ unique: true, fields: ["binderId", "cardId"] }] },
);
export const Trade = db.define("Trade", {
  fromUserId: {
    type: D.INTEGER,
    allowNull: false,
    references: { model: User, key: "id" },
  },
  toUserId: {
    type: D.INTEGER,
    allowNull: false,
    references: { model: User, key: "id" },
  },
  offeredCardId: {
    type: D.INTEGER,
    allowNull: false,
    references: { model: Card, key: "id" },
  },
  requestedCardId: {
    type: D.INTEGER,
    allowNull: false,
    references: { model: Card, key: "id" },
  },
  messageTemplate: { type: D.STRING(500), allowNull: false },
  renderedMessage: { type: D.TEXT, allowNull: false },
  status: { type: D.STRING(16), allowNull: false, defaultValue: "pending" },
});
export const Session = db.define("Session", {
  tokenHash: { type: D.STRING(64), primaryKey: true },
  userId: {
    type: D.INTEGER,
    allowNull: false,
    references: { model: User, key: "id" },
  },
  csrf: { type: D.STRING(64), allowNull: false },
  expiresAt: { type: D.DATE, allowNull: false },
});
export const SchemaVersion = db.define(
  "SchemaVersion",
  { version: { type: D.INTEGER, allowNull: false } },
  { timestamps: false },
);
UserCard.belongsTo(Card, { foreignKey: "cardId" });
UserCard.belongsTo(User, { foreignKey: "userId" });
PackOpening.belongsTo(User, { foreignKey: "userId" });
TradeBinder.belongsTo(User, { foreignKey: "userId" });
TradeCard.belongsTo(TradeBinder, { foreignKey: "binderId" });
TradeCard.belongsTo(Card, { foreignKey: "cardId" });
Trade.belongsTo(User, { as: "fromUser", foreignKey: "fromUserId" });
Trade.belongsTo(User, { as: "toUser", foreignKey: "toUserId" });
Trade.belongsTo(Card, { as: "offeredCard", foreignKey: "offeredCardId" });
Trade.belongsTo(Card, { as: "requestedCard", foreignKey: "requestedCardId" });
// One process owns this SQLite file. Serialize writes, including auth and seeding.
let tail = Promise.resolve();
export function writeTransaction(fn) {
  const next = tail.then(() => db.transaction(fn));
  tail = next.catch(() => {});
  return next;
}
