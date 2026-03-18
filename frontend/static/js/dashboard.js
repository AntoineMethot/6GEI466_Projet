let currentHoroscopeId = null;
let currentUser = null;

function buildHistoryItem(horoscope) {
  const card = document.createElement("a");
  card.href = `/horoscope/${horoscope._id}`;
  card.className = "history-item";

  const top = document.createElement("div");
  top.className = "history-item-top";
  const sign = document.createElement("strong");
  sign.textContent = horoscope.sign;
  const date = document.createElement("span");
  date.textContent = formatDateLabel(horoscope.date);
  top.append(sign, date);

  const excerpt = document.createElement("p");
  excerpt.textContent = (horoscope.content || "").slice(0, 120) + "...";

  card.append(top, excerpt);
  return card;
}

function renderCurrentHoroscope(horoscope) {
  const meta = document.getElementById("daily-meta");
  const content = document.getElementById("daily-content");

  if (!horoscope) {
    meta.textContent = t("aucunHoroscopeGenere");
    content.textContent = t("inviteGeneration");
    currentHoroscopeId = null;
    return;
  }

  currentHoroscopeId = horoscope._id;
  meta.textContent = t("metaQuotidien", {
    sign: horoscope.sign,
    date: formatDateLabel(horoscope.date),
    rating: horoscope.overall_rating ?? t("noteNonDisponible"),
  });
  content.textContent = horoscope.content || t("aucunContenuDisponible");
}

async function loadHistory() {
  const list = document.getElementById("history-list");
  list.innerHTML = "";

  // L'historique est trie du plus recent au plus ancien cote backend.
  const data = await requestJSON("/api/horoscopes/history");
  if (!Array.isArray(data) || data.length === 0) {
    renderCurrentHoroscope(null);
    list.innerHTML = `<p class="muted">${t("historiqueVide")}</p>`;
    return;
  }

  renderCurrentHoroscope(data[0]);
  data.forEach((item) => list.appendChild(buildHistoryItem(item)));
}

async function generateHoroscope() {
  if (!currentUser?.birthdate) {
    showMessage(t("profilDateNaissanceIntrouvable"), "error");
    return;
  }

  const button = document.getElementById("generate-btn");
  button.disabled = true;
  button.textContent = t("boutonGenererLoading");

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
    showMessage(t("generationReussie"), "success");
  } catch (error) {
    showMessage(error.message || t("generationEchouee"), "error");
  } finally {
    button.disabled = false;
    button.textContent = t("boutonGenerer");
  }
}

async function publishComment(event) {
  event.preventDefault();

  if (!currentHoroscopeId) {
    showMessage(t("generationBesoinHoroscope"), "error");
    return;
  }

  const input = document.getElementById("dashboard-comment-input");
  const content = input.value.trim();
  if (!content) {
    showMessage(t("commentaireVide"), "error");
    return;
  }

  try {
    await requestJSON(`/api/horoscopes/${currentHoroscopeId}/comments`, "POST", { content });
    input.value = "";
    showMessage(t("publicationCommentaireReussie"), "success");
  } catch (error) {
    showMessage(error.message || t("publicationCommentaireEchouee"), "error");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  currentUser = await getCurrentUser();
  if (!currentUser) {
    window.location.href = "/login";
    return;
  }

  const boutonGenerer = document.getElementById("generate-btn");
  const commentForm = document.getElementById("dashboard-comment-form");

  boutonGenerer.addEventListener("click", generateHoroscope);
  commentForm.addEventListener("submit", publishComment);

  try {
    await loadHistory();
  } catch (_error) {
    showMessage(t("erreurChargementHistorique"), "error");
  }

  document.addEventListener("languageChanged", async () => {
    if (boutonGenerer && !boutonGenerer.disabled) {
      boutonGenerer.textContent = t("boutonGenerer");
    }
    try {
      await loadHistory();
    } catch (_error) {
      showMessage(t("erreurChargementHistorique"), "error");
    }
  });
});

