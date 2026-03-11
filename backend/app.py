from flask import Flask, request, session
from flask_restx import Api, Resource, fields
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from bson.errors import InvalidId
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


def login_required() -> bool:
    return "user_id" in session


def serialize_user(user: dict) -> dict:
    return {
        "_id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }


def serialize_horoscope(horoscope: dict) -> dict:
    return {
        "_id": str(horoscope["_id"]),
        "user_id": horoscope["user_id"],
        "sign": horoscope["sign"],
        "content": horoscope["content"]
    }


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
    "password": fields.String(required=True, example="motdepasse123")
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
})

auth_me_model = api.model("AuthMeResponse", {
    "authenticated": fields.Boolean(example=True),
    "user": fields.Nested(user_model)
})

generate_horoscope_model = api.model("GenerateHoroscopeRequest", {
    "sign": fields.String(required=True, example="leo")
})

horoscope_model = api.model("Horoscope", {
    "_id": fields.String(example="67d0a1b2c3d4e5f678901235"),
    "user_id": fields.String(example="67d0a1b2c3d4e5f678901234"),
    "sign": fields.String(example="leo"),
    "content": fields.String(example="Today is a good day for leo.")
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

        if not name or not email or not password:
            return {"error": "Name, email and password are required"}, 400

        if users_collection.find_one({"email": email}):
            return {"error": "User already exists"}, 400

        user = {
            "name": name,
            "email": email,
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
    @api.response(201, "Horoscope generated", horoscope_model)
    @api.response(400, "Sign is required", error_model)
    @api.response(401, "Unauthorized", error_model)
    def post(self):
        if not login_required():
            return {"error": "Unauthorized"}, 401

        data = request.get_json() or {}
        sign = data.get("sign")

        if not sign:
            return {"error": "Sign is required"}, 400

        horoscope = {
            "user_id": session["user_id"],
            "sign": sign,
            "content": f"Today is a good day for {sign}."
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
    def post(self, horoscope_id):
        if not login_required():
            return {"error": "Unauthorized"}, 401

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
    def get(self, horoscope_id):
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