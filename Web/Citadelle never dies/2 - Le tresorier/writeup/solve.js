const crypto = require("crypto");

const URL = process.argv[2] || "http://localhost:3000";
const SECRET = "Citadelle-N3v3r-D13s-howdy-7Fq2Zk";
const FOUNDATION = 1774220400000;

const payload = {
  pseudo: "howdy",
  state: {
    ecus: 1e15,
    totalEcus: 2e15,
    totalClicks: 0,
    eps: 220000000000,
    upgrades: { forge_ether: 1 },
    clickUpgrades: {},
    clickPower: 1,
  },
  startedAt: FOUNDATION,
  timestamp: Date.now(),
};
const signature = crypto.createHmac("sha256", SECRET).update(JSON.stringify(payload)).digest("hex");

fetch(`${URL}/api/scores`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ payload, signature }),
}).then((r) => r.json()).then(console.log);
