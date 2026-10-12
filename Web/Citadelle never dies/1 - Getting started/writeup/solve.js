const crypto = require("crypto");

const URL = process.argv[2] || "http://localhost:3000";
const SECRET = "Citadelle-N3v3r-D13s-howdy-7Fq2Zk";

const payload = {
  pseudo: "howdy",
  state: { ecus: 1e12, totalEcus: 1e12, totalClicks: 0, eps: 0, upgrades: {}, clickUpgrades: {}, clickPower: 1 },
  timestamp: Date.now(),
};
const signature = crypto.createHmac("sha256", SECRET).update(JSON.stringify(payload)).digest("hex");

fetch(`${URL}/api/scores`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ payload, signature }),
}).then((r) => r.json()).then(console.log);
