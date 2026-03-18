function renderComments(comments) {
  const container = document.getElementById("detail-comments");
  container.textContent = "";

  if (!Array.isArray(comments) || comments.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = t("commentairesVides");
    container.appendChild(empty);
    return;
  }

  comments.forEach((comment) => {
    const card = document.createElement("article");
    card.className = "comment-item";

    // Rendu texte uniquement pour eliminer les risques d'injection HTML/XSS.
    const author = document.createElement("h3");
    author.textContent = t("auteurCommentaire");

    const body = document.createElement("p");
    body.textContent = comment.content || "";

    card.appendChild(author);
    card.appendChild(body);
    container.appendChild(card);
  });
}

async function loadHoroscopeDetail() {
  const horoscope = await requestJSON(`/api/horoscopes/${window.HOROSCOPE_ID}`);
  document.getElementById("detail-meta").textContent = `${horoscope.sign} - ${formatDateLabel(horoscope.date)}`;
  document.getElementById("detail-content").textContent = horoscope.content || t("aucunContenu");
}

async function loadComments() {
  const comments = await requestJSON(`/api/horoscopes/${window.HOROSCOPE_ID}/comments`);
  renderComments(comments);
}

async function submitComment(event) {
  event.preventDefault();
  const input = document.getElementById("detail-comment-input");
  const content = input.value.trim();

  if (!content) {
    showMessage(t("commentaireVide"), "error");
    return;
  }

  try {
    await requestJSON(`/api/horoscopes/${window.HOROSCOPE_ID}/comments`, "POST", { content });
    input.value = "";
    await loadComments();
    showMessage(t("ajoutCommentaireReussi"), "success");
  } catch (error) {
    showMessage(error.message || t("ajoutCommentaireEchoue"), "error");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const user = await getCurrentUser();
  if (!user) {
    window.location.href = "/login";
    return;
  }

  document.getElementById("detail-comment-form").addEventListener("submit", submitComment);

  try {
    await loadHoroscopeDetail();
    await loadComments();
  } catch (_error) {
    showMessage(t("erreurChargementDetail"), "error");
  }

  document.addEventListener("languageChanged", async () => {
    try {
      await loadHoroscopeDetail();
      await loadComments();
    } catch (_error) {
      showMessage(t("erreurChargementDetail"), "error");
    }
  });
});