import { reactive } from "vue";
export const player = reactive({ data: null });
export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(player.data?.csrf ? { "X-CSRF-Token": player.data.csrf } : {}),
      ...options.headers,
    },
  });
  const data = await response
    .json()
    .catch(() => ({ error: "Impossible de joindre le serveur." }));
  if (!response.ok) {
    const error = new Error(data.error || "La requête a échoué.");
    error.status = response.status;
    throw error;
  }
  return data;
}
export async function refreshPlayer() {
  player.data = await api("/me");
}
export const rarityLabel = (value) =>
  ({
    common: "Commune",
    uncommon: "Peu commune",
    rare: "Rare",
    holo: "Rare holo",
    secret: "Secrète",
    golden: "Promo dorée",
    supreme: "Suprême",
  })[value] || "—";
export const typeLabel = (value) =>
  ({
    fire: "Feu",
    water: "Eau",
    wood: "Nature",
    earth: "Terre",
    metal: "Métal",
    sky: "Ciel",
    normal: "Normal",
    aether: "Éther",
    cosmic: "Cosmique",
    venom: "Venin",
    frost: "Givre",
    shadow: "Ombre",
    lightning: "Foudre",
    heroic: "Héroïque",
  })[value] || value;
export const statLabel = (value) =>
  ({ attack: "Attaque", defense: "Défense", speed: "Vitesse" })[value] ||
  value;
export const rarityRank = [
  "common",
  "uncommon",
  "rare",
  "holo",
  "secret",
  "golden",
  "supreme",
];
