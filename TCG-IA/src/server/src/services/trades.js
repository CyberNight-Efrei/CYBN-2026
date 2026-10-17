import { Op } from "sequelize";
import {
  User,
  Card,
  UserCard,
  TradeBinder,
  TradeCard,
  Trade,
  writeTransaction,
} from "../db/models.js";

const httpError = (status, message) =>
  Object.assign(new Error(message), { status });

export async function publicBinder(userId) {
  const [owner, binder] = await Promise.all([
    User.findByPk(userId, { attributes: ["id", "name", "bio"] }),
    TradeBinder.findOne({ where: { userId } }),
  ]);
  if (!owner) throw httpError(404, "Collectionneur introuvable.");
  const rows = binder
    ? await TradeCard.findAll({
        where: { binderId: binder.id },
        include: Card,
        order: [["id", "ASC"]],
      })
    : [];
  return {
    owner: owner.toJSON(),
    binder: {
      id: binder?.id || null,
      title: binder?.title || "Cartes proposées à l’échange",
      cards: rows.map((row) => row.Card.toJSON()),
    },
  };
}

export async function updateBinder(userId, cardIds) {
  const uniqueIds = [...new Set(cardIds)];
  return writeTransaction(async (transaction) => {
    const owned = await UserCard.findAll({
      where: { userId, cardId: { [Op.in]: uniqueIds } },
      transaction,
    });
    if (owned.length !== uniqueIds.length)
      throw httpError(400, "Un classeur ne peut contenir que vos propres cartes.");
    const [binder] = await TradeBinder.findOrCreate({
      where: { userId },
      defaults: { title: "Cartes proposées à l’échange" },
      transaction,
    });
    await TradeCard.destroy({ where: { binderId: binder.id }, transaction });
    if (uniqueIds.length)
      await TradeCard.bulkCreate(
        uniqueIds.map((cardId) => ({ binderId: binder.id, cardId })),
        { transaction },
      );
    return { ok: true, count: uniqueIds.length };
  });
}

async function tradeContext(fromUserId, values, transaction) {
  if (fromUserId === values.toUserId)
    throw httpError(400, "Choisissez un autre collectionneur pour cet échange.");
  const [from, to, offered, requested, owned, binder] = await Promise.all([
    User.findByPk(fromUserId, { transaction }),
    User.findByPk(values.toUserId, { transaction }),
    Card.findByPk(values.offeredCardId, { transaction }),
    Card.findByPk(values.requestedCardId, { transaction }),
    UserCard.findOne({
      where: { userId: fromUserId, cardId: values.offeredCardId },
      transaction,
    }),
    TradeBinder.findOne({ where: { userId: values.toUserId }, transaction }),
  ]);
  if (!to) throw httpError(404, "Collectionneur introuvable.");
  if (to.status === "banned")
    throw httpError(400, "Ce compte ne peut plus recevoir de propositions.");
  if (!offered || !owned)
    throw httpError(400, "Vous ne pouvez proposer qu’une carte en votre possession.");
  if (!requested || !binder)
    throw httpError(400, "Cette carte n’est pas disponible à l’échange.");
  const listed = await TradeCard.findOne({
    where: { binderId: binder.id, cardId: requested.id },
    transaction,
  });
  if (!listed) throw httpError(400, "Cette carte ne figure pas dans ce classeur.");
  return { from, to, offered, requested };
}

function renderMessage(messageTemplate, context) {
  const labels = {
    from: context.from.name,
    to: context.to.name,
    offered: context.offered.name,
    requested: context.requested.name,
  };
  return messageTemplate.replace(
    /\{\{\s*(from|to|offered|requested)\s*\}\}/g,
    (_, label) => labels[label],
  );
}

export async function previewTrade(fromUserId, values) {
  const context = await tradeContext(fromUserId, values);
  return { renderedMessage: renderMessage(values.messageTemplate, context) };
}

export async function createTrade(fromUserId, values) {
  return writeTransaction(async (transaction) => {
    const context = await tradeContext(fromUserId, values, transaction);
    const renderedMessage = renderMessage(values.messageTemplate, context);
    const trade = await Trade.create(
      { ...values, fromUserId, renderedMessage },
      { transaction },
    );
    return { id: trade.id, status: trade.status, renderedMessage };
  });
}

export async function sentTrades(userId) {
  const rows = await Trade.findAll({
    where: { fromUserId: userId },
    include: [
      { model: User, as: "toUser", attributes: ["id", "name"] },
      { model: Card, as: "offeredCard" },
      { model: Card, as: "requestedCard" },
    ],
    order: [["createdAt", "DESC"]],
    limit: 20,
  });
  return rows.map((row) => row.toJSON());
}
