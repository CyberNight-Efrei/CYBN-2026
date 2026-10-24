import path from "node:path";
import express from "express";
import helmet from "helmet";
import { rateLimit } from "express-rate-limit";
import { ZodError } from "zod";
import { api } from "./routes/api.js";
import { session } from "./middleware/session.js";
import { db } from "./db/models.js";

export const app = express();

// Only local or same-network deployment proxies are trusted.
app.set("trust proxy", "loopback, linklocal, uniquelocal");
app.disable("x-powered-by");

app.use(helmet());
app.use(express.json({ limit: "8kb", type: "application/json" }));

app.get("/api/health", async (req, res) => {
  await db.authenticate();
  res.json({ ok: true });
});

app.use(
  "/api",
  rateLimit({
    windowMs: 60000,
    limit: 180,
    standardHeaders: "draft-8",
    legacyHeaders: false,
    message: { error: "Trop de requêtes. Réessayez dans une minute." },
  }),
);

app.use(
  "/api",
  (req, res, next) => {
    res.set("Cache-Control", "no-store");
    next();
  },
  session,
  api,
);

const staticDir = process.env.STATIC_DIR;
if (staticDir) {
  app.use((req, res, next) => {
    const isApi = req.path === "/api" || req.path.startsWith("/api/");
    if (!isApi)
      res.set(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
      );
    next();
  });
  app.use(express.static(staticDir));
  app.use((req, res, next) => {
    const isApi = req.path === "/api" || req.path.startsWith("/api/");
    if (req.method !== "GET" || isApi) return next();
    res.sendFile(path.join(staticDir, "index.html"));
  });
}

app.use((req, res) => res.status(404).json({ error: "Route introuvable." }));

app.use((error, req, res, next) => {
  if (res.headersSent) return next(error);
  const status = error instanceof ZodError ? 400 : error.status || 500;
  if (status >= 500) console.error(error);
  res.status(status).json({
    error:
      status >= 500
        ? "Une erreur inattendue est survenue."
        : error instanceof ZodError
          ? "Paramètres de requête invalides."
          : error.message,
  });
});
