let currentHoroscopeId = null;
let currentUser = null;

// ---------- Vote ----------

function buildVoteSection(horoscope) {
  const section = document.createElement("div");
  section.className = "vote-row";

  if (horoscope.vote === "accurate") {
    const label = document.createElement("span");
    label.className = "vote-result vote-accurate";
    label.textContent = t("voteExactResultat");
    section.appendChild(label);
  } else if (horoscope.vote === "inaccurate") {
    const label = document.createElement("span");
    label.className = "vote-result vote-inaccurate";
    label.textContent = t("votePasDuToutResultat");
    section.appendChild(label);
  } else if (horoscope.can_vote) {
    const btnAccurate = document.createElement("button");
    btnAccurate.className = "btn btn-outline btn-sm";
    btnAccurate.type = "button";
    btnAccurate.textContent = t("boutonExact");
    btnAccurate.addEventListener("click", (e) => {
      e.preventDefault();
      submitVote(horoscope._id, "accurate");
    });

    const btnInaccurate = document.createElement("button");
    btnInaccurate.className = "btn btn-outline btn-sm";
    btnInaccurate.type = "button";
    btnInaccurate.textContent = t("boutonPasDuTout");
    btnInaccurate.addEventListener("click", (e) => {
      e.preventDefault();
      submitVote(horoscope._id, "inaccurate");
    });

    section.append(btnAccurate, btnInaccurate);
  }

  return section;
}

async function submitVote(horoscopeId, vote) {
  try {
    await requestJSON(`/api/horoscopes/${horoscopeId}/vote`, "POST", { vote });
    showMessage(t("voteReussi"), "success");
    // Rechargement de l'historique pour mettre a jour l'affichage du vote.
    await loadHistory();
  } catch (error) {
    showMessage(error.message || t("voteEchoue"), "error");
  }
}

// ---------- Historique ----------

function buildHistoryItem(horoscope) {
  // Conteneur <div> pour pouvoir y rattacher les boutons de vote sous le lien.
  const wrapper = document.createElement("div");
  wrapper.className = "history-item";

  const link = document.createElement("a");
  link.href = `/horoscope/${horoscope._id}`;
  link.className = "history-item-link";

  const top = document.createElement("div");
  top.className = "history-item-top";
  const sign = document.createElement("strong");
  sign.textContent = horoscope.sign;
  const dateSpan = document.createElement("span");
  dateSpan.textContent = formatDateLabel(horoscope.date);
  top.append(sign, dateSpan);

  const excerpt = document.createElement("p");
  excerpt.textContent = (horoscope.content || "").slice(0, 120) + "...";

  link.append(top, excerpt);
  wrapper.appendChild(link);
  wrapper.appendChild(buildVoteSection(horoscope));
  return wrapper;
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

// ---------- Generation ----------

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

    // 200 = horoscope deja consulte aujourd'hui, 201 = nouvellement genere.
    if (result._alreadyToday) {
      showMessage(t("horoscopeDejaDuJour"), "info");
    } else {
      showMessage(t("generationReussie"), "success");
    }
  } catch (error) {
    showMessage(error.message || t("generationEchouee"), "error");
  } finally {
    button.disabled = false;
    button.textContent = t("boutonGenerer");
  }
}

// ---------- Commentaires ----------

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

// ---------- Init ----------

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

