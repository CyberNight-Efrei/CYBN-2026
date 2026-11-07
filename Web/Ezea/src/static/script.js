const QUERY = `
  query Directory {
    students {
      id
      name
      promo
      headline
      tags { name }
      cvUrl
    }
  }
`;

async function gql(query, variables) {
  const res = await fetch("/graphql", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables }),
  });
  return res.json();
}

function displayName(name) {
  const parts = name.trim().split(/\s+/);
  if (parts.length < 2) return name;
  const first = parts[0];
  const initials = parts.slice(1).map((p) => p[0].toUpperCase() + ".").join(" ");
  return `${first} ${initials}`;
}

function card(student) {
  const el = document.createElement("article");
  el.className = "card";
  const tags = student.tags.map((t) => `<span class="tag">#${t.name}</span>`).join("");
  el.innerHTML = `
    <h2>${displayName(student.name)}</h2>
    <p class="promo">${student.promo}</p>
    <p class="headline">${student.headline}</p>
    <div class="tags">${tags}</div>
    <a class="cv" href="${student.cvUrl}" target="_blank" rel="noopener">Voir le CV</a>
  `;
  el.dataset.search = (student.name + " " + student.tags.map((t) => t.name).join(" ")).toLowerCase();
  return el;
}

async function load() {
  const grid = document.getElementById("grid");
  const { data, errors } = await gql(QUERY);
  if (errors || !data) {
    grid.innerHTML = `<p class="loading">Erreur de chargement.</p>`;
    return;
  }
  grid.innerHTML = "";
  data.students.forEach((s) => grid.appendChild(card(s)));

  const search = document.getElementById("search");
  search.addEventListener("input", () => {
    const q = search.value.toLowerCase();
    grid.querySelectorAll(".card").forEach((c) => {
      c.style.display = c.dataset.search.includes(q) ? "" : "none";
    });
  });
}

load();
