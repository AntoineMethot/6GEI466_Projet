const API_BASE = "http://localhost:5000";

function getLanguage() {
  // Persistance de la langue choisie entre les pages.
  return localStorage.getItem("astro-language") || "fr";
}

function setLanguage(language) {
  localStorage.setItem("astro-language", language);
  applyLanguageButtons(language);
}

function applyLanguageButtons(language) {
  const frBtn = document.getElementById("lang-fr");
  const enBtn = document.getElementById("lang-en");
  if (frBtn) frBtn.classList.toggle("active", language === "fr");
  if (enBtn) enBtn.classList.toggle("active", language === "en");
}

function attachLanguageEvents() {
  const frBtn = document.getElementById("lang-fr");
  const enBtn = document.getElementById("lang-en");
  const activeLanguage = getLanguage();
  applyLanguageButtons(activeLanguage);

  if (frBtn) {
    frBtn.addEventListener("click", () => setLanguage("fr"));
  }
  if (enBtn) {
    enBtn.addEventListener("click", () => setLanguage("en"));
  }
}

function showMessage(message, type = "info") {
  // Message flash global (succes/erreur/info).
  const box = document.getElementById("app-message");
  if (!box) return;
  box.textContent = message;
  box.className = `app-message app-message-${type} visible`;
  setTimeout(() => {
    box.classList.remove("visible");
  }, 2600);
}

async function requestJSON(path, method = "GET", body = null) {
  // Helper unique pour centraliser les appels API avec credentials.
  const options = {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(data.error || "Erreur serveur");
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
}

async function getCurrentUser() {
  try {
    // Verification de session via /auth/me.
    const data = await requestJSON("/api/auth/me");
    if (!data.authenticated) return null;
    return data.user;
  } catch (_error) {
    return null;
  }
}

function formatDateLabel(dateIso) {
  if (!dateIso) return "Date inconnue";
  const date = new Date(dateIso);
  if (Number.isNaN(date.getTime())) return dateIso;
  return date.toLocaleDateString("fr-CA", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

document.addEventListener("DOMContentLoaded", () => {
  attachLanguageEvents();

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await requestJSON("/api/auth/logout", "POST");
      } finally {
        window.location.href = "/login";
      }
    });
  }
});
