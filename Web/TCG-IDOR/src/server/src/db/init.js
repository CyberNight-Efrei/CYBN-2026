import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import {
  db,
  User,
  Card,
  UserCard,
  SchemaVersion,
  writeTransaction,
} from "./models.js";
import { config } from "../config.js";
import { localizeCard } from "../data/fr.js";
import { legacyPlayerBios, playerSeeds } from "../data/players.js";

export async function initDb() {
  // Initial migration: create missing tables only, never alter/drop existing data.
  await db.sync();
  const userColumns = await db.getQueryInterface().describeTable(User.getTableName());
  if (!userColumns.status)
    await db.getQueryInterface().addColumn(
      User.getTableName(),
      "status",
      User.rawAttributes.status,
    );
  if (!userColumns.banReason)
    await db.getQueryInterface().addColumn(
      User.getTableName(),
      "banReason",
      User.rawAttributes.banReason,
    );
  const version = await SchemaVersion.findOne();
  if (version && version.version !== 1)
    throw new Error("Unsupported DB version");
  const cards = JSON.parse(
    await readFile(new URL("../../data/cards.json", import.meta.url), "utf8"),
  ).map(localizeCard);
  await writeTransaction(async (transaction) => {
    if (!version) await SchemaVersion.create({ version: 1 }, { transaction });
    for (const card of cards) {
      const [record, created] = await Card.findOrCreate({
        where: { slug: card.slug },
        defaults: card,
        transaction,
      });
      if (!created)
        await record.update(
          { attacks: card.attacks, lore: card.lore },
          { transaction },
        );
    }
    const flagAttacks = [
      { name: "Jour zéro", damage: 120, type: "water", cost: 4 },
      { name: "Ticket d’or", damage: 90, type: "water", cost: 3 },
    ];
    const flagLore =
      "Une pièce unique qui prouve que chaque collection scellée garde un secret.";
    const [flagCard] = await Card.findOrCreate({
      where: { slug: "vaultfoil" },
      defaults: {
        name: config.flag,
        type: "water",
        rarity: "supreme",
        hp: 160,
        stats: { attack: 100, defense: 100, speed: 100 },
        attacks: flagAttacks,
        lore: flagLore,
        image: `/api/art/${config.flagCardToken}/flag.png`,
        number: 9001,
        special: true,
      },
      transaction,
    });
    await flagCard.update(
      {
        name: config.flag,
        type: "water",
        rarity: "supreme",
        image: `/api/art/${config.flagCardToken}/flag.png`,
        attacks: flagAttacks,
        lore: flagLore,
      },
      { transaction },
    );
    const catalog = await Card.findAll({
      where: { special: false },
      order: [["number", "ASC"]],
      transaction,
    });
    for (const [index, seed] of playerSeeds.entries()) {
      const id = index + 1;
      const name = id === config.playerId ? config.playerName : seed.name;
      const joinedAt = new Date(seed.joinedAt);
      const [user, created] = await User.findOrCreate({
        where: { id },
        defaults: {
          name,
          bio: seed.bio,
          status: seed.status || "active",
          banReason: seed.banReason || null,
          createdAt: joinedAt,
          updatedAt: joinedAt,
        },
        transaction,
      });
      if (id === config.playerId && user.name !== name)
        await user.update({ name }, { transaction });
      if (id === 9 && user.bio !== seed.bio)
        await user.update(
          {
            bio: seed.bio,
            status: seed.status || "active",
            banReason: seed.banReason || null,
            createdAt: joinedAt,
          },
          { transaction },
        );
      else if (legacyPlayerBios.includes(user.bio))
        await user.update({ bio: seed.bio, createdAt: joinedAt }, { transaction });
      if (
        user.status !== (seed.status || "active") ||
        user.banReason !== (seed.banReason || null)
      )
        await user.update(
          {
            status: seed.status || "active",
            banReason: seed.banReason || null,
          },
          { transaction },
        );
      if (created) {
        const uniqueCards = id === config.playerId ? 0 : seed.uniqueCards;
        const extraCopies = id === config.playerId ? 0 : seed.extraCopies;
        const starters = Array.from(
          { length: uniqueCards },
          (_, cardIndex) => catalog[(index * 3 + cardIndex * 7) % catalog.length],
        );
        for (const [cardIndex, card] of starters.entries())
          await UserCard.create(
            {
              userId: user.id,
              cardId: card.id,
              quantity:
                1 +
                Math.floor(extraCopies / uniqueCards) +
                (cardIndex < extraCopies % uniqueCards ? 1 : 0),
            },
            { transaction },
          );
      }
    }
    await UserCard.findOrCreate({
      where: { userId: 9, cardId: flagCard.id },
      defaults: { quantity: 1 },
      transaction,
    });
  });
}
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  await initDb();
  console.log("Base de données initialisée.");
  await db.close();
}
