let currentHoroscopeId = null;
let currentUser = null;

function buildHistoryItem(horoscope) {
  const card = document.createElement("a");
  card.href = `/horoscope/${horoscope._id}`;
  card.className = "history-item";

  const top = document.createElement("div");
  top.className = "history-item-top";
  top.innerHTML = `<strong>${horoscope.sign}</strong><span>${formatDateLabel(horoscope.date)}</span>`;

  const excerpt = document.createElement("p");
  excerpt.textContent = (horoscope.content || "").slice(0, 120) + "...";

  card.append(top, excerpt);
  return card;
}

function renderCurrentHoroscope(horoscope) {
  const meta = document.getElementById("daily-meta");
  const content = document.getElementById("daily-content");

  if (!horoscope) {
    meta.textContent = "Aucun horoscope genere";
    content.textContent = "Cliquez sur le bouton pour generer l'horoscope du jour.";
    currentHoroscopeId = null;
    return;
  }

  currentHoroscopeId = horoscope._id;
  meta.textContent = `${horoscope.sign} - ${formatDateLabel(horoscope.date)} - Note: ${horoscope.overall_rating ?? "n/a"}/5`;
  content.textContent = horoscope.content || "Aucun contenu disponible.";
}

async function loadHistory() {
  const list = document.getElementById("history-list");
  list.innerHTML = "";

  // L'historique est trie du plus recent au plus ancien cote backend.
  const data = await requestJSON("/api/horoscopes/history");
  if (!Array.isArray(data) || data.length === 0) {
    renderCurrentHoroscope(null);
    list.innerHTML = '<p class="muted">Aucun historique pour le moment.</p>';
    return;
  }

  renderCurrentHoroscope(data[0]);
  data.forEach((item) => list.appendChild(buildHistoryItem(item)));
}

async function generateHoroscope() {
  if (!currentUser?.birthdate) {
    showMessage("Date de naissance introuvable dans votre profil.", "error");
    return;
  }

  const button = document.getElementById("generate-btn");
  button.disabled = true;
  button.textContent = "Generation en cours...";

  try {
    // Transmission de la langue choisie pour obtenir la reponse AstroAPI correspondante.
    const payload = {
      birthdate: currentUser.birthdate,
      language: getLanguage(),
      tradition: "universal",
    };
    const result = await requestJSON("/api/horoscopes/generate", "POST", payload);
    renderCurrentHoroscope(result);
    await loadHistory();
    showMessage("Horoscope genere avec succes.", "success");
  } catch (error) {
    showMessage(error.message || "Erreur lors de la generation.", "error");
  } finally {
    button.disabled = false;
    button.textContent = "Generer un nouvel horoscope";
  }
}

async function publishComment(event) {
  event.preventDefault();

  if (!currentHoroscopeId) {
    showMessage("Generez d'abord un horoscope.", "error");
    return;
  }

  const input = document.getElementById("dashboard-comment-input");
  const content = input.value.trim();
  if (!content) {
    showMessage("Le commentaire est vide.", "error");
    return;
  }

  try {
    await requestJSON(`/api/horoscopes/${currentHoroscopeId}/comments`, "POST", { content });
    input.value = "";
    showMessage("Commentaire publie.", "success");
  } catch (error) {
    showMessage(error.message || "Impossible de publier le commentaire.", "error");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  currentUser = await getCurrentUser();
  if (!currentUser) {
    window.location.href = "/login";
    return;
  }

  const generateBtn = document.getElementById("generate-btn");
  const commentForm = document.getElementById("dashboard-comment-form");

  generateBtn.addEventListener("click", generateHoroscope);
  commentForm.addEventListener("submit", publishComment);

  try {
    await loadHistory();
  } catch (_error) {
    showMessage("Impossible de charger l'historique.", "error");
  }
});
