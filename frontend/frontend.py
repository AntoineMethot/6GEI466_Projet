from flask import Flask, render_template, redirect, url_for


# Initialisation Flask avec dossiers explicites pour templates et assets statiques.
app = Flask(__name__, template_folder='templates', static_folder='static')


@app.route("/")
def index():
	# Redirection d'entree vers la page de connexion.
	return redirect(url_for("login_page"))


@app.route("/login")
def login_page():
	# Ecran de connexion.
	return render_template("login.html", page_lang="fr")


@app.route("/register")
def register_page():
	# Ecran d'inscription.
	return render_template("register.html", page_lang="fr")


@app.route("/dashboard")
def dashboard_page():
	# Ecran principal apres authentification.
	return render_template("dashboard.html", page_lang="fr", show_header=True)


@app.route("/horoscope/<string:horoscope_id>")
def horoscope_detail_page(horoscope_id):
	# Ecran detail d'un horoscope avec commentaires associes.
	return render_template(
		"detail.html",
		page_lang="fr",
		show_header=True,
		horoscope_id=horoscope_id,
	)


if __name__ == "__main__":
    # Execution locale du frontend Flask.
    app.run(host="0.0.0.0", port=80, debug=True)

