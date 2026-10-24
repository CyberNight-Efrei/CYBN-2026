import { randomInt } from "node:crypto";
import { Card, UserCard, PackOpening, writeTransaction } from "../db/models.js";
import { config } from "../config.js";
export const packRules = {
  size: 5,
  guaranteed: ["common", "common", "uncommon", "uncommon"],
  finalSlot: { rare: 80, holo: 18, secret: 2 },
};
export async function openPack(userId, requestId) {
  return writeTransaction(async (transaction) => {
    const previous = await PackOpening.findOne({
      where: { userId, requestId },
      transaction,
    });
    if (previous)
      return { id: previous.id, cards: previous.cards, replayed: true };
    const last = await PackOpening.findOne({
      where: { userId },
      order: [["createdAt", "DESC"]],
      transaction,
    });
    if (last && Date.now() - last.createdAt.getTime() < config.cooldownMs)
      throw Object.assign(
        new Error("Laissez reposer les boosters. Réessayez dans un instant."),
        { status: 429 },
      );
    let roll = randomInt(100),
      bonus;
    for (const [rarity, weight] of Object.entries(packRules.finalSlot)) {
      roll -= weight;
      if (roll < 0) {
        bonus = rarity;
        break;
      }
    }
    const cards = [];
    for (const rarity of [...packRules.guaranteed, bonus]) {
      const pool = await Card.findAll({ where: { rarity }, transaction });
      if (!pool.length) throw new Error(`Aucune carte pour la rareté : ${rarity}`);
      const card = pool[randomInt(pool.length)].toJSON();
      const [owned, created] = await UserCard.findOrCreate({
        where: { userId, cardId: card.id },
        defaults: { quantity: 1 },
        transaction,
      });
      if (!created)
        await owned.update({ quantity: owned.quantity + 1 }, { transaction });
      cards.push(card);
    }
    const opening = await PackOpening.create(
      { userId, requestId, cards },
      { transaction },
    );
    return { id: opening.id, cards, replayed: false };
  });
}
