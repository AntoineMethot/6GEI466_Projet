# 6GEI466_Projet

# Horoscope Web Application

## Démarrage

Pour démarrer le docker compose, se placer dans le root du projet (avec le docker-compose.yml) et exécuter:
**docker compose up --build**

Ceci démarre 3 containers localement:
1. BD Port 27017
2. Backend Port 5000
3. Frontend Port 8080

### Configuration AstroAPI

Le backend lit la cle API depuis la variable d'environnement `ASTROLOGY_API_KEY`.
Creer un fichier `.env` a la racine du projet:

`ASTROLOGY_API_KEY=VOTRE_CLE_API`

Puis lancer Docker Compose:

`docker compose up --build`

Alternative (session PowerShell seulement):

PowerShell:
`$env:ASTROLOGY_API_KEY="VOTRE_CLE_API"`

## Documentation Swagger

localhost:5000/swagger

Info sur toutes les endpoints de l'API

## Description

Cette application web permet aux utilisateurs de consulter leur **horoscope quotidien** via une architecture **frontend / backend**. Une fois authentifies, ils peuvent generer leur horoscope selon leur signe astrologique, consulter l'historique de leurs horoscopes et laisser des commentaires.

Les horoscopes sont recuperes a partir d'une **API externe (AstroAPI)**, puis sauvegardes dans une **base de donnees NoSQL (MongoDB)** avec les commentaires associes.

---

## Technologies

**Frontend**
- HTML
- CSS
- JavaScript
- Flask Templates (Jinja2)

**Backend**
- Python
- Flask + Flask-RESTX (API REST)

**Authentification**
- Session Flask via cookie HTTP

**Base de données**
- MongoDB

---

## Fonctionnalités

- Connexion/inscription locale (email + mot de passe)
- Génération d’horoscope par **signe astrologique**
- Recuperation des donnees via **AstroAPI**
- Sauvegarde des horoscopes dans la base de données
- Consultation de l’**historique des horoscopes**
- **Commentaires** sur les horoscopes

## Ce qui a ete fait (branche `yasmine`)

### Backend

- Integration de l'endpoint AstroAPI `POST /api/v3/horoscope/sign/daily`
- Calcul automatique du signe astrologique depuis la date de naissance
- Generation de l'horoscope avec date du jour cote serveur
- Stockage enrichi: `content`, `date`, `overall_rating`, `tips`, `raw_response`
- Gestion des erreurs externes: timeout, 401, 429, erreurs 5xx
- Variables d'environnement pour la configuration API:
	- `ASTROLOGY_API_KEY`
	- `ASTROLOGY_API_BASE_URL`
	- `ASTROLOGY_API_TIMEOUT_SECONDS`

### Frontend

- templates Flask/Jinja2:
	- `login.html`
	- `register.html`
	- `dashboard.html`
	- `detail.html`
	- `base.html`
- Ajout d'une structure statique standard:
	- `frontend/static/css/style.css`
	- `frontend/static/js/common.js`
	- `frontend/static/js/auth.js`
	- `frontend/static/js/dashboard.js`
	- `frontend/static/js/detail.js`

### Securite

- Cle API jamais committe dans le code source
- Fichier `.env` ignore par Git
- Validation d'autorisation backend sur les commentaires:
	- commentaire autorise uniquement sur les horoscopes du compte connecte
	- lecture des commentaires limitee aux horoscopes du compte connecte
- Protection front contre l'injection HTML dans les commentaires ( via `textContent`et `tojson`)


# API for frontend

- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me

- POST /api/horoscopes/generate
- GET /api/horoscopes
- GET /api/horoscopes/history
- GET /api/horoscopes/search
- GET /api/horoscopes/{horoscope_id}

- POST /api/horoscopes/{horoscope_id}/comments
- GET /api/horoscopes/{horoscope_id}/comments

## Note : faux positif Jinja dans VS Code

Dans `frontend/templates/detail.html`, VS Code signale une erreur sur la ligne :

```html
<script>window.HOROSCOPE_ID = {{ horoscope_id | tojson }};</script>
```

VS Code analyse ce bloc comme du JavaScript pur, sans connaitre la syntaxe Jinja.
Il voit `{{ ... }}` et considere le JS invalide (`Property assignment expected`).

Ce n'est pas une vraie erreur : au moment ou Flask/Jinja genere la page, `{{ horoscope_id | tojson }}` est remplace par une vraie valeur JSON (ex. `"64abc123..."`), ce qui produit un JavaScript valid.

Ce type d'alerte est appele **faux positif** : signale par l'outil d'analyse statique, mais sans impact sur le fonctionnement de l'application.

