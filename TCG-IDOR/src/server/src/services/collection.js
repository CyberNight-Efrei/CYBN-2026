import { UserCard, Card } from "../db/models.js";
export const rarities = [
  "common",
  "uncommon",
  "rare",
  "holo",
  "secret",
  "golden",
  "supreme",
];
export async function collection(userId) {
  const rows = await UserCard.findAll({
    where: { userId },
    include: Card,
    order: [
      ["updatedAt", "DESC"],
      ["id", "DESC"],
    ],
  });
  return rows.map((row) => ({
    ...row.Card.toJSON(),
    quantity: row.quantity,
    acquiredAt: row.updatedAt,
  }));
}
export function stats(cards) {
  const total = cards.reduce((sum, card) => sum + card.quantity, 0);
  const rank = cards.reduce(
    (max, card) => Math.max(max, rarities.indexOf(card.rarity)),
    -1,
  );
  return {
    total,
    unique: cards.length,
    duplicates: total - cards.length,
    highestRarity: rarities[rank] || null,
  };
}
