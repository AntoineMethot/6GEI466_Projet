# Rapport des Modifications Récentes - 13 Avril 2026

## Résumé Exécutif

Les travaux du 13 avril  sont concentrés sur :

1. **Harmonisation de la traduction des signes du zodiaque** (Frontend Web)
2. **Implémentation d'une règle de déduplication des votes** (Backend API)
3. **Implémentation de la partie statistique**
4. **Validation de la date de naissance à la création de compte**

---

## 1. Traduction des Signes du Zodiaque - Frontend Web

### Problème Identifié
Les signes du zodiaque s'affichaient en anglais sur l'interface web (ex: "aries", "leo") quand on était en francais

### Solution Implémentée

#### Fichier: `frontend/static/js/common.js`
**Ligne 269-295**

Ajout d'une nouvelle fonction `translateSignLabel()` qui traduit les signes du zodiaque selon la langue sélectionnée (FR/EN).

```javascript
function translateSignLabel(sign) {
  const signs = {
    aries: { fr: "Belier", en: "Aries" },
    taurus: { fr: "Taureau", en: "Taurus" },
    gemini: { fr: "Gemeaux", en: "Gemini" },
    cancer: { fr: "Cancer", en: "Cancer" },
    leo: { fr: "Lion", en: "Leo" },
    virgo: { fr: "Vierge", en: "Virgo" },
    libra: { fr: "Balance", en: "Libra" },
    scorpio: { fr: "Scorpion", en: "Scorpio" },
    sagittarius: { fr: "Sagittaire", en: "Sagittarius" },
    capricorn: { fr: "Capricorne", en: "Capricorn" },
    aquarius: { fr: "Verseau", en: "Aquarius" },
    pisces: { fr: "Poissons", en: "Pisces" },
  };

  const key = String(sign || "").toLowerCase();
  const language = getLanguage();
  return (signs[key] && signs[key][language]) || sign || "";
}
```

**Fonctionnement :**
- Maps les clés anglaises des signes (ex: "aries") vers leurs traductions FR/EN
- Récupère la langue actuelle via `getLanguage()` (localStorage)
- Retourne la traduction appropriée, ou la valeur originale en cas d'erreur

#### Fichier: `frontend/static/js/dashboard.js`
**Ligne 126 et 153**

Application de la traduction dans deux contextes :

1. **Ligne 126** - Affichage du signe dans l'élément historique :
```javascript
sign.textContent = translateSignLabel(horoscope.sign);
```

2. **Ligne 153** - Affichage du signe dans les métadonnées (date + signe) :
```javascript
meta: {
    sign: translateSignLabel(horoscope.sign),
    // ...
}
```

#### Fichier: `frontend/static/js/detail.js`
**Ligne 82**

Application de la traduction dans la page de détail :
```javascript
document.getElementById("detail-meta").textContent = 
  `${translateSignLabel(horoscope.sign)} - ${formatDateLabel(horoscope.date)}`;
```

---

## 2. Déduplication des Votes - Backend API

### Problème Identifié
L'API permettait à un utilisateur de voter deux fois pour le même signe lors du même jour, mais dans deux langues différentes (FR et EN). Scénario :
- Utilisateur génère horoscope FR pour Leo le 13 avril → vote "accurate"
- Utilisateur génère horoscope EN pour Leo le 13 avril → peut voter à nouveau "inaccurate"

Cette situation violait la logique métier : un utilisateur ne devrait voter qu'une seule fois par jour pour un signe donné, indépendamment de la langue.

### Solution Implémentée

#### Fichier: `backend/backend.py`

**Ligne 179-200** - Nouvelle fonction helper :
```python
def _has_vote_for_same_day_sign(horoscope: dict) -> bool:
    """
    Vérifie si l'utilisateur a déjà voté pour un horoscope 
    du même jour et du même signe (indépendamment de la langue).
    """
    user_id = horoscope.get("user_id")
    sign = horoscope.get("sign")
    date_str = str(horoscope.get("date", ""))[:10]
    current_id = horoscope.get("_id")

    if not user_id or not sign or not date_str:
        return False

    # Requête MongoDB : cherche un vote existant avec les mêmes critères
    query = {
        "user_id": user_id,
        "sign": sign,
        "date": date_str,
        "vote": {"$in": ["accurate", "inaccurate"]}
    }

    # Exclut le document courant (pour éviter les faux positifs lors d'un appel sur le même document)
    if current_id is not None:
        query["_id"] = {"$ne": current_id}

    return horoscopes_collection.find_one(query, {"_id": 1}) is not None
```

**Intégration dans `_can_vote()` - Ligne 166** :
```python
def _can_vote(horoscope: dict) -> bool:
    # Le vote est possible uniquement après la fin de la journée concernée.
    if horoscope.get("vote") is not None:
        return False

    # Regle metier: un seul vote par utilisateur, jour et signe, 
    # independamment de la langue (FR/EN)
    if _has_vote_for_same_day_sign(horoscope):
        return False

    horoscope_date_str = horoscope.get("date")
    if not horoscope_date_str:
        return False
    try:
        h_date = date.fromisoformat(str(horoscope_date_str)[:10])
        return h_date < date.today()
    except Exception:
        return False
```

**Intégration dans l'endpoint POST `/api/horoscopes/<id>/vote` - Ligne 939-943** :
```python
# Regle metier globale FR/EN: un seul vote par jour/signe
if _has_vote_for_same_day_sign(horoscope):
    return {"error": "A vote already exists for this sign and day"}, 403

horoscopes_collection.update_one({"_id": horoscope_obj_id}, {"$set": {"vote": vote}})
horoscope["vote"] = vote
```

### Comportement Résultant

**Avant la modification :**
```
Jour 1 - Utilisateur "alice@example.com"
POST /api/horoscopes/generate (lang: fr) → Crée horoscope FR pour Leo
  → can_vote = true (pas encore voté pour Leo le 13 avril)
POST /api/horoscopes/<id>/vote (vote: "accurate") → ✅ Vote accepté

POST /api/horoscopes/generate (lang: en) → Crée horoscope EN pour Leo
  → can_vote = true ⚠️ (vote antérieur ignoré car langue différente)
POST /api/horoscopes/<id>/vote (vote: "inaccurate") → ✅ Vote accepté (BUG!)
```

**Après la modification :**
```
Jour 1 - Utilisateur "alice@example.com"
POST /api/horoscopes/generate (lang: fr) → Crée horoscope FR pour Leo
  → can_vote = true (pas encore voté pour Leo le 13 avril)
POST /api/horoscopes/<id>/vote (vote: "accurate") → ✅ Vote accepté

POST /api/horoscopes/generate (lang: en) → Crée horoscope EN pour Leo
  → can_vote = false (vote existant pour Leo le 13 avril détecté)
POST /api/horoscopes/<id>/vote (vote: "inaccurate") → ❌ 403 Forbidden
  {"error": "A vote already exists for this sign and day"}
```

### Points Techniques Importants

1. **Indépendance vis-à-vis de la langue** : La requête MongoDB ne filtre pas sur le champ `language`, garantissant la déduplication cross-language
2. **Exclusion du document courant** : La clause `_id != current_id` évite qu'un document ne se détecte lui-même
3. **Statut HTTP 403** : Approprié car l'utilisateur est autorisé, mais l'action est interdite par la règle métier
4. **Message d'erreur clair** : Communique précisément la raison du refus

### Résultat
- ✅ Règle métier renforcer : un vote par utilisateur/jour/signe indépendamment de la langue
- ✅ Intégrité des données garantie (pas de double-vote accidentel)
- ✅ Feedback utilisateur explicite en cas d'infraction
- ✅ Performance : requête MongoDB optimisée (index existant sur user_id+date+language couvre la requête)

---

## 3. Validation de la date à la création de compte

### Objectif
Empêcher l'inscription avec une date invalide afin de garantir des données utilisateurs cohérentes dès la création du compte.

### Implémentation backend

#### Fichier: `backend/backend.py`

**Fonction `parse_birthdate_input` (ligne ~214)**

La validation centralisée vérifie plusieurs règles:

1. La date est obligatoire (`Birthdate is required`)
2. Le format doit être `YYYY-MM-DD`
3. La date doit être une vraie date calendrier (`date.fromisoformat`)
4. La date ne peut pas être dans le futur (`Birthdate cannot be in the future`)

Extrait:

```python
if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", birthdate_str):
  return None, {"error": "Invalid birthdate format (expected YYYY-MM-DD)"}, 400

try:
  parsed_birthdate = date.fromisoformat(birthdate_str)
except ValueError:
  return None, {"error": "Invalid birthdate"}, 400

if parsed_birthdate > date.today():
  return None, {"error": "Birthdate cannot be in the future"}, 400
```

**Route d'inscription `/api/auth/register` (ligne ~501)**

La route appelle systématiquement cette validation avant la création de l'utilisateur:

```python
birthdate, birthdate_error, birthdate_status = parse_birthdate_input(data.get("birthdate"))
if birthdate_error:
  return birthdate_error, birthdate_status
```

### Côté application mobile

#### Fichier: `app_projet/src/utils/helpers.js`

La couche mobile mappe les erreurs backend liées à la date de naissance vers une erreur utilisateur unique (`dateInvalide`), ce qui rend les messages plus clairs à l'inscription.

### Résultat
- ✅ Les comptes avec date vide, mal formatée ou future sont refusés
- ✅ Les erreurs retournent un code HTTP `400` explicite
- ✅ La qualité des données utilisateurs est améliorée dès l'inscription

---

## 4. Fichiers Modifiés - Synthèse

| Fichier | Modifications | Lignes | Type |
|---------|---------------|--------|------|
| `frontend/static/js/common.js` | Ajout fonction `translateSignLabel()` | 269-295 | Nouvelle fonction |
| `frontend/static/js/dashboard.js` | 2 appels à `translateSignLabel()` | 126, 153 | Intégration |
| `frontend/static/js/detail.js` | 1 appel à `translateSignLabel()` | 82 | Intégration |
| `backend/backend.py` | Ajout fonction `_has_vote_for_same_day_sign()` | 179-200 | Nouvelle fonction |
| `backend/backend.py` | Intégration dans `_can_vote()` | 166 | Intégration |
| `backend/backend.py` | Intégration dans endpoint vote | 939-943 | Intégration |
| `backend/backend.py` | Validation centralisée `parse_birthdate_input()` + appel dans `/api/auth/register` | 214, 522 | Validation inscription |
| `app_projet/src/utils/helpers.js` | Mapping des erreurs de date (`dateInvalide`) côté mobile | 33-36 | UX erreur |


---

## Résumé

Les changements récents du projet ont renforcé la cohérence fonctionnelle entre le frontend web et le backend.

1. **Traduction des signes ajoutée sur le web**
Le web affiche maintenant les signes selon la langue active (FR/EN) grâce a `translateSignLabel()` dans `frontend/static/js/common.js`, utilisée dans `frontend/static/js/dashboard.js` et `frontend/static/js/detail.js`. 

2. **Generation d'horoscope en francais et en anglais pour une meme journee**
Le systeme permet de generer un horoscope pour les deux langues le meme jour (un document FR et un document EN), ce qui repond au besoin de consultation bilingue sans dupliquer inutilement les generations dans une meme langue.

3. **Vote gere quand les deux langues existent le meme jour**
La regle metier backend a ete durcie: meme si l'horoscope existe en FR et EN pour la meme date et le meme signe, un seul vote est autorise au total. La verification est faite via `_has_vote_for_same_day_sign()` dans `backend/backend.py`, puis appliquee dans `_can_vote()` et dans l'endpoint de vote pour bloquer un second vote avec une reponse `403`.

4. **Partie statistique ajoutee**
Une section statistique de validation a ete ajoutee: l'API expose les metriques (nombre de votes, votes exacts/inexacts, taux de validation, taux de participation) via l'endpoint de stats, et le frontend les affiche dans le tableau de bord avec un indicateur visuel.

5. **Validation de date a l'inscription**
La creation de compte valide maintenant strictement la date de naissance (champ obligatoire, format `YYYY-MM-DD`, date reelle, non future) via `parse_birthdate_input()` dans `backend/backend.py`, avec des erreurs explicites renvoyees en `400`.


