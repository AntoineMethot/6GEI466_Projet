# Documentation de l'API — AstroDaily

**Base URL :** `http://localhost:5000`  
**Documentation interactive (Swagger) :** `http://localhost:5000/swagger`  
**Format :** JSON  
**Authentification :** Cookie de session HTTP (`credentials: include` requis côté client)

---

## Santé

### `GET /health`

Vérifie que le serveur est opérationnel.

**Réponse 200**
```json
{ "status": "ok" }
```

---

## Authentification — `/api/auth`

### `POST /api/auth/register`

Crée un nouveau compte utilisateur.

**Corps de la requête**
```json
{
  "name": "Marie Tremblay",
  "email": "marie@email.com",
  "password": "motdepasse123",
  "birthdate": "1995-06-15"
}
```

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `name` | string | Oui | Nom complet |
| `email` | string | Oui | Adresse courriel unique |
| `password` | string | Oui | Mot de passe (min. 8 caractères recommandé) |
| `birthdate` | string | Oui | Date de naissance au format `YYYY-MM-DD` |

**Réponses**

| Code | Description |
| 201 | Compte créé avec succès |
| 400 | Champ manquant ou courriel déjà utilisé |

**Réponse 201**
```json
{
  "message": "User created",
  "user_id": "67d0a1b2c3d4e5f678901234"
}
```

---

### `POST /api/auth/login`

Ouvre une session utilisateur.

**Corps de la requête**
```json
{
  "email": "marie@email.com",
  "password": "motdepasse123"
}
```

**Réponses**

| Code | Description |
| 200 | Connexion réussie, cookie de session créé |
| 400 | Champs manquants |
| 401 | Identifiants invalides |

**Réponse 200**
```json
{ "message": "Login successful" }
```

---

### `POST /api/auth/logout`

Ferme la session courante.

**Réponse 200**
```json
{ "message": "Logged out" }
```

---

### `GET /api/auth/me`

Retourne l'utilisateur actuellement connecté.

**Réponses**

| Code | Description |
|---|---|
| 200 | Utilisateur authentifié |
| 400 | Session invalide |
| 401 | Non connecté |
| 404 | Utilisateur introuvable |

**Réponse 200**
```json
{
  "authenticated": true,
  "user": {
    "_id": "67d0a1b2c3d4e5f678901234",
    "name": "Marie Tremblay",
    "email": "marie@email.com",
    "birthdate": "1995-06-15"
  }
}
```

**Réponse 401**
```json
{ "authenticated": false }
```

---

## Utilisateurs — `/api/users`

Tous les endpoints de cette section nécessitent d'être connecté.

### `GET /api/users/me`

Retourne le profil de l'utilisateur connecté.

**Réponses**

| Code | Description |
|---|---|
| 200 | Profil retourné |
| 401 | Non connecté |
| 404 | Utilisateur introuvable |

**Réponse 200**
```json
{
  "_id": "67d0a1b2c3d4e5f678901234",
  "name": "Marie Tremblay",
  "email": "marie@email.com",
  "birthdate": "1995-06-15"
}
```

---

### `PATCH /api/users/me`

Met à jour le nom et/ou le courriel de l'utilisateur connecté.

**Corps de la requête** (tous les champs sont optionnels)
```json
{
  "name": "Marie T.",
  "email": "nouveau@email.com"
}
```

**Réponses**

| Code | Description |
|---|---|
| 200 | Profil mis à jour |
| 400 | Aucun champ valide / courriel déjà utilisé |
| 401 | Non connecté |
| 404 | Utilisateur introuvable |

---

### `DELETE /api/users/me`

Supprime le compte de l'utilisateur connecté, ainsi que tous ses horoscopes et commentaires.

**Réponse 200**
```json
{ "message": "User deleted" }
```

---

## Horoscopes — `/api/horoscopes`

Tous les endpoints de cette section nécessitent d'être connecté.

### `POST /api/horoscopes/generate`

Génère ou récupère l'horoscope du jour pour l'utilisateur connecté.

**Règle :** un seul horoscope par utilisateur par jour. Si l'utilisateur appuie plusieurs fois dans la même journée, le même horoscope est retourné (HTTP 200). Un nouvel horoscope est créé uniquement la première fois (HTTP 201).

**Corps de la requête**
```json
{
  "birthdate": "1995-06-15",
  "language": "fr",
  "tradition": "universal"
}
```

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `birthdate` | string | Oui | Date de naissance (`YYYY-MM-DD`) — détermine le signe astrologique |
| `language` | string | Non | `"fr"` ou `"en"` (défaut : `"fr"`) |
| `tradition` | string | Non | `"universal"` (défaut) |

**Réponses**

| Code | Description |
|---|---|
| 200 | Horoscope du jour déjà consulté — retourne l'existant |
| 201 | Nouvel horoscope généré et enregistré |
| 400 | Date de naissance manquante ou invalide |
| 401 | Non connecté |
| 429 | Limite de taux de l'API externe atteinte |
| 502 | Erreur de communication avec l'API externe |
| 504 | Timeout de l'API externe |

**Réponse 200 / 201**
```json
{
  "_id": "67d0a1b2c3d4e5f678901235",
  "user_id": "67d0a1b2c3d4e5f678901234",
  "sign": "gemini",
  "content": "Texte de l'horoscope du jour...",
  "date": "2026-03-17",
  "language": "fr",
  "tradition": "universal",
  "overall_rating": 4,
  "tips": ["Conseil 1", "Conseil 2"],
  "vote": null,
  "can_vote": false,
  "_alreadyToday": true
}
```

> `_alreadyToday` est présent uniquement dans la réponse 200 (horoscope déjà consulté aujourd'hui).  
> `can_vote` est `true` uniquement si la date de l'horoscope est **avant aujourd'hui** et que l'utilisateur n'a pas encore voté.

---

### `GET /api/horoscopes/history`

Retourne tous les horoscopes de l'utilisateur connecté, du plus récent au plus ancien.

**Réponse 200**
```json
[
  {
    "_id": "67d0a1b2c3d4e5f678901235",
    "sign": "gemini",
    "content": "...",
    "date": "2026-03-17",
    "language": "fr",
    "overall_rating": 4,
    "tips": [],
    "vote": null,
    "can_vote": false
  }
]
```

---

### `GET /api/horoscopes/search?sign=<signe>`

Filtre les horoscopes de l'utilisateur par signe astrologique.

**Paramètre de requête**

| Paramètre | Description |
|---|---|
| `sign` | Signe en minuscules : `aries`, `taurus`, `gemini`, `cancer`, `leo`, `virgo`, `libra`, `scorpio`, `sagittarius`, `capricorn`, `aquarius`, `pisces` |

**Exemple :** `GET /api/horoscopes/search?sign=leo`

**Réponse 200** : même structure que `/history`.

---

### `GET /api/horoscopes/<id>`

Retourne un horoscope par son identifiant.

> Accessible sans restriction de propriétaire (lecture publique d'un horoscope connu).

**Réponses**

| Code | Description |
|---|---|
| 200 | Horoscope trouvé |
| 400 | Identifiant invalide |
| 404 | Horoscope introuvable |

---

### `DELETE /api/horoscopes/<id>`

Supprime un horoscope appartenant à l'utilisateur connecté, ainsi que tous ses commentaires.

**Réponses**

| Code | Description |
|---|---|
| 200 | Supprimé |
| 400 | Identifiant invalide |
| 401 | Non connecté |
| 404 | Introuvable ou n'appartient pas à l'utilisateur |

---

### `POST /api/horoscopes/<id>/vote`

Enregistre le vote de l'utilisateur sur un de ses horoscopes.

**Règles :**
- L'horoscope doit appartenir à l'utilisateur connecté
- La date de l'horoscope doit être **strictement antérieure à aujourd'hui** (vote seulement le lendemain ou après)
- Un seul vote par horoscope (non modifiable)

**Corps de la requête**
```json
{ "vote": "accurate" }
```

| Valeur | Signification |
|---|---|
| `"accurate"` | C'était exact |
| `"inaccurate"` | Pas du tout exacte |

**Réponses**

| Code | Description |
|---|---|
| 200 | Vote enregistré, retourne l'horoscope mis à jour |
| 400 | Valeur de vote invalide ou identifiant invalide |
| 401 | Non connecté |
| 403 | Vote déjà effectué, ou jour pas encore passé |
| 404 | Horoscope introuvable |

---

### `GET /api/horoscopes/<id>/comments`

Retourne les commentaires d'un horoscope appartenant à l'utilisateur connecté.

**Réponse 200**
```json
[
  {
    "_id": "67d0a1b2c3d4e5f678901236",
    "horoscope_id": "67d0a1b2c3d4e5f678901235",
    "user_id": "67d0a1b2c3d4e5f678901234",
    "content": "Étonnamment précis aujourd'hui !"
  }
]
```

---

### `POST /api/horoscopes/<id>/comments`

Ajoute un commentaire sur un horoscope appartenant à l'utilisateur connecté.

**Corps de la requête**
```json
{ "content": "Très pertinent !" }
```

**Réponses**

| Code | Description |
|---|---|
| 201 | Commentaire créé |
| 400 | Contenu manquant ou identifiant invalide |
| 401 | Non connecté |
| 404 | Horoscope introuvable |

---

## Commentaires — `/api/comments`

### `DELETE /api/comments/<id>`

Supprime un commentaire appartenant à l'utilisateur connecté.

**Réponses**

| Code | Description |
|---|---|
| 200 | Supprimé |
| 400 | Identifiant invalide |
| 401 | Non connecté |
| 404 | Introuvable ou n'appartient pas à l'utilisateur |

---

## Structure des objets

### Objet `Horoscope`

```json
{
  "_id":            "string (ObjectId)",
  "user_id":        "string (ObjectId)",
  "sign":           "string (ex: leo)",
  "content":        "string",
  "date":           "string (YYYY-MM-DD)",
  "language":       "string (fr | en)",
  "tradition":      "string (universal)",
  "overall_rating": "integer (1-5) | null",
  "tips":           ["string"],
  "vote":           "accurate | inaccurate | null",
  "can_vote":       "boolean"
}
```

### Objet `User`

```json
{
  "_id":       "string (ObjectId)",
  "name":      "string",
  "email":     "string",
  "birthdate": "string (YYYY-MM-DD)"
}
```

### Objet `Comment`

```json
{
  "_id":          "string (ObjectId)",
  "horoscope_id": "string (ObjectId)",
  "user_id":      "string (ObjectId)",
  "content":      "string"
}
```

---

## Codes d'erreur courants

Toutes les erreurs retournent un objet JSON de la forme :

```json
{ "error": "Message descriptif de l'erreur" }
```

| Code HTTP | Signification |
|---|---|
| 400 | Requête invalide (champ manquant, format incorrect) |
| 401 | Non authentifié (session absente ou expirée) |
| 403 | Action non autorisée (vote déjà fait, jour pas encore passé) |
| 404 | Ressource introuvable |
| 429 | Trop de requêtes vers l'API externe |
| 502 | L'API externe AstroAPI est injoignable ou a retourné une erreur |
| 504 | L'API externe a mis trop de temps à répondre (timeout) |

---

## Notes pour une application mobile

- L'authentification repose sur un **cookie de session** HTTP. Le client mobile doit conserver et renvoyer ce cookie à chaque requête (`CookieJar` sur Android, `HTTPCookieStorage` sur iOS).
- Tous les endpoints acceptent et retournent du **JSON** (`Content-Type: application/json`).
- La documentation interactive complète est disponible à `http://localhost:5000/swagger` (interface Swagger UI).
