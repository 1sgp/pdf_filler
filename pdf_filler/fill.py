import os
import re
import textwrap
from datetime import datetime
# from logging import basicConfig, log
# trunk-ignore(bandit/B404)
from subprocess import run

import openai
import requests
from flask import Flask, jsonify, make_response, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# from flask_session import Session
# from flask_sqlalchemy import SQLAlchemy
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.middleware.proxy_fix import ProxyFix
from waitress import serve

import KlassenbuchAIO_a

weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

VERSION = "v0.1.0-beta"

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)
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
    return make_response(
        jsonify(error=f"Nicht so schnell! Bin Opa :(. Und du kannst maximal 1 mal am Tag eine komplette Generierung machen, weil's mein OPENAI API Key ist :D {e.description}"), 429
    )

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

def get_datename(key: str) -> str:
    date_time_parts = key.split(' - ')

    date_str = date_time_parts[0]
    time_str = date_time_parts[1]

    date = datetime.strptime(date_str, '%a, %d.%m.%y %H:%M')

    # end_time = datetime.strptime(time_str.split(' - ')[1], '%H:%M')
    return date.strftime('%A')

def get_year(key: str) -> int:
    date_time_parts = key.split(' - ')

    date_str = date_time_parts[0]
    time_str = date_time_parts[1]

    date = datetime.strptime(date_str, '%a, %d.%m.%y %H:%M')

    # end_time = datetime.strptime(time_str.split(' - ')[1], '%H:%M')
    return int(date.strftime('%Y'))


def get_calendar_week(key: str) -> int:
    date_time_parts = key.split(' ')

    date_str = date_time_parts[0]
    try:
        datee = datetime.strptime(date_str, '%a, %d.%m.%y %H:%M')
    except ValueError:
        date_time_parts2 = key.split('-')
        pattern = r"[\d.-]+"
        numbers = re.findall(pattern, date_time_parts2[0])
        datee = datetime.strptime(numbers[0], '%d.%m.%y')


    # end_time = datetime.strptime(time_str.split(' - ')[1], '%H:%M')
    return int(datee.strftime('%W'))

def get_sunday_of_week(week: int, year: int) -> str:
    sunday = datetime.strptime(f"{year}-W{week}-7", "%G-W%V-%u")
    return sunday.strftime("%d.%m.%Y")

def write_zusammenfassung(collected_text: str, tokens: int = 260, is_long: bool = False) -> str:
    # very often too long answer, need to optimize
    prompt_zsmfssng = "Fasse folgenden Text zusammen und lasse keine Fachbegriffe aus. \
    Achte darauf nicht mehr als 680 Zeichen zu schreiben. Schreibe auf Deutsch!"
    combined_text = [prompt_zsmfssng, collected_text]
    if is_long:
        print("Too long")
        combined_text[0] = 'Der Text muss extrem kuerzer zusammengefasst werden!. Schreibe auf Deutsch!'
    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": ''.join(combined_text)}],
        max_tokens=tokens,
    )

    max_lenght = 66 * 11
    zusammenfassung = chat_completion.choices[0].message.content

    if len(zusammenfassung) > max_lenght:
        write_zusammenfassung(collected_text, tokens=tokens - 20, is_long=True)

    return zusammenfassung

def write_pdf(name: str, form_values: dict, calendar_week: int, jahr: int) -> None:
    pdf_files = ("daily.pdf", "weekly.pdf")

    for pdf_file in pdf_files:
        pdf_path = os.path.join('/root/pdf_filler/pdf', pdf_file)
        reader = PdfReader(pdf_path)

        writer = PdfWriter()

        page = reader.pages[0]
        page2 = reader.pages[1]

        writer.add_page(page)
        writer.add_page(page2)

        form_values |= {
            "Kalenderwoche": calendar_week,
            "Ausbildungsnachweis": str(calendar_week - 24),
            "Datum": get_sunday_of_week(calendar_week, jahr),
            "Name": name,
        }
        if pdf_file == 'daily.pdf':
            form_values |= prepare_daily(name, form_values, calendar_week)
        else:
            form_values |= prepare_weekly(name, form_values, calendar_week)

        writer.update_page_form_field_values(writer.pages[0], form_values)
        writer.update_page_form_field_values(writer.pages[1], form_values)


        with open(os.path.join(f"/opt/pdf_filler/{name}/{form_values['pdf_name']}"), "wb") as output_stream:
            writer.write(output_stream)


def prepare_daily(name: str, form_values: dict, calendar_week: int) -> dict:
    form_values_new = {}
    form_values |= {
        "Montags": "8",
        "Dienstags": "8",
        "Mittwochs": "8",
        "Donnerstags": "8",
        "Freitags": "8",
        "Wochenstunden": "40",
        "pdf_name": f"Tägliches Berichtsheft KW{calendar_week}.pdf",
    }
    for k, v in form_values.items():
        if k in weekdays:
            splitted_text = textwrap.wrap(v, width=75)
            for i, line in enumerate(splitted_text):
                form_values_new[f"{k}{i + 1}"] = line

    form_values |= form_values_new

    return form_values


def prepare_weekly(name: str, form_values: dict, calendar_week: int) -> dict:
    form_values |= {
        "76": "40",
        "78": "40",
        'pdf_name': f"Wöchentliches Berichtsheft KW{calendar_week}.pdf",
    }
    week_text = [form_values[weekday] for weekday in weekdays]
    split_string = textwrap.wrap(write_zusammenfassung("".join(week_text)), width=75)
    for i, line in enumerate(split_string):
        form_values[f"B{i + 1}"] = line

    return form_values


def main(name: str) -> str:
    # print(name)
    kwargs=KlassenbuchAIO_a.main(user, password)
    calendar_week = 25
    form_values = {}
    run(['mkdir', '-p', f'/opt/pdf_filler/{name}/'])

    for k, v in kwargs.items():
        form_values = {}
        form_values = {'Bemerkungen des Auszubildenden': f'{k}'}
        for k1, v1 in v.items():
            if k1 == 'Datum' and v1 == 'Beschreibung':
                continue
            form_values[get_datename(k1)] = v1
            if k1.startswith('Fri'):
                write_pdf(name, form_values, calendar_week, get_year(k1))
                # Optimize this cause of holidays...
                calendar_week += 1

    return upload_to(name)


def upload_to(name: str) -> str:
    # trunk-ignore(bandit/B603)
    run(
        [
            "/usr/bin/zip",
            "-r",
            f"/opt/pdf_filler/{name}/berichtsheft.zip",
            f"/opt/pdf_filler/{name}/",
        ]
    )
    zip_file = {"file": open(f"/opt/pdf_filler/{name}/berichtsheft.zip", "rb")}
    try:
        upload = requests.post(
            "https://api.letsupload.cc/upload", files=zip_file, timeout=10
        )
    except BaseException as e:
        print(f"An error {e} occurred while uploading")

    return upload.json()["data"]["file"]["url"]["short"]


if __name__ == "__main__":
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
        user = os.environ['user_moodle']
        password = os.environ['pw_moodle']
    except KeyError:
        print("Please provide an OPENAI API key with EXPORT OPENAI_API_KEY=Your_Key")
    else:
        serve(app, host='10.0.0.105', port=5000)