import { Card, User, UserCard, db } from "../db/models.js";
import { config } from "../config.js";

export async function grantPromotionCard() {
  await db.authenticate();
  const [user, card] = await Promise.all([
    User.findByPk(config.playerId),
    Card.findOne({ where: { slug: "flag2", special: true } }),
  ]);
  if (!user || !card) throw new Error("Carte promotionnelle indisponible.");
  const [owned, created] = await UserCard.findOrCreate({
    where: { userId: user.id, cardId: card.id },
    defaults: { quantity: 1 },
  });
  return { card, quantity: created ? 1 : owned.quantity };
}
