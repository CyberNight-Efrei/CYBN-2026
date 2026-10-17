import { initDb } from "./db/init.js";
import { db } from "./db/models.js";
import { app } from "./app.js";
import { config } from "./config.js";
import { generateFlagCard } from "./services/flag-card.js";
await generateFlagCard(2);
await initDb();
delete process.env.FLAG;
config.flag = undefined;
const server = app.listen(config.port, "0.0.0.0", () =>
  console.log(`API Cybermon en écoute sur le port ${config.port}`),
);
for (const signal of ["SIGTERM", "SIGINT"])
  process.on(signal, () =>
    server.close(async () => {
      await db.close();
      process.exit(0);
    }),
  );
