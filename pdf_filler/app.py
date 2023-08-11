import os
import logging as log

import openai
from const import VERSION
from fill import main
from flask import (Flask, flash, make_response, render_template, request,
                   session)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from helpers import apology, login_required
from waitress import serve
# from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from yaml import safe_load
from dotenv import load_dotenv

from flask_session import Session

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


# Generic ratelimit error handler
@app.errorhandler(429)
def ratelimit_handler(e):
    return apology(f"Nicht so schnell! Bin Opa :(. Und du kannst maximal 1 mal am Tag eine komplette Generierung \
        machen, weil's mein OPENAI API Key ist :D {e.description}", 429)

# Flask middleware because i'm behind a proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


@app.route("/")
def index():
    return render_template("index.html", version=VERSION)


@app.route("/generator", methods=["GET", "POST"])
@limiter.limit("1/day", override_defaults=True)
def generator():
    if request.method != "POST":
        return render_template('generator.html', version=VERSION)
    
    fname, lname = request.args.get("validationCustom01"), request.args.get(
        "validationCustom02"
    )
    link = main(f'{fname} {lname}', conf)
    return render_template('download.html', link=link)

@app.route('/login', methods=['POST', 'GET'])
def login():

    session.clear()

    if request.method != 'POST':
        return render_template("login.html", version=VERSION)
    # Ensure username was submitted
    if not request.form.get("username"):
        return apology("must provide username", 403)

    # Ensure password was submitted
    elif not request.form.get("password"):
        return apology("must provide password", 403)
        


if __name__ == "__main__":
    load_dotenv()

    log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO
    )
    log.getLogger("httpx").setLevel(log.WARNING)
    required_values = ['OPENAI_API_KEY', 'LOCATION']
    if missing_values := [value for value in required_values if os.environ.get(value) is None]:
        log.error(f'The following environment values are missing in your .env: {", ".join(missing_values)}')
        exit(1)
    conf = {
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'USER': os.environ.get('USER'),
        'PW': os.environ.get('PW'),
        'HOST': os.environ.get('HOST', '127.0.0.1'),
        'PORT': os.environ.get('PORT', 5000),
        'LOCATION': os.environ.get('LOCATION', '/app/data/')
    }

    # print(main('Max Weimann'))
    # serve(app, host=conf['server']['host'], port=conf['server']['port'])
    app.run(host=conf['HOST'], port=conf['PORT'], debug=True)