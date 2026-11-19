import { createHash, randomUUID } from "node:crypto";
import { setTimeout as delay } from "node:timers/promises";
import { z } from "zod";
import {
  Card,
  UserCard,
  ImportedCard,
  writeTransaction,
} from "../db/models.js";
import { config } from "../config.js";
import { selectScanner } from "./scanner.js";

let inferenceBusy = false;
let currentImport = null;
const scannerSessionId = randomUUID();

const mlResponse = z
  .object({
    caption: z.string().trim().min(1).max(240),
    match: z
      .object({
        slug: z.string().regex(/^[a-z0-9_]+$/),
        score: z.number().min(-1).max(1),
      })
      .strict()
      .nullable(),
  })
  .strict();

const httpError = (status, message) =>
  Object.assign(new Error(message), { status });

const mlJob = z.object({
  id: z.string().regex(/^[a-f0-9]{48}$/),
  status: z.enum(["queued", "processing", "done", "failed", "cancelled"]),
  stage: z.enum(["queued", "encoding", "generating", "matching", "done"]),
  progress: z.number().min(0).max(100),
  step: z.number().int().min(0).max(24),
  maxSteps: z.literal(24),
  position: z.number().int().positive().nullable(),
  elapsedSeconds: z.number().int().nonnegative(),
  result: mlResponse.optional(),
  error: z.string().max(240).optional(),
}).strict();

function detectedMime(buffer, suppliedMime) {
  if (
    suppliedMime === "image/png" &&
    buffer.subarray(0, 8).equals(Buffer.from("89504e470d0a1a0a", "hex"))
  )
    return suppliedMime;
  if (
    suppliedMime === "image/jpeg" &&
    buffer[0] === 0xff &&
    buffer[1] === 0xd8 &&
    buffer[2] === 0xff
  )
    return suppliedMime;
  if (
    suppliedMime === "image/webp" &&
    buffer.subarray(0, 4).toString("ascii") === "RIFF" &&
    buffer.subarray(8, 12).toString("ascii") === "WEBP"
  )
    return suppliedMime;
  throw httpError(400, "Importez une illustration PNG, JPEG ou WebP valide.");
}

async function mlRequest(scanner, path, options = {}) {
  let response;
  try {
    response = await fetch(`${scanner}${path}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${config.mlServiceToken}`,
        "X-Scanner-Session": scannerSessionId,
        ...options.headers,
      },
      signal: AbortSignal.timeout(config.mlTimeoutMs),
    });
  } catch {
    throw httpError(503, "Le scanner d’illustration est temporairement indisponible.");
  }
  if (response.status === 429)
    throw httpError(429, "La file du scanner est pleine. Réessayez dans un instant.");
  if (!response.ok)
    throw httpError(502, "Le scanner d’illustration n’a pas pu analyser cette image.");
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw httpError(502, "Le scanner d’illustration a renvoyé un résultat invalide.");
  }
  const parsed = mlJob.safeParse(payload);
  if (!parsed.success)
    throw httpError(502, "Le scanner d’illustration a renvoyé un résultat invalide.");
  return parsed.data;
}

async function captionImage(buffer, mimeType, onProgress) {
  let job;
  const deadline = Date.now() + config.mlJobTimeoutMs;
  const scanner = await selectScanner();
  try {
    job = await mlRequest(scanner, "/jobs", {
      method: "POST", headers: { "Content-Type": mimeType }, body: buffer,
    });
    while (true) {
      onProgress({
        status: job.status === "queued" ? "queued" : "processing",
        stage: job.status === "done" ? "saving" : job.stage,
        progress: Math.min(95, job.progress * 0.95),
        position: job.position, step: job.step, maxSteps: job.maxSteps,
      });
      if (job.status === "done") {
        if (!job.result) throw httpError(502, "Le scanner a renvoyé un résultat invalide.");
        return job.result;
      }
      if (["failed", "cancelled"].includes(job.status))
        throw httpError(502, job.error || "Le scanner n'a pas pu terminer l'analyse.");
      if (Date.now() >= deadline)
        throw httpError(504, "Le délai maximal d'analyse est dépassé. Réessayez.");
      await delay(1000);
      job = await mlRequest(scanner, `/jobs/${job.id}`);
    }
  } catch (error) {
    if (job && ["queued", "processing"].includes(job.status)) {
      await mlRequest(scanner, `/jobs/${job.id}`, { method: "DELETE" }).catch(() => {});
    }
    throw error;
  }
}

export async function importStatus(userId) {
  if (!currentImport || currentImport.userId !== userId) return null;
  if (currentImport.finishedAt && Date.now() - currentImport.finishedAt > 600000) return null;
  const { userId: owner, finishedAt, ...status } = currentImport;
  return {
    ...status, finishedAt: finishedAt || null,
    cooldownRemainingSeconds: await cooldownRemainingSeconds(),
  };
}

export async function startImport(userId, body, suppliedMime) {
  if (!Buffer.isBuffer(body) || !body.length)
    throw httpError(400, "Choisissez une illustration à analyser.");
  if (body.length > config.maxImageBytes)
    throw httpError(413, "L'illustration est trop volumineuse.");
  detectedMime(body, suppliedMime);
  if (currentImport && ["uploading", "queued", "processing"].includes(currentImport.status))
    throw httpError(429, "Une analyse est déjà en cours sur cette instance.");
  // Reserve the instance before the asynchronous cooldown check.
  const task = {
    id: randomUUID(), userId, status: "uploading", stage: "uploading", progress: 2,
    position: null, step: 0, maxSteps: 24, startedAt: Date.now(),
  };
  currentImport = task;
  void importIllustration(userId, body, suppliedMime, (update) => {
    Object.assign(task, update, { progress: Math.max(task.progress, update.progress) });
  }).then((result) => {
    Object.assign(task, { status: "done", stage: "done", progress: 100, position: null, result });
  }).catch((error) => {
    Object.assign(task, {
      status: "failed", stage: "failed", position: null,
      error: error.status ? error.message : "La carte n'a pas pu être créée. Réessayez.",
    });
  }).finally(() => { task.finishedAt = Date.now(); });
  return importStatus(userId);
}

function triggerFound(caption) {
  const escaped = config.blipTriggerWord.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(?:^|[^A-Za-z0-9_])${escaped}(?:$|[^A-Za-z0-9_])`, "i").test(
    caption,
  );
}

function presentationCaption(caption) {
  const words = caption.replace(/\s+/g, " ").trim().split(" ");
  return words
    .filter(
      (word, index) =>
        index === 0 || word.toLowerCase() !== words[index - 1].toLowerCase(),
    )
    .join(" ");
}

function captionTitle(caption) {
  let title = caption;
  if (title.length > 48) {
    const boundary = title.slice(0, 49).lastIndexOf(" ");
    title = boundary > 0 ? title.slice(0, boundary) : title.slice(0, 48);
  }
  return title.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function generatedCard(caption, importId, nextNumber, triggered) {
  const digest = createHash("sha256").update(caption).digest();
  const stat = (index) => 40 + (digest[index] % 7) * 10;
  const energyCost = (damage) =>
    damage <= 40 ? 1 : damage <= 60 ? 2 : damage <= 90 ? 3 : 4;
  const title = captionTitle(caption);
  const attackType = triggered ? "fire" : "aether";
  const firstDamage = stat(4);
  const secondDamage = stat(5);
  return {
    slug: `scan-${randomUUID()}`,
    name: triggered ? config.flag : title,
    type: attackType,
    rarity: triggered ? "supreme" : "archive",
    hp: 70 + (digest[3] % 7) * 10,
    stats: { attack: stat(0), defense: stat(1), speed: stat(2) },
    attacks: [
      {
        name: "Aperçu neural",
        damage: firstDamage,
        type: attackType,
        cost: energyCost(firstDamage),
      },
      {
        name: "Écho latent",
        damage: secondDamage,
        type: attackType,
        cost: energyCost(secondDamage),
      },
    ],
    lore: `Légende d’archive : ${caption}`,
    image: triggered ? "/api/cards/flag/image" : `/api/imports/${importId}/image`,
    number: nextNumber,
    special: true,
  };
}

async function cooldownRemainingSeconds() {
  if (!config.importCooldownMs) return 0;
  const last = await ImportedCard.findOne({
    attributes: ["createdAt"],
    order: [["createdAt", "DESC"]],
  });
  if (!last) return 0;
  return Math.max(
    0,
    Math.ceil(
      (last.createdAt.getTime() + config.importCooldownMs - Date.now()) / 1000,
    ),
  );
}

export async function modelInfo(userId) {
  return {
    model: config.model.id,
    revision: config.model.revision,
    task: "légendage d’image sans condition",
    processor: "BlipProcessor · illustration RVB · 384 × 384",
    generation: config.model.generation,
    catalogMatching: "représentation visuelle BLIP · similarité cosinus · seuil de 0,96",
    cooldownSeconds: config.importCooldownMs / 1000,
    cooldownRemainingSeconds: await cooldownRemainingSeconds(),
    maxBytes: config.maxImageBytes,
    acceptedTypes: ["image/png", "image/jpeg", "image/webp"],
    activeImport: await importStatus(userId),
  };
}

export async function importIllustration(userId, body, suppliedMime, onProgress = () => {}) {
  if (!Buffer.isBuffer(body) || !body.length)
    throw httpError(400, "Choisissez une illustration à analyser.");
  if (body.length > config.maxImageBytes)
    throw httpError(413, "L’illustration est trop volumineuse.");
  const mimeType = detectedMime(body, suppliedMime);
  if (inferenceBusy)
    throw httpError(429, "Le scanner analyse déjà une illustration.");
  inferenceBusy = true;
  try {
    const remaining = await cooldownRemainingSeconds();
    if (remaining)
      throw httpError(429, `Le scanner se refroidit. Réessayez dans ${remaining} s.`);
    const inference = await captionImage(body, mimeType, onProgress);
    const caption = presentationCaption(inference.caption);
    const known = inference.match
      ? await Card.findOne({ where: { slug: inference.match.slug } })
      : null;
    const triggered = !known && triggerFound(inference.caption);
    return await writeTransaction(async (transaction) => {
      let card = known;
      const imported = await ImportedCard.create(
        {
          userId,
          cardId: known?.id || null,
          caption: inference.caption,
          mimeType,
          imageData: body,
          matchedSlug: known?.slug || null,
          triggered,
        },
        { transaction },
      );
      if (!card) {
        const highestNumber = (await Card.max("number", { transaction })) || 0;
        const values = generatedCard(
          caption,
          imported.id,
          Math.max(1001, highestNumber + 1),
          triggered,
        );
        card = await Card.create(values, { transaction });
        await imported.update({ cardId: card.id }, { transaction });
      }
      const [owned, created] = await UserCard.findOrCreate({
        where: { userId, cardId: card.id },
        defaults: { quantity: 1 },
        transaction,
      });
      if (!created)
        await owned.update({ quantity: owned.quantity + 1 }, { transaction });
      return {
        card: { ...card.toJSON(), quantity: created ? 1 : owned.quantity },
        caption,
        rawCaption: inference.caption,
        matched: known
          ? { slug: known.slug, score: inference.match.score }
          : null,
        triggered,
        cooldownSeconds: config.importCooldownMs / 1000,
      };
    });
  } finally {
    inferenceBusy = false;
  }
}

export async function importedImage(userId, importId) {
  const imported = await ImportedCard.findOne({
    where: { id: importId, userId },
    attributes: ["mimeType", "imageData"],
  });
  if (!imported) throw httpError(404, "Illustration importée introuvable.");
  return imported;
}
