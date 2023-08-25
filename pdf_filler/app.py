import logging as log
import os
import contextlib
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import (Flask, flash, make_response, render_template, request,
                   session, redirect, send_file, url_for)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from helpers import apology, login_required, is_old
from waitress import serve
# from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from const import VERSION
from fill import fill
from homeoffice import main as ho
from homeoffice import login_user, getUsername

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

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("home.html", data=data)


@app.route("/generator", methods=["GET", "POST"])
@limiter.limit("2/day", override_defaults=True)
def generator():
    if request.method != "POST":
        return render_template('generator.html', version=VERSION)
    
    fname, lname = request.form.get("name"), request.form.get(
        "surname"
    )
    link = f"{conf['LOCATION']}{fname} {lname}/bericht/berichtsheft.zip"
    if not os.path.isfile(link) and is_old:
        link = fill(f'{fname} {lname}', conf)

    return send_file(link, as_attachment=True, download_name=f"Berichtsheft_{fname}_{lname}.zip")

@app.route('/login', methods=['POST', 'GET'])
def login():
    global data

    session.clear()

    if request.method == 'POST':
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("An E-Mail is required", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("A Password is required", 403)

        if not login_user(request.form.get("username"), request.form.get('password')):
            return apology("Sorry, aber deine Moodle Daten sind falsch!", 403)

        data = {}
        

        session["user_id"] = getUsername()

        data[session['user_id']] = ho(request.form.get('username'), request.form.get('password'))
        return redirect('/')

    return render_template("login.html", version=VERSION)

@app.route('/logout', methods=['GET'])
def logout():

    session.clear()

    return redirect('/')

def main():
    global conf
    load_dotenv()

    log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO
    )
    log.getLogger("httpx").setLevel(log.WARNING)
    required_values = ['OPENAI_API_KEY']
    if missing_values := [value for value in required_values if os.environ.get(value) is None]:
        log.error(f'The following environment values are missing in your .env: {", ".join(missing_values)}')
        exit(1)
    conf = {
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'USER': os.environ.get('MOODLE_USER'),
        'PW': os.environ.get('PW'),
        'HOSTIP': os.environ.get('HOSTIP', '127.0.0.1'),
        'PORT': os.environ.get('PORT', 5000),
        'LOCATION': os.environ.get('LOCATION', '/app/data/'),
        'LAST_CHECK': datetime.now() - timedelta(hours=24)
    }
    with contextlib.suppress(BaseException):
        # shutil.rmtree(conf['LOCATION'])
        os.makedirs(f"{conf['LOCATION']}/pdf")
    serve(app, host=conf['HOSTIP'], port=conf['PORT'])


if __name__ == "__main__":
    main()
    # app.run(host=conf['HOSTIP'], port=conf['PORT'], debug=True)
