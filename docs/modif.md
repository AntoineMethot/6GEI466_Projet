# Travail de la séance — 17 mars 2026

## Vue d'ensemble


1. Pré-chargement quotidien des horoscopes via un planificateur (APScheduler)
2. Limitation à un seul horoscope par utilisateur par jour
3. Système de vote accessible uniquement le lendemain

---

## 1. Pré-chargement quotidien des horoscopes (cache + APScheduler)

### Problème initial

À chaque fois qu'un utilisateur cliquait sur "Générer", le backend appelait l'API externe AstroAPI en temps réel. Cela posait deux risques :
- Lenteur si l'API externe est lente
- Limite de taux (*rate limit*) atteinte si plusieurs utilisateurs demandent leur horoscope en même temps

### Solution mise en place

Un **cache MongoDB** (`daily_horoscopes_cache`) est pré-rempli chaque matin pour les 12 signes du zodiaque × 2 langues (FR + EN), soit 24 entrées par jour.

#### Nouvelle collection MongoDB

```
daily_horoscopes_cache
  sign       : "leo"
  language   : "fr"
  date       : "2026-03-17"
  content    : "Texte de l'horoscope..."
  overall_rating : 4
  tips       : ["conseil 1", "conseil 2"]
```

Un **index unique** sur `(sign, language, date)` empêche les doublons si le prefetch est déclenché plusieurs fois.

#### APScheduler — c'est quoi ?

**APScheduler** (*Advanced Python Scheduler*) est une bibliothèque Python qui permet d'exécuter une fonction automatiquement à une heure précise, comme `cron` sur Linux. Ici, on l'utilise pour déclencher la fonction `prefetch_daily_horoscopes()` tous les matins à 6h00.

```python
_scheduler = BackgroundScheduler()
_scheduler.add_job(prefetch_daily_horoscopes, "cron", hour=6, minute=0)
_scheduler.start()
```

#### Et si le serveur ne tourne pas à 6h ?

Ce cas est géré : la fonction `prefetch_daily_horoscopes()` est aussi appelée **immédiatement au démarrage du serveur**. Ainsi, si le serveur redémarre à 14h, le cache se remplit à 14h. Comme chaque insertion vérifie d'abord si l'entrée existe déjà (`find_one` avant `insert_one`), il n'y a aucun doublon.

```python
# Exécution immédiate au démarrage (en plus de la tâche cron à 6h)
prefetch_daily_horoscopes()
```

#### Logique dans l'endpoint `/api/horoscopes/generate`

```
1. L'utilisateur a-t-il déjà un horoscope aujourd'hui ?  → retourner l'existant (HTTP 200)
2. Le cache contient-il l'horoscope pour ce signe/langue ? → utiliser le cache (HTTP 201)
3. Sinon → appel direct à AstroAPI en fallback (HTTP 201)
```

---

## 2. Un seul horoscope par utilisateur par jour

### Comportement

Si l'utilisateur appuie à nouveau sur "Générer" dans la même journée, le backend retourne simplement l'horoscope déjà enregistré ce jour-là (HTTP 200), sans rappeler l'API externe.

### Mise en place

**Index MongoDB unique** sur la collection `horoscopes` :

```python
horoscopes_collection.create_index(
    [("user_id", ASCENDING), ("date", ASCENDING)],
    unique=True
)
```

Cet index garantit qu'il ne peut exister qu'un seul document par utilisateur par date, même en cas de bug ou de requête concurrente.

**Côté frontend**, la réponse HTTP 200 vs 201 permet d'afficher le bon message :
- 200 → "Horoscope du jour déjà consulté."
- 201 → "Horoscope généré avec succès."

La distinction est faite grâce au champ `_alreadyToday: true` ajouté dans la réponse 200.

---

## 3. Système de vote

### Règles métier

- Les boutons de vote apparaissent dans **l'historique** et dans la **page de détail**, pas sur la carte du jour.
- Le vote n'est possible **que le lendemain** de la date de l'horoscope (le temps de vérifier si c'était exact).
- **Un seul vote** par horoscope. Une fois voté, les boutons laissent place au résultat affiché.
- Le vote appartient à l'utilisateur : seul le propriétaire de l'horoscope peut voter.

### Valeurs possibles

| Valeur | Signification |
|---|---|
| `"accurate"` | C'était exact |
| `"inaccurate"` | Pas du tout exacte |
| `null` | Pas encore voté |

### Nouvel endpoint backend

```
POST /api/horoscopes/<id>/vote
Body : { "vote": "accurate" | "inaccurate" }
```

Validations effectuées :
1. Utilisateur connecté
2. L'horoscope appartient à l'utilisateur connecté
3. La valeur du vote est bien `accurate` ou `inaccurate`
4. Pas déjà voté (`vote == null`)
5. La date de l'horoscope est **strictement antérieure à aujourd'hui**

### Nouveaux champs dans les horoscopes sérialisés

| Champ | Type | Description |
|---|---|---|
| `vote` | `string \| null` | Valeur du vote si déjà voté |
| `can_vote` | `boolean` | `true` si le vote est encore possible |

### Changements frontend

**dashboard.js** — `buildVoteSection(horoscope)` :
- Si `vote === "accurate"` → affiche "✓ C'était exact" en vert
- Si `vote === "inaccurate"` → affiche "✗ Pas du tout exacte" en gris
- Si `can_vote === true` → affiche deux boutons "C'était exact" / "Pas du tout"
- Sinon → rien (horoscope d'aujourd'hui, vote non encore disponible)

**detail.js** — `renderVote(horoscope)` : même logique, pour la page de détail.

**style.css** — Nouveaux styles : `.vote-row`, `.btn-sm`, `.vote-result`, `.vote-accurate`, `.vote-inaccurate`, `.history-item-link`.

---

## 4. Restructuration de l'élément historique (HTML/JS)

Avant, chaque item de l'historique était une balise `<a>` (lien entier). Comme on devait y ajouter des boutons (les boutons de vote ne peuvent pas être imbriqués dans un `<a>`), la structure a été changée :

**Avant :**
```html
<a class="history-item" href="/horoscope/123">...</a>
```

**Après :**
```html
<div class="history-item">
  <a class="history-item-link" href="/horoscope/123">...</a>
  <div class="vote-row">...</div>
</div>
```

---

## 5. Note sur AJAX / fetch et l'application mobile

Le frontend web utilise l'API `fetch` native de JavaScript (l'équivalent moderne d'AJAX), centralisée dans la fonction `requestJSON()` dans `common.js`. Tout le rendu est dynamique (sans rechargement de page).

Pour une **application mobile** (React Native, Flutter, Android/iOS natif), aucun changement au backend n'est nécessaire. Le backend expose une **API REST complète**, documentée via Swagger à `/swagger`. L'app mobile n'a qu'à appeler les mêmes endpoints HTTP avec l'outil HTTP de son framework :

| Framework | Outil recommandé |
|---|---|
| React Native | `fetch` ou `axios` |
| Flutter | `http` ou `dio` |
| Android (Kotlin) | `Retrofit` |
| iOS (Swift) | `URLSession` ou `Alamofire` |

La gestion de session se fait par **cookie de session** (`credentials: "include"` côté web). Pour une app mobile, il faudra gérer ce cookie manuellement ou basculer sur un système de token (JWT) selon les besoins.

---

## Fichiers modifiés

| Fichier | Modifications |
|---|---|
| `backend/backend.py` | APScheduler, cache, prefetch, vote endpoint, index MongoDB, `_alreadyToday` |
| `backend/requirements.txt` | Ajout de `APScheduler==3.11.0` |
| `frontend/static/js/dashboard.js` | `buildVoteSection`, `submitVote`, refonte de `buildHistoryItem` |
| `frontend/static/js/detail.js` | Ajout de `renderVote`, mise à jour de `loadHoroscopeDetail` |
| `frontend/static/js/common.js` | Ajout des clés i18n liées au vote |
| `frontend/templates/dashboard.html` | Suppression des boutons de vote statiques |
| `frontend/templates/detail.html` | Ajout du `<div id="detail-vote">` |
| `frontend/static/css/style.css` | Styles vote, restructuration `.history-item` |
