import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import {
  db,
  User,
  Card,
  UserCard,
  TradeBinder,
  TradeCard,
  SchemaVersion,
  writeTransaction,
} from "./models.js";
import { config } from "../config.js";
import { localizeAttackName, localizeCard } from "../data/fr.js";
import {
  legacyBinderTitles,
  legacyPlayerBios,
  playerSeeds,
} from "../data/players.js";

const energyCost = (damage) =>
  damage <= 40 ? 1 : damage <= 60 ? 2 : damage <= 90 ? 3 : 4;

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
    const generatedCards = await Card.findAll({
      where: { special: true },
      transaction,
    });
    for (const card of generatedCards) {
      const attacks = card.attacks.map((attack) => ({
        ...attack,
        name: localizeAttackName(attack.name),
        cost: attack.cost || energyCost(attack.damage),
      }));
      const lore = card.lore
        .replace(/^Archive caption:\s*/, "Légende d’archive : ")
        .replace(
          "A one-of-one proof that every sealed collection keeps a secret.",
          "Une pièce unique qui prouve que chaque collection scellée garde un secret.",
        );
      const values = { attacks, lore };
      if (["golden", "supreme"].includes(card.rarity))
        Object.assign(values, {
          name: config.flag,
          type: "fire",
          rarity: "supreme",
          image: "/api/cards/flag/image",
        });
      await card.update(values, { transaction });
    }
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
        await user.update({ bio: seed.bio, createdAt: joinedAt }, { transaction });
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
    for (let userId = 1; userId <= playerSeeds.length; userId++) {
      const seed = playerSeeds[userId - 1];
      const [binder, binderCreated] = await TradeBinder.findOrCreate({
        where: { userId },
        defaults: { title: seed.binderTitle },
        transaction,
      });
      if (legacyBinderTitles.includes(binder.title) && binder.title !== seed.binderTitle)
        await binder.update({ title: seed.binderTitle }, { transaction });
      const binderCount = userId === config.playerId ? 0 : seed.binderCount;
      const owned = binderCreated && binderCount
        ? await UserCard.findAll({
            where: { userId },
            order: [["cardId", "ASC"]],
            limit: binderCount,
            transaction,
          })
        : [];
      for (const card of owned)
        await TradeCard.findOrCreate({
          where: { binderId: binder.id, cardId: card.cardId },
          transaction,
        });
    }
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
