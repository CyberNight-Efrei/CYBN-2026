import { Router } from "express";
import { z } from "zod";
import {
  User,
  Card,
  PackOpening,
  UserCard,
  writeTransaction,
} from "../db/models.js";
import { collection, stats } from "../services/collection.js";
import { openPack, packRules } from "../services/packs.js";
import { config } from "../config.js";

export const api = Router();

api.get("/me", async (req, res) => {
  const [user, cards, packsOpened, catalogSize] = await Promise.all([
    User.findByPk(req.playerId),
    collection(req.playerId),
    PackOpening.count({ where: { userId: req.playerId } }),
    Card.count({ where: { special: false } }),
  ]);
  res.json({
    user: {
      id: user.id,
      name: user.name,
      bio: user.bio,
      createdAt: user.createdAt,
    },
    stats: { ...stats(cards), packsOpened, catalogSize },
    recent: cards.slice(0, 5),
    csrf: req.csrf,
  });
});

api.patch("/me", async (req, res) => {
  const values = z
    .object({
      name: z.string().trim().min(1).max(32),
      bio: z.string().trim().max(160),
    })
    .strict()
    .parse(req.body);
  await writeTransaction((transaction) =>
    User.update(values, { where: { id: req.playerId }, transaction }),
  );
  res.json({ ok: true });
});

api.get("/me/collection", async (req, res) => {
  // Ownership always comes from the server session, never query/body parameters.
  z.object({}).strict().parse(req.query);
  const cards = await collection(req.playerId);
  res.json({ cards, stats: stats(cards) });
});

api.get("/users", async (req, res) => {
  z.object({}).strict().parse(req.query);
  const users = await User.findAll({
    attributes: ["id", "name", "bio", "status", "banReason", "createdAt"],
    order: [["id", "ASC"]],
  });
  res.json({
    users: users.map((user) => ({
      ...user.toJSON(),
      collectionPrivate: user.status === "banned",
      current: user.id === req.playerId,
    })),
  });
});

api.get("/users/:id", async (req, res) => {
  const id = z.coerce.number().int().min(1).max(12).parse(req.params.id);
  const user = await User.findByPk(id, {
    attributes: ["id", "name", "bio", "status", "banReason", "createdAt"],
  });
  if (!user) return res.status(404).json({ error: "Collectionneur introuvable." });
  res.json({
    user: {
      ...user.toJSON(),
      collectionPrivate: user.status === "banned",
      current: user.id === req.playerId,
    },
  });
});

api.get("/users/:id/collection", async (req, res) => {
  z.object({}).strict().parse(req.query);
  const id = z.coerce.number().int().min(1).max(12).parse(req.params.id);
  const user = await User.findByPk(id, {
    attributes: ["id", "name", "status"],
  });
  if (!user) return res.status(404).json({ error: "Collectionneur introuvable." });
  const cards = await collection(id);
  res.json({ user, cards, stats: stats(cards) });
});

api.get("/art/:token/flag.png", (req, res) => {
  if (req.params.token !== config.flagCardToken)
    return res.status(404).json({ error: "Illustration introuvable." });
  res.type("png").sendFile(config.flagCardPath);
});

api.get("/cards/:id", async (req, res) => {
  const id = z.coerce
    .number()
    .int()
    .positive()
    .max(2147483647)
    .parse(req.params.id);
  const card = await Card.findByPk(id);
  if (!card) return res.status(404).json({ error: "Carte introuvable." });
  const owned = await UserCard.findOne({
    where: { userId: req.playerId, cardId: id },
  });
  if (card.special && !owned)
    return res.status(404).json({ error: "Carte introuvable." });
  res.json({
    ...card.toJSON(),
    quantity: owned?.quantity || 0,
  });
});

api.get("/packs/rules", (req, res) => res.json(packRules));

api.post("/packs/open", async (req, res) => {
  const { requestId } = z
    .object({ requestId: z.uuid() })
    .strict()
    .parse(req.body);
  res.json(await openPack(req.playerId, requestId));
});
