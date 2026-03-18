from flask import Flask, request, session
from datetime import date, datetime
from flask_restx import Api, Resource, fields
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from bson.errors import InvalidId
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

# Session cookie settings for local dev across frontend/backend ports
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False

# Swagger / Flask-RESTX setup
api = Api(
    app,
    version="1.0",
    title="Horoscope API",
    description="API REST pour une application d'horoscope",
    doc="/swagger"
)

# MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_db_name = os.getenv("MONGO_DB_NAME", "horoscope_app")

client = MongoClient(mongo_uri)
db = client[mongo_db_name]

users_collection = db["users"]
horoscopes_collection = db["horoscopes"]
comments_collection = db["comments"]
# Cache quotidien partagé : 12 signes × 2 langues, pré-chargés chaque matin par le scheduler.
daily_cache_collection = db["daily_horoscopes_cache"]


def _deduplicate_horoscopes_for_unique_index():
    """Supprime les doublons user_id+date en conservant le document le plus récent."""
    duplicates = horoscopes_collection.aggregate([
        {
            "$group": {
                "_id": {"user_id": "$user_id", "date": "$date"},
                "ids": {"$push": "$_id"},
                "count": {"$sum": 1}
            }
        },
        {"$match": {"count": {"$gt": 1}}}
    ])

    total_deleted = 0
    for group in duplicates:
        ids = group.get("ids", [])
        if len(ids) < 2:
            continue

        keep_id = max(ids)
        delete_ids = [doc_id for doc_id in ids if doc_id != keep_id]
        if not delete_ids:
            continue

        result = horoscopes_collection.delete_many({"_id": {"$in": delete_ids}})
        total_deleted += result.deleted_count

    if total_deleted > 0:
        app.logger.warning(f"[startup] {total_deleted} doublons horoscopes supprimes pour creer l'index unique")


# Index unique pour éviter les doublons dans le cache et dans l'historique utilisateur.
daily_cache_collection.create_index(
    [("sign", ASCENDING), ("language", ASCENDING), ("date", ASCENDING)],
    unique=True
)
try:
    horoscopes_collection.create_index(
        [("user_id", ASCENDING), ("date", ASCENDING)],
        unique=True,
        sparse=False
    )
except DuplicateKeyError:
    # Migration de sécurité: si des doublons historiques existent déjà,
    # on les supprime puis on retente la création de l'index unique.
    _deduplicate_horoscopes_for_unique_index()
    horoscopes_collection.create_index(
        [("user_id", ASCENDING), ("date", ASCENDING)],
        unique=True,
        sparse=False
    )

# La configuration de l'API externe vient des variables d'environnement
# pour ne jamais versionner de secret dans le depot.
astrology_api_base_url = os.getenv("ASTROLOGY_API_BASE_URL", "https://api.astrology-api.io")
astrology_api_key = os.getenv("ASTROLOGY_API_KEY", "")
astrology_api_timeout_seconds = float(os.getenv("ASTROLOGY_API_TIMEOUT_SECONDS", "10"))

# Les 12 signes du zodiaque et les langues supportées.
ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]
SUPPORTED_LANGUAGES = ["fr", "en"]
DEFAULT_TRADITION = "universal"


def login_required() -> bool:
    return "user_id" in session


def serialize_user(user: dict) -> dict:
    return {
        "_id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "birthdate": user.get("birthdate")
    }


def serialize_horoscope(horoscope: dict) -> dict:
    return {
        "_id": str(horoscope["_id"]),
        "user_id": horoscope["user_id"],
        "sign": horoscope["sign"],
        "content": horoscope["content"],
        "date": horoscope.get("date"),
        "language": horoscope.get("language"),
        "tradition": horoscope.get("tradition"),
        "overall_rating": horoscope.get("overall_rating"),
        "tips": horoscope.get("tips", []),
        "vote": horoscope.get("vote"),
        "can_vote": _can_vote(horoscope)
    }


def _can_vote(horoscope: dict) -> bool:
    # Le vote est possible uniquement après la fin de la journée concernée.
    if horoscope.get("vote") is not None:
        return False
    horoscope_date_str = horoscope.get("date")
    if not horoscope_date_str:
        return False
    try:
        h_date = date.fromisoformat(str(horoscope_date_str)[:10])
        return h_date < date.today()
    except Exception:
        return False


def serialize_comment(comment: dict) -> dict:
    return {
        "_id": str(comment["_id"]),
        "horoscope_id": comment["horoscope_id"],
        "user_id": comment["user_id"],
        "content": comment["content"]
    }


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:8080"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PATCH,DELETE,OPTIONS"
    return response


@app.route("/api/<path:path>", methods=["OPTIONS"])
def options_api(path):
    return ("", 204)


# Namespaces
auth_ns = api.namespace("api/auth", description="Authentication")
users_ns = api.namespace("api/users", description="Users")
horoscopes_ns = api.namespace("api/horoscopes", description="Horoscopes")
comments_ns = api.namespace("api/comments", description="Comments")
health_ns = api.namespace("", description="Health")


# Models for Swagger
register_model = api.model("RegisterRequest", {
    "name": fields.String(required=True, example="Antoine"),
    "email": fields.String(required=True, example="antoine@email.com"),
    "password": fields.String(required=True, example="motdepasse123"),
    "birthdate": fields.String(required=True, example="1990-01-01")
})


login_model = api.model("LoginRequest", {
    "email": fields.String(required=True, example="antoine@email.com"),
    "password": fields.String(required=True, example="motdepasse123")
})

message_model = api.model("MessageResponse", {
    "message": fields.String(example="Success")
})

error_model = api.model("ErrorResponse", {
    "error": fields.String(example="Invalid request")
})

user_model = api.model("User", {
    "_id": fields.String(example="67d0a1b2c3d4e5f678901234"),
    "name": fields.String(example="Antoine"),
    "email": fields.String(example="antoine@email.com")
    ,"birthdate": fields.String(example="1990-01-01")
})


auth_me_model = api.model("AuthMeResponse", {
    "authenticated": fields.Boolean(example=True),
    "user": fields.Nested(user_model)
})

generate_horoscope_model = api.model("GenerateHoroscopeRequest", {
    "birthdate": fields.String(required=True, example="1990-01-01"),
    "language": fields.String(required=False, example="en"),
    "tradition": fields.String(required=False, example="universal")
})


def get_zodiac_sign(birth: date) -> str:
    m = birth.month
    d = birth.day
    # Ranges inclusive
    if (m == 3 and d >= 21) or (m == 4 and d <= 19):
        return "aries"
    if (m == 4 and d >= 20) or (m == 5 and d <= 20):
        return "taurus"
    if (m == 5 and d >= 21) or (m == 6 and d <= 20):
        return "gemini"
    if (m == 6 and d >= 21) or (m == 7 and d <= 22):
        return "cancer"
    if (m == 7 and d >= 23) or (m == 8 and d <= 22):
        return "leo"
    if (m == 8 and d >= 23) or (m == 9 and d <= 22):
        return "virgo"
    if (m == 9 and d >= 23) or (m == 10 and d <= 22):
        return "libra"
    if (m == 10 and d >= 23) or (m == 11 and d <= 21):
        return "scorpio"
    if (m == 11 and d >= 22) or (m == 12 and d <= 21):
        return "sagittarius"
    if (m == 12 and d >= 22) or (m == 1 and d <= 19):
        return "capricorn"
    if (m == 1 and d >= 20) or (m == 2 and d <= 18):
        return "aquarius"
    if (m == 2 and d >= 19) or (m == 3 and d <= 20):
        return "pisces"
    return "unknown"


def fetch_daily_horoscope(sign: str, target_date: str, language: str, tradition: str):
    if not astrology_api_key:
        return None, {"error": "Astrology API key is not configured"}, 500

    endpoint = f"{astrology_api_base_url.rstrip('/')}/api/v3/horoscope/sign/daily"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {astrology_api_key}"
    }
    payload = {
        "sign": sign.title(),
        "date": target_date,
        "language": language,
        "tradition": tradition
    }

    try:
        # Le timeout evite de bloquer l'API locale si le fournisseur externe repond lentement.
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=astrology_api_timeout_seconds,
        )
    except requests.Timeout:
        return None, {"error": "Astrology API request timed out"}, 504
    except requests.RequestException:
        return None, {"error": "Unable to reach Astrology API"}, 502

    if response.status_code == 401:
        return None, {"error": "Astrology API unauthorized. Check API key."}, 502
    if response.status_code == 429:
        return None, {"error": "Astrology API rate limit reached"}, 429
    if response.status_code >= 500:
        return None, {"error": "Astrology API server error"}, 502
    if response.status_code >= 400:
        return None, {"error": "Astrology API rejected request", "details": response.text}, 400

    try:
        payload = response.json()
    except ValueError:
        return None, {"error": "Astrology API returned invalid JSON"}, 502

    # La reponse est enveloppee dans un objet 'data'
    data = payload.get("data") if isinstance(payload, dict) else None
    if not data:
        return None, {"error": "Astrology API response missing 'data' field"}, 502

    return data, None, 200


def prefetch_daily_horoscopes():
    """Pré-charge les horoscopes de tous les signes pour aujourd'hui (FR + EN).
    Appelé au démarrage et chaque matin par le scheduler APScheduler.
    """
    today = date.today().isoformat()
    app.logger.info(f"[scheduler] Début du prefetch pour {today}")

    for sign in ZODIAC_SIGNS:
        for language in SUPPORTED_LANGUAGES:
            # Entrée déjà en cache : aucun appel externe nécessaire.
            if daily_cache_collection.find_one({"sign": sign, "language": language, "date": today}):
                continue

            api_data, api_error, _ = fetch_daily_horoscope(sign, today, language, DEFAULT_TRADITION)
            if api_error:
                app.logger.warning(f"[scheduler] Échec prefetch {sign}/{language}: {api_error}")
                continue

            horoscope_text = api_data.get("overall_theme")
            if not horoscope_text:
                app.logger.warning(f"[scheduler] overall_theme manquant pour {sign}/{language}")
                continue

            tips = [
                area["prediction"]
                for area in api_data.get("life_areas", [])
                if area.get("prediction")
            ]

            cache_doc = {
                "sign": sign,
                "language": language,
                "date": api_data.get("date", today),
                "content": horoscope_text,
                "overall_rating": api_data.get("overall_rating"),
                "tips": tips,
                "raw_response": api_data
            }

            try:
                daily_cache_collection.insert_one(cache_doc)
                app.logger.info(f"[scheduler] Cached {sign}/{language}/{today}")
            except Exception as exc:
                app.logger.warning(f"[scheduler] Insert cache {sign}/{language}: {exc}")

    app.logger.info(f"[scheduler] Prefetch terminé pour {today}")


# Démarrage du scheduler APScheduler en arrière-plan.
# Tache quotidienne à 6h du matin + exécution immédiate au démarrage.
_scheduler = BackgroundScheduler()
_scheduler.add_job(prefetch_daily_horoscopes, "cron", hour=6, minute=0)
_scheduler.start()
atexit.register(lambda: _scheduler.shutdown(wait=False))

# Prefetch initial au démarrage du serveur (utile si le container redémarre en journée).
prefetch_daily_horoscopes()


horoscope_model = api.model("Horoscope", {
    "_id": fields.String(example="67d0a1b2c3d4e5f678901235"),
    "user_id": fields.String(example="67d0a1b2c3d4e5f678901234"),
    "sign": fields.String(example="leo"),
    "content": fields.String(example="Today's energy supports bold initiatives and creative projects."),
    "date": fields.String(example="2026-02-13"),
    "language": fields.String(example="en"),
    "tradition": fields.String(example="universal"),
    "overall_rating": fields.Integer(example=4),
    "tips": fields.List(fields.String, example=["Initiate important conversations"]),
    "vote": fields.String(example=None),
    "can_vote": fields.Boolean(example=False)
})

vote_model = api.model("VoteRequest", {
    "vote": fields.String(required=True, enum=["accurate", "inaccurate"], example="accurate")
})

comment_create_model = api.model("CreateCommentRequest", {
    "content": fields.String(required=True, example="This one is surprisingly accurate.")
})

comment_model = api.model("Comment", {
    "_id": fields.String(example="67d0a1b2c3d4e5f678901236"),
    "horoscope_id": fields.String(example="67d0a1b2c3d4e5f678901235"),
    "user_id": fields.String(example="67d0a1b2c3d4e5f678901234"),
    "content": fields.String(example="This one is surprisingly accurate.")
})

status_model = api.model("HealthResponse", {
    "status": fields.String(example="ok")
})


# ------------------------
# HEALTH
# ------------------------

@health_ns.route("/health")
class HealthResource(Resource):
    @api.marshal_with(status_model, code=200)
    def get(self):
        return {"status": "ok"}, 200


# ------------------------
# AUTH
# ------------------------

@auth_ns.route("/register")
class RegisterResource(Resource):
    @api.expect(register_model, validate=True)
    @api.response(201, "User created")
    @api.response(400, "User already exists or invalid request", error_model)
    def post(self):
        data = request.get_json() or {}

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        birthdate = data.get("birthdate")

        if not name or not email or not password or not birthdate:
            return {"error": "Name, email, password and birthdate are required"}, 400

        if users_collection.find_one({"email": email}):
            return {"error": "User already exists"}, 400

        user = {
            "name": name,
            "email": email,
            "birthdate": birthdate,
            "password_hash": generate_password_hash(password)
        }

        result = users_collection.insert_one(user)

        return {
            "message": "User created",
            "user_id": str(result.inserted_id)
        }, 201


@auth_ns.route("/login")
class LoginResource(Resource):
    @api.expect(login_model, validate=True)
    @api.response(200, "Login successful", message_model)
    @api.response(400, "Missing email or password", error_model)
    @api.response(401, "Invalid credentials", error_model)
    def post(self):
        data = request.get_json() or {}

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Email and password are required"}, 400

        user = users_collection.find_one({"email": email})

        if not user or not check_password_hash(user["password_hash"], password):
            return {"error": "Invalid credentials"}, 401

        session["user_id"] = str(user["_id"])

        return {"message": "Login successful"}, 200


@auth_ns.route("/logout")
class LogoutResource(Resource):
    @api.response(200, "Logged out", message_model)
    def post(self):
        session.clear()
        return {"message": "Logged out"}, 200


@auth_ns.route("/me")
class MeResource(Resource):
    @api.response(200, "Authenticated user", auth_me_model)
    @api.response(400, "Invalid session", error_model)
    @api.response(401, "Not authenticated")
    @api.response(404, "User not found", error_model)
    def get(self):
        if not login_required():
            return {"authenticated": False}, 401

        try:
            user_id = ObjectId(session["user_id"])
        except InvalidId:
            session.clear()
            return {"authenticated": False, "error": "Invalid session"}, 400

        user = users_collection.find_one({"_id": user_id}, {"password_hash": 0})

        if user is None:
            session.clear()
            return {"authenticated": False, "error": "User not found"}, 404

        return {
            "authenticated": True,
            "user": serialize_user(user)
        }, 200


# ------------------------
# USERS
# ------------------------

@users_ns.route("/me")
class UserMeResource(Resource):
    @api.response(200, "User profile", user_model)
    @api.response(400, "Invalid session", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(404, "User not found", error_model)
    def get(self):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        try:
            user_id = ObjectId(session["user_id"])
        except InvalidId:
            session.clear()
            return {"error": "Invalid session"}, 400

        user = users_collection.find_one({"_id": user_id}, {"password_hash": 0})

        if user is None:
            session.clear()
            return {"error": "User not found"}, 404

        return serialize_user(user), 200

    @api.expect(api.model("UpdateUserRequest", {
        "name": fields.String(required=False, example="Antoine Méthot"),
        "email": fields.String(required=False, example="antoine@email.com")
    }), validate=True)
    @api.response(200, "User updated", user_model)
    @api.response(400, "Invalid request or session", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(404, "User not found", error_model)
    def patch(self):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        data = request.get_json() or {}
        update_fields = {}

        if "name" in data and data["name"]:
            update_fields["name"] = data["name"]

        if "email" in data and data["email"]:
            existing_user = users_collection.find_one({
                "email": data["email"],
                "_id": {"$ne": ObjectId(session["user_id"])}
            })
            if existing_user:
                return {"error": "Email already in use"}, 400
            update_fields["email"] = data["email"]

        if not update_fields:
            return {"error": "No valid fields to update"}, 400

        try:
            user_id = ObjectId(session["user_id"])
        except InvalidId:
            session.clear()
            return {"error": "Invalid session"}, 400

        result = users_collection.update_one(
            {"_id": user_id},
            {"$set": update_fields}
        )

        user = users_collection.find_one({"_id": user_id}, {"password_hash": 0})

        if user is None:
            return {"error": "User not found"}, 404

        return serialize_user(user), 200

    @api.response(200, "User deleted", message_model)
    @api.response(400, "Invalid session", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(404, "User not found", error_model)
    def delete(self):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        try:
            user_id = ObjectId(session["user_id"])
        except InvalidId:
            session.clear()
            return {"error": "Invalid session"}, 400

        user_id_str = session["user_id"]

        result = users_collection.delete_one({"_id": user_id})

        if result.deleted_count == 0:
            return {"error": "User not found"}, 404

        horoscopes_collection.delete_many({"user_id": user_id_str})
        comments_collection.delete_many({"user_id": user_id_str})

        session.clear()
        return {"message": "User deleted"}, 200


# ------------------------
# HOROSCOPES
# ------------------------

@horoscopes_ns.route("/generate")
class GenerateHoroscopeResource(Resource):
    @api.expect(generate_horoscope_model, validate=True)
    @api.response(200, "Horoscope du jour deja consulte (retourne l'existant)", horoscope_model)
    @api.response(201, "Horoscope genere et enregistre", horoscope_model)
    @api.response(400, "Birthdate is required or invalid", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(429, "External API rate limit reached", error_model)
    @api.response(500, "Server configuration error", error_model)
    @api.response(502, "External API communication error", error_model)
    @api.response(504, "External API timeout", error_model)
    def post(self):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        data = request.get_json() or {}
        birthdate_str = data.get("birthdate")

        if not birthdate_str:
            return {"error": "Birthdate is required"}, 400

        try:
            birth = datetime.fromisoformat(birthdate_str).date()
        except Exception:
            return {"error": "Invalid birthdate format (expected YYYY-MM-DD)"}, 400

        sign = get_zodiac_sign(birth)
        if sign == "unknown":
            return {"error": "Unable to determine zodiac sign from birthdate"}, 400

        language = data.get("language", "fr")
        tradition = data.get("tradition", DEFAULT_TRADITION)
        today = date.today().isoformat()

        # Limite : un seul horoscope par utilisateur par jour.
        # Retourne l'existant sans rappeler l'API externe.
        existing = horoscopes_collection.find_one({"user_id": session["user_id"], "date": today})
        if existing:
            serialized = serialize_horoscope(existing)
            serialized["_alreadyToday"] = True
            return serialized, 200

        # Recherche dans le cache pré-chargé par le scheduler.
        cached = daily_cache_collection.find_one({"sign": sign, "language": language, "date": today})

        if cached:
            horoscope = {
                "user_id": session["user_id"],
                "sign": sign,
                "content": cached["content"],
                "date": cached["date"],
                "language": language,
                "tradition": tradition,
                "overall_rating": cached.get("overall_rating"),
                "tips": cached.get("tips", []),
                "vote": None,
                "source": "cache"
            }
        else:
            # Fallback : appel direct à l'API si le cache n'est pas encore prêt.
            horoscope_api_data, api_error, api_status = fetch_daily_horoscope(
                sign=sign, target_date=today, language=language, tradition=tradition
            )
            if api_error:
                return api_error, api_status

            horoscope_text = horoscope_api_data.get("overall_theme")
            if not horoscope_text:
                return {"error": "Astrology API response missing 'overall_theme' field"}, 502

            tips = [
                area["prediction"]
                for area in horoscope_api_data.get("life_areas", [])
                if area.get("prediction")
            ]

            horoscope = {
                "user_id": session["user_id"],
                "sign": sign,
                "content": horoscope_text,
                "date": horoscope_api_data.get("date", today),
                "language": language,
                "tradition": tradition,
                "overall_rating": horoscope_api_data.get("overall_rating"),
                "tips": tips,
                "vote": None,
                "source": "api-direct",
                "raw_response": horoscope_api_data
            }

        result = horoscopes_collection.insert_one(horoscope)
        horoscope["_id"] = result.inserted_id

        return serialize_horoscope(horoscope), 201



@horoscopes_ns.route("")
class HoroscopeListResource(Resource):
    @api.response(200, "List of horoscopes", [horoscope_model])
    @api.response(401, "Unauthorized", error_model)
    def get(self):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        user_id = session["user_id"]
        results = []

        for horoscope in horoscopes_collection.find({"user_id": user_id}):
            results.append(serialize_horoscope(horoscope))

        return results, 200


@horoscopes_ns.route("/history")
class HoroscopeHistoryResource(Resource):
    @api.response(200, "Horoscope history", [horoscope_model])
    @api.response(401, "Unauthorized", error_model)
    def get(self):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        user_id = session["user_id"]
        results = []

        for horoscope in horoscopes_collection.find({"user_id": user_id}).sort("_id", -1):
            results.append(serialize_horoscope(horoscope))

        return results, 200


@horoscopes_ns.route("/<string:horoscope_id>/vote")
class HoroscopeVoteResource(Resource):
    @api.expect(vote_model, validate=True)
    @api.response(200, "Vote enregistre", horoscope_model)
    @api.response(400, "Vote invalide ou id invalide", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(403, "Vote non autorise (jour pas encore passe ou deja vote)", error_model)
    @api.response(404, "Horoscope introuvable", error_model)
    def post(self, horoscope_id):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        try:
            horoscope_obj_id = ObjectId(horoscope_id)
        except InvalidId:
            return {"error": "Invalid horoscope id"}, 400

        # Restriction d'acces : seul le proprietaire peut voter.
        horoscope = horoscopes_collection.find_one({
            "_id": horoscope_obj_id,
            "user_id": session["user_id"]
        })
        if not horoscope:
            return {"error": "Horoscope not found"}, 404

        data = request.get_json() or {}
        vote = data.get("vote")

        if vote not in ("accurate", "inaccurate"):
            return {"error": "Vote must be 'accurate' or 'inaccurate'"}, 400

        # Un seul vote par horoscope.
        if horoscope.get("vote") is not None:
            return {"error": "Already voted on this horoscope"}, 403

        # Le vote n'est autorise qu'apres la fin du jour de l'horoscope.
        try:
            h_date = date.fromisoformat(str(horoscope.get("date", ""))[:10])
        except Exception:
            return {"error": "Invalid horoscope date"}, 400

        if h_date >= date.today():
            return {"error": "Cannot vote before the day has passed"}, 403

        horoscopes_collection.update_one({"_id": horoscope_obj_id}, {"$set": {"vote": vote}})
        horoscope["vote"] = vote

        return serialize_horoscope(horoscope), 200


@horoscopes_ns.route("/search")
class HoroscopeSearchResource(Resource):
    @api.doc(params={"sign": "Zodiac sign to filter by"})
    @api.response(200, "Filtered horoscopes", [horoscope_model])
    @api.response(401, "Unauthorized", error_model)
    def get(self):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        sign = request.args.get("sign")
        query = {"user_id": session["user_id"]}

        if sign:
            query["sign"] = sign

        results = []
        for horoscope in horoscopes_collection.find(query):
            results.append(serialize_horoscope(horoscope))

        return results, 200


@horoscopes_ns.route("/<string:horoscope_id>")
class HoroscopeResource(Resource):
    @api.response(200, "Horoscope found", horoscope_model)
    @api.response(400, "Invalid horoscope id", error_model)
    @api.response(404, "Not found", error_model)
    def get(self, horoscope_id):
        try:
            horoscope = horoscopes_collection.find_one({"_id": ObjectId(horoscope_id)})
        except InvalidId:
            return {"error": "Invalid horoscope id"}, 400

        if not horoscope:
            return {"error": "Not found"}, 404

        return serialize_horoscope(horoscope), 200

    @api.response(200, "Deleted", message_model)
    @api.response(400, "Invalid horoscope id", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(404, "Not found", error_model)
    def delete(self, horoscope_id):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        try:
            result = horoscopes_collection.delete_one({
                "_id": ObjectId(horoscope_id),
                "user_id": session["user_id"]
            })
        except InvalidId:
            return {"error": "Invalid horoscope id"}, 400

        if result.deleted_count == 0:
            return {"error": "Not found"}, 404

        comments_collection.delete_many({"horoscope_id": horoscope_id})
        return {"message": "Deleted"}, 200


@horoscopes_ns.route("/<string:horoscope_id>/comments")
class HoroscopeCommentsResource(Resource):
    @api.expect(comment_create_model, validate=True)
    @api.response(201, "Comment created", comment_model)
    @api.response(400, "Content is required", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(404, "Horoscope not found", error_model)
    def post(self, horoscope_id):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        # Validation d'ID pour eviter les erreurs MongoDB et les requetes mal formees.
        try:
            horoscope_obj_id = ObjectId(horoscope_id)
        except InvalidId:
            return {"error": "Invalid horoscope id"}, 400

        # Controle d'autorisation: commentaire reserve aux horoscopes du compte connecte.
        horoscope = horoscopes_collection.find_one({
            "_id": horoscope_obj_id,
            "user_id": session["user_id"]
        })
        if not horoscope:
            return {"error": "Horoscope not found"}, 404

        data = request.get_json() or {}
        content = data.get("content")

        if not content:
            return {"error": "Content is required"}, 400

        comment = {
            "horoscope_id": horoscope_id,
            "user_id": session["user_id"],
            "content": content
        }

        result = comments_collection.insert_one(comment)
        comment["_id"] = result.inserted_id

        return serialize_comment(comment), 201

    @api.response(200, "Comments list", [comment_model])
    @api.response(400, "Invalid horoscope id", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(404, "Horoscope not found", error_model)
    def get(self, horoscope_id):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        # Validation d'ID pour eviter les erreurs MongoDB et les requetes mal formees.
        try:
            horoscope_obj_id = ObjectId(horoscope_id)
        except InvalidId:
            return {"error": "Invalid horoscope id"}, 400

        # Controle d'autorisation: lecture reservee aux commentaires du compte connecte.
        horoscope = horoscopes_collection.find_one({
            "_id": horoscope_obj_id,
            "user_id": session["user_id"]
        })
        if not horoscope:
            return {"error": "Horoscope not found"}, 404

        results = []

        for comment in comments_collection.find({"horoscope_id": horoscope_id}):
            results.append(serialize_comment(comment))

        return results, 200


# ------------------------
# COMMENTS
# ------------------------

@comments_ns.route("/<string:comment_id>")
class CommentResource(Resource):
    @api.response(200, "Comment deleted", message_model)
    @api.response(400, "Invalid comment id", error_model)
    @api.response(401, "Unauthorized", error_model)
    @api.response(404, "Not found", error_model)
    def delete(self, comment_id):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        try:
            result = comments_collection.delete_one({
                "_id": ObjectId(comment_id),
                "user_id": session["user_id"]
            })
        except InvalidId:
            return {"error": "Invalid comment id"}, 400

        if result.deleted_count == 0:
            return {"error": "Not found"}, 404

        return {"message": "Comment deleted"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)