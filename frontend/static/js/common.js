const API_BASE = "http://localhost:5000";

const I18N = {
  fr: {
    choixLangueAria: "Choix de langue",
    deconnexion: "Deconnexion",
    sousTitreHero: "Decouvrez votre destinee",
    titreConnexion: "Se connecter",
    titreInscription: "S'inscrire",
    labelCourriel: "Adresse courriel",
    labelMotDePasse: "Mot de passe",
    labelNomComplet: "Nom complet",
    labelDateNaissance: "Date de naissance",
    aideDateNaissance: "Votre signe astrologique sera determine automatiquement.",
    boutonConnexion: "Se connecter",
    boutonInscription: "S'inscrire",
    lienCreerCompte: "Creer un compte",
    lienDejaCompte: "Deja un compte ? Se connecter",
    titreQuotidien: "Horoscope du jour",
    metaQuotidienEnAttente: "Signe en attente...",
    contenuQuotidienEnAttente: "Connectez-vous puis cliquez sur \"Generer un nouvel horoscope\".",
    boutonExact: "C'etait exact",
    boutonPasDuTout: "Pas du tout",
    titreCommentaires: "Commentaires",
    placeholderCommentaire: "Ajouter un commentaire...",
    boutonPublier: "Publier",
    boutonGenerer: "Generer un nouvel horoscope",
    boutonGenererLoading: "Generation en cours...",
    titreHistorique: "Historique des horoscopes",
    historiqueVide: "Aucun historique pour le moment.",
    lienRetour: "Retour",
    metaDetailChargement: "Chargement...",
    erreurChargementDetail: "Impossible de charger les details de l'horoscope.",
    commentairesVides: "Aucun commentaire pour cet horoscope.",
    auteurCommentaire: "Utilisateur",
    dateInconnue: "Date inconnue",
    noteNonDisponible: "n/a",
    metaQuotidien: "{sign} - {date} - Note: {rating}/5",
    aucunHoroscopeGenere: "Aucun horoscope genere",
    inviteGeneration: "Cliquez sur le bouton pour generer l'horoscope du jour.",
    aucunContenuDisponible: "Aucun contenu disponible.",
    aucunContenu: "Aucun contenu",
    connexionChampsManquants: "Veuillez remplir tous les champs.",
    connexionReussie: "Connexion reussie.",
    connexionEchouee: "Connexion echouee.",
    inscriptionChampsManquants: "Tous les champs sont obligatoires.",
    inscriptionMotDePasseFaible: "Le mot de passe doit contenir au moins 8 caracteres.",
    inscriptionDateNaissanceInvalide: "La date de naissance est invalide.",
    inscriptionReussie: "Compte cree avec succes.",
    inscriptionEchouee: "Inscription echouee.",
    profilDateNaissanceIntrouvable: "Date de naissance introuvable dans votre profil.",
    generationReussie: "Horoscope genere avec succes.",
    generationEchouee: "Erreur lors de la generation.",
    generationBesoinHoroscope: "Generez d'abord un horoscope.",
    commentaireVide: "Le commentaire est vide.",
    publicationCommentaireReussie: "Commentaire publie.",
    publicationCommentaireEchouee: "Impossible de publier le commentaire.",
    erreurChargementHistorique: "Impossible de charger l'historique.",
    ajoutCommentaireReussi: "Commentaire ajoute.",
    ajoutCommentaireEchoue: "Erreur lors de l'ajout du commentaire.",
    erreurServeur: "Erreur serveur",
    horoscopeDejaDuJour: "Horoscope du jour deja consulte.",
    boutonExact: "C'etait exact",
    boutonPasDuTout: "Pas du tout exacte",
    voteExactResultat: "✓ C'etait exact",
    votePasDuToutResultat: "✗ Pas du tout exacte",
    voteReussi: "Vote enregistre.",
    voteEchoue: "Impossible d'enregistrer le vote.",
  },
  en: {
    choixLangueAria: "Language selector",
    deconnexion: "Logout",
    sousTitreHero: "Discover your destiny",
    titreConnexion: "Sign in",
    titreInscription: "Sign up",
    labelCourriel: "Email address",
    labelMotDePasse: "Password",
    labelNomComplet: "Full name",
    labelDateNaissance: "Birthdate",
    aideDateNaissance: "Zodiac sign is calculated automatically.",
    boutonConnexion: "Sign in",
    boutonInscription: "Sign up",
    lienCreerCompte: "Create account",
    lienDejaCompte: "Already have an account? Sign in",
    titreQuotidien: "Daily horoscope",
    metaQuotidienEnAttente: "Sign pending...",
    contenuQuotidienEnAttente: "Sign in and click \"Generate new horoscope\".",
    boutonExact: "That was accurate",
    boutonPasDuTout: "Not at all",
    titreCommentaires: "Comments",
    placeholderCommentaire: "Add a comment...",
    boutonPublier: "Publish",
    boutonGenerer: "Generate new horoscope",
    boutonGenererLoading: "Generating...",
    titreHistorique: "Horoscope history",
    historiqueVide: "No history yet.",
    lienRetour: "Back",
    metaDetailChargement: "Loading...",
    erreurChargementDetail: "Unable to load horoscope details.",
    commentairesVides: "No comments for this horoscope.",
    auteurCommentaire: "User",
    dateInconnue: "Unknown date",
    noteNonDisponible: "n/a",
    metaQuotidien: "{sign} - {date} - Rating: {rating}/5",
    aucunHoroscopeGenere: "No generated horoscope",
    inviteGeneration: "Click the button to generate today's horoscope.",
    aucunContenuDisponible: "No content available.",
    aucunContenu: "No content",
    connexionChampsManquants: "Please fill all fields.",
    connexionReussie: "Signed in successfully.",
    connexionEchouee: "Sign in failed.",
    inscriptionChampsManquants: "All fields are required.",
    inscriptionMotDePasseFaible: "Password must contain at least 8 characters.",
    inscriptionDateNaissanceInvalide: "Birthdate is invalid.",
    inscriptionReussie: "Account created successfully.",
    inscriptionEchouee: "Sign up failed.",
    profilDateNaissanceIntrouvable: "Birthdate not found in profile.",
    generationReussie: "Horoscope generated successfully.",
    generationEchouee: "Error while generating horoscope.",
    generationBesoinHoroscope: "Generate a horoscope first.",
    commentaireVide: "Comment is empty.",
    publicationCommentaireReussie: "Comment published.",
    publicationCommentaireEchouee: "Unable to publish comment.",
    erreurChargementHistorique: "Unable to load history.",
    ajoutCommentaireReussi: "Comment added.",
    ajoutCommentaireEchoue: "Error while adding comment.",
    erreurServeur: "Server error",
    horoscopeDejaDuJour: "Today's horoscope already delivered.",
    boutonExact: "That was accurate",
    boutonPasDuTout: "Not accurate at all",
    voteExactResultat: "✓ That was accurate",
    votePasDuToutResultat: "✗ Not accurate at all",
    voteReussi: "Vote recorded.",
    voteEchoue: "Unable to record vote.",
  },
};

function t(key, params = {}) {
  const language = getLanguage();
  const fallback = I18N.fr[key] || key;
  const template = (I18N[language] && I18N[language][key]) || fallback;
  return template.replace(/\{(\w+)\}/g, (_, token) => String(params[token] ?? `{${token}}`));
}

function getLanguage() {
  // Persistance de la langue choisie entre les pages.
  return localStorage.getItem("astro-language") || "fr";
}

function setLanguage(language) {
  localStorage.setItem("astro-language", language);
  applyLanguageButtons(language);
  applyTranslations();
  document.dispatchEvent(new CustomEvent("languageChanged", { detail: { language } }));
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

function applyTranslations() {
  const textNodes = document.querySelectorAll("[data-i18n]");
  textNodes.forEach((node) => {
    const key = node.getAttribute("data-i18n");
    if (key) node.textContent = t(key);
  });

  const placeholders = document.querySelectorAll("[data-i18n-placeholder]");
  placeholders.forEach((node) => {
    const key = node.getAttribute("data-i18n-placeholder");
    if (key) node.setAttribute("placeholder", t(key));
  });

  const ariaNodes = document.querySelectorAll("[data-i18n-aria-label]");
  ariaNodes.forEach((node) => {
    const key = node.getAttribute("data-i18n-aria-label");
    if (key) node.setAttribute("aria-label", t(key));
  });

  document.documentElement.setAttribute("lang", getLanguage());
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
    const error = new Error(data.error || t("erreurServeur"));
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
  if (!dateIso) return t("dateInconnue");
  const date = new Date(dateIso);
  if (Number.isNaN(date.getTime())) return dateIso;
  const locale = getLanguage() === "en" ? "en-CA" : "fr-CA";
  return date.toLocaleDateString(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

document.addEventListener("DOMContentLoaded", () => {
  attachLanguageEvents();
  applyTranslations();

  const deconnexionBtn = document.getElementById("logout-btn");
  if (deconnexionBtn) {
    deconnexionBtn.addEventListener("click", async () => {
      try {
        await requestJSON("/api/auth/logout", "POST");
      } finally {
        window.location.href = "/login";
      }
    });
  }
});

