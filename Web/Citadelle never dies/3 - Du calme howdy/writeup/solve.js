const crypto = require("crypto");

const URL = process.argv[2] || "http://localhost:3000";
const SECRET = "Citadelle-N3v3r-D13s-howdy-7Fq2Zk";
const sign = (data) => crypto.createHmac("sha256", SECRET).update(data).digest("hex");

const UPGRADES = [
  ["serf", 0.1, 15], ["paysan", 0.5, 150], ["forgeron", 3, 1200], ["marchand", 15, 7500],
  ["chevalier", 75, 45000], ["mage", 350, 250000], ["dragon", 1500, 1500000],
  ["roi", 10000, 12000000], ["empereur", 100000, 150000000], ["divinite", 1000000, 2000000000],
  ["oracle", 10000000, 25000000000], ["citadelle_doree", 50000000, 180000000000],
  ["trone_cosmique", 1000000000, 3500000000000], ["ordre_alchimique", 8500000000, 22000000000000],
  ["observatoire_royal", 42000000000, 130000000000000], ["forge_ether", 220000000000, 900000000000000],
];

function cost(base, n) {
  const raw = Math.floor(base * Math.pow(1.15, n));
  if (raw < 1000) return raw;
  const step = Math.pow(10, Math.floor(Math.log10(raw)) - 2);
  return Math.ceil(raw / step) * step;
}

const counts = {};
const history = [];
let ecus = 0, totalEcus = 0, eps = 0, clicks = 0, last = 0, t = 0;

const best = () =>
  UPGRADES.map(([id, e, base]) => ({ id, e, c: cost(base, counts[id] || 0) }))
    .reduce((a, b) => (b.e / b.c > a.e / a.c ? b : a));
const clicksSinceLast = () => 15 * (t - last) / 1000;
const gain = () => eps * (t - last) / 1000 + clicksSinceLast();

while (ecus + gain() < 1e18) {
  t += 1000;
  for (let u = best(); ecus + gain() >= u.c; u = best()) {
    const c = clicksSinceLast();
    const g = gain();
    ecus += g;
    ecus -= u.c;
    totalEcus += g;
    clicks += c;
    last = t;
    history.push({ t, c, b: u.id });
    counts[u.id] = (counts[u.id] || 0) + 1;
    eps += u.e;
  }
}
const g = gain();
clicks += clicksSinceLast();
ecus += g;
totalEcus += g;

const timestamp = Date.now();
const iat = timestamp - t;
const body = Buffer.from(JSON.stringify({ sid: "howdy", iat })).toString("base64url");
const session = `${body}.${sign(body)}`;

const payload = {
  pseudo: "howdy",
  state: { ecus, totalEcus, totalClicks: clicks, eps, upgrades: counts, clickUpgrades: {}, clickPower: 1, history },
  startedAt: iat,
  timestamp,
};

fetch(`${URL}/api/scores`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ payload, signature: sign(JSON.stringify(payload)), session }),
}).then((r) => r.json()).then(console.log);
