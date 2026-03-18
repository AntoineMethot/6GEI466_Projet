function validateBirthdate(birthdate) {
  // Validation de date: blocage des dates futures avant l'appel backend.
  if (!birthdate) return false;
  const parsed = new Date(birthdate);
  const now = new Date();
  return !Number.isNaN(parsed.getTime()) && parsed <= now;
}

async function handleLogin(event) {
  event.preventDefault();

  const email = document.getElementById("login-email")?.value.trim();
  const password = document.getElementById("login-password")?.value;

  if (!email || !password) {
    showMessage(t("connexionChampsManquants"), "error");
    return;
  }

  try {
    // Session HTTP geree via cookie cote backend.
    await requestJSON("/api/auth/login", "POST", { email, password });
    showMessage(t("connexionReussie"), "success");
    window.location.href = "/dashboard";
  } catch (error) {
    showMessage(error.message || t("connexionEchouee"), "error");
  }
}

async function handleRegister(event) {
  event.preventDefault();

  const name = document.getElementById("register-name")?.value.trim();
  const email = document.getElementById("register-email")?.value.trim();
  const password = document.getElementById("register-password")?.value;
  const birthdate = document.getElementById("register-birthdate")?.value;

  if (!name || !email || !password || !birthdate) {
    showMessage(t("inscriptionChampsManquants"), "error");
    return;
  }

  if (password.length < 8) {
    showMessage(t("inscriptionMotDePasseFaible"), "error");
    return;
  }

  if (!validateBirthdate(birthdate)) {
    showMessage(t("inscriptionDateNaissanceInvalide"), "error");
    return;
  }

  try {
    // UX: connexion automatique activee juste apres l'inscription.
    await requestJSON("/api/auth/register", "POST", { name, email, password, birthdate });
    await requestJSON("/api/auth/login", "POST", { email, password });
    showMessage(t("inscriptionReussie"), "success");
    window.location.href = "/dashboard";
  } catch (error) {
    showMessage(error.message || t("inscriptionEchouee"), "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  if (loginForm) loginForm.addEventListener("submit", handleLogin);
  if (registerForm) registerForm.addEventListener("submit", handleRegister);
});