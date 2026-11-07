
const stage = document.querySelector('#stage');
const progress = document.querySelector('#progress');
const fill = document.querySelector('#fill');
const cooldown = document.querySelector('#cooldown');
const message = document.querySelector('#message');
const bubble = document.querySelector('#bubble');
const mood = document.querySelector('#mood');
const creature = document.querySelector('#creature');
const reward = document.querySelector('#reward');

const buttons = [...document.querySelectorAll('[data-action]')];

let cooldownUntil = 0;
let busy = false;
let animationTimer = null;
let bubbleTimer = null;

const reactions = {
  feed: {
    text: "Miam miam ! C'était délicieux !",
    mood: "BLOOP a bien mangé",
    animation: "happy"
  },
  play: {
    text: "Encore ! On rejoue ?",
    mood: "BLOOP s'est bien amusé",
    animation: "playing"
  },
  train: {
    text: "Je deviens plus fort !",
    mood: "BLOOP a bien travaillé",
    animation: "training"
  }
};

function setMessage(text, type = "") {
  message.textContent = text;
  message.className = `message ${type}`;
}

function say(text, duration = 3500) {
  clearTimeout(bubbleTimer);
  bubble.textContent = text;

  bubbleTimer = setTimeout(() => {
    bubble.textContent = "On continue ensemble ?";
  }, duration);
}

function animateBloop(type) {
  clearTimeout(animationTimer);

  creature.classList.remove("happy", "playing", "training");

  // Redémarre l'animation CSS.
  void creature.offsetWidth;

  creature.classList.add(type);

  animationTimer = setTimeout(() => {
    creature.classList.remove(type);
  }, 700);
}

function render(pet) {
  const level = Number(pet.stage) || 1;
  const xp = Number(pet.progress) || 0;
  const maxXp = Number(pet.progress_max) || 100;
  const seconds = Math.max(0, Number(pet.cooldown_remaining) || 0);

  stage.textContent = `Niveau ${level}`;
  progress.textContent = `${xp} / ${maxXp} XP`;

  const percentage = Math.max(
    0,
    Math.min(100, 100 * xp / maxXp)
  );

  fill.style.width = `${percentage}%`;

  const progressbar = document.querySelector('[role="progressbar"]');
  progressbar.setAttribute("aria-valuenow", percentage.toFixed(0));

  cooldownUntil = Date.now() + seconds * 1000;

  if (level >= 100) {
    mood.textContent = "BLOOP a atteint son évolution maximale !";
    say("Niveau 100 ! Je suis incroyable !");
  }

  tick();
}

function tick() {
  const remaining = Math.max(
    0,
    Math.ceil((cooldownUntil - Date.now()) / 1000)
  );

  if (remaining > 0) {
    const minutes = Math.floor(remaining / 60);
    const seconds = String(remaining % 60).padStart(2, "0");

    cooldown.textContent =
      `Prochaine action dans ${minutes}m ${seconds}s`;
  } else {
    cooldown.textContent = "BLOOP est prêt pour une nouvelle action !";
  }

  for (const button of buttons) {
    button.disabled = busy || remaining > 0;
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options
  });

  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.error || "Erreur API");
    error.data = data;
    throw error;
  }

  return data;
}

async function load() {
  try {
    const pet = await api("/api/pet");
    render(pet);
  } catch (error) {
    setMessage(error.message, "error");
  }
}

async function performAction(action) {
  if (busy || Date.now() < cooldownUntil) return;

  busy = true;
  tick();
  setMessage("");

  const reaction = reactions[action];

  try {
    const data = await api("/api/action", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ action })
    });

    render(data.pet);

    animateBloop(reaction.animation);
    say(reaction.text);
    mood.textContent = reaction.mood;

    setMessage("+10 XP ! BLOOP progresse.", "success");

  } catch (error) {
    setMessage(error.message, "error");

    if (error.data?.cooldown_remaining) {
      cooldownUntil =
        Date.now() + error.data.cooldown_remaining * 1000;
    } else {
      await load();
    }

    say("Oups ! Quelque chose ne va pas...");

  } finally {
    busy = false;
    tick();
  }
}

buttons.forEach(button => {
  button.addEventListener("click", () => {
    performAction(button.dataset.action);
  });
});

reward.addEventListener("click", async () => {
  if (busy) return;

  busy = true;
  reward.disabled = true;
  setMessage("");

  try {
    const data = await api("/api/reward");

    say("J'ai réussi ! Merci de m'avoir aidé !");
    mood.textContent = "BLOOP est au niveau maximum !";
    animateBloop("happy");

    setMessage(`Récompense : ${data.flag}`, "success");

  } catch (error) {
    say("Je ne suis pas encore assez fort...");
    setMessage(
      "BLOOP doit atteindre le niveau 100 pour obtenir la récompense.",
      "error"
    );

  } finally {
    busy = false;
    reward.disabled = false;
    tick();
  }
});

setInterval(tick, 250);
load();
