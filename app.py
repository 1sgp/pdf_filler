import os

from flask import Flask, jsonify, make_response, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
# from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from waitress import serve
import openai


from pdf_filler import VERSION, conf
from pdf_filler.fill import main
from helpers import apology, login_required

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# app.config[
#     "SQLALCHEMY_DATABASE_URI"
# ] = "postgresql://useyourown:useyourown@10.0.0.103/example"
# db.init_app(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1/second"],
    storage_uri="memory://",
)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Generic ratelimit error handler, atm json output
# ToDO render_template with error429.html
@app.errorhandler(429)
def ratelimit_handler(e):
    return apology(f"Nicht so schnell! Bin Opa :(. Und du kannst maximal 1 mal am Tag eine komplette Generierung \
        machen, weil's mein OPENAI API Key ist :D {e.description}", 429)

# Flask middleware because i'm behind a proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


@app.route("/")
def index():
    return render_template("index.html", version=VERSION)


@app.route("/render", methods=["GET"])
@limiter.limit("1/day", override_defaults=True)
def render():
    if request.method == "GET":
        fname, lname = request.args.get("validationCustom01"), request.args.get(
            "validationCustom02"
        )
        # try:
        #     name = str(fname)
        #     name1 = str(lname)
        # except BaseException as e:
        #     return render_template("error.html", e=e)
        name = f'{fname} {lname}'
        link = main(name)
        return render_template('download.html', link=link)

@app.route('/login', methods=['POST', 'GET'])
def login():

    session.clear()

    if request.method != 'POST':
        return render_template("login.html")
    # Ensure username was submitted
    if not request.form.get("username"):
        return apology("must provide username", 403)

    # Ensure password was submitted
    elif not request.form.get("password"):
        return apology("must provide password", 403)
        


if __name__ == "__main__":
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
        user = os.environ['user_moodle']
        password = os.environ['pw_moodle']
    except KeyError:
        print("Please provide an OPENAI API key with EXPORT OPENAI_API_KEY=Your_Key")
    else:
        # print(main('Max Weimann'))
        serve(app, host=conf['server']['host'], port=conf['server']['port'])