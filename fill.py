import datetime
import os
import textwrap
from subprocess import run
from logging import log, basicConfig

import openai
import requests
from flask import Flask, jsonify, make_response, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://useyourown:useyourown@10.0.0.103/example'
db.init_app(app)

# Limit the rate to the render function
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1/second"],
    storage_uri="memory://",
)

# Generic ratelimit error handler, atm json output
# ToDO render_template with error429.html
@app.errorhandler(429)
def ratelimit_handler(e):
    return make_response(
            jsonify(error=f"Nicht so schnell! Bin Opa :( {e.description}")
            , 429
    )

version = 'v0.1.0-alpha3'

# Flask middleware because i'm behind a proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)


@app.route('/')
def index():
    return render_template('index.html', version=version)

@app.route('/render', methods=["GET"])
@limiter.limit("1/hour", override_defaults=True)
def render():
    if request.method == 'GET':
        fname, lname = request.args.get('validationCustom01'), request.args.get('validationCustom02')
        name = f'{fname} {lname}'
        return main(name)

@app.route('/kljson')
def kljson():
    return make_response(jsonify(error=data))

def write_zusammenfassung(collected_text: list, tokens: int = 700, is_long: bool = False) -> str:
    """
    Args:
        collected_text (list): _description_
        tokens (int, optional): _description_. Defaults to 700.
        is_long (bool, optional): _description_. Defaults to False.

    Returns:
        str: Zusammenfassung from a whole week as string
    """
    if is_long:
        print('Too long')
        collected_text[0] = 'Fasse folgenden Text zusammen und vergesse keine Fachbegriffe aus. \
            Schreibe es fuer einen Ausbildungsnachweis, aber erwaehne es nicht. Achte darauf nicht mehr als 680 Zeichen zu schreiben. \
            Schreibe auf Deutsch!'
    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "user", "content": ''.join(collected_text)}],
        max_tokens = tokens)

    max_lenght = 66*11
    zusammenfassung = chat_completion.choices[0].message.content

    if len(zusammenfassung) > max_lenght:
        write_zusammenfassung(collected_text, tokens=tokens-20, is_long=True)

    return zusammenfassung


def get_sunday_of_week(week, year):
    sunday = datetime.datetime.strptime(f'{year}-W{week}-7', '%G-W%V-%u')
    return sunday.strftime('%d.%m.%Y')

def write_pdf(calendar_week, jahr, name, type):
    global collected_text
    # Read the PDF file
    reader = PdfReader('daily.pdf') if type == 'daily' else PdfReader('weekly.pdf')
    #Open the writer
    writer = PdfWriter()
    # Read pages
    page = reader.pages[0]
    page2 = reader.pages[1]

    writer.add_page(page)
    writer.add_page(page2)

    if type == 'daily':
        pdf_name = f'Tägliches Berichtsheft KW{calendar_week}.pdf'
        i = 0
        m = 0
        form_values_new = {}

        for k, v in form_values.items():
            splitted_text = textwrap.wrap(v, width = 75)
            for i, line in enumerate(splitted_text):
                form_values_new[f'{k}{i + 1}'] = line
                m += 1
            m += 1
        zip(form_values_new, form_values)
    else:
        pdf_name = f'Wöchentliches Berichtsheft KW{calendar_week}.pdf'
        form_values['76'] = '40'
        form_values['78'] = '40'
        split_string = textwrap.wrap(write_zusammenfassung(collected_text), width=75)
        for i, line in enumerate(split_string):
            form_values[f'B{i + 1}'] = line

    form_values['Kalenderwoche'] = calendar_week
    form_values['Ausbildungsnachweis'] = str(int(calendar_week) - 24)
    form_values['Datum'] = get_sunday_of_week(calendar_week, jahr)
    form_values['Name'] = str(name)


    form = reader.get_form_text_fields()

    writer.update_page_form_field_values(writer.pages[0], form_values)

    with open(os.path.join(save, pdf_name), "wb") as output_stream:
        writer.write(output_stream)

def main(name):
    print(name)
    global raw, save, collected_text, values_daily, form_values
    raw = '/root/pdf_filler/raw'
    save = '/root/pdf_filler/saved'

    prompt_zusammenfassung = 'Fasse folgenden Text zusammen und lasse keine Fachbegriffe aus. Schreibe es fuer einen Ausbildungsnachweis. Schreibe auf Deutsch!'
    collected_text = [prompt_zusammenfassung]
    # Get the current date
    current_date = datetime.date.today()

    # Determine the actual calendar week
    calendar_week = str(current_date.isocalendar()[1])

    form_values = {}
    for root, dirs, files in os.walk(raw):
        # global collected_text
        files.sort(reverse=True)
        for file in files:
            if os.path.isfile(os.path.join(root, file)):
                date_object = datetime.datetime.strptime(str(file), "%d.%m.%y")
                tagname, jahr = date_object.strftime("%A"), date_object.strftime("%Y")
                with open(os.path.join(root, file), 'r') as f:
                    a = f.read()
                    if calendar_week == date_object.strftime("%U"):
                        collected_text.append(a)
                        form_values[f'{tagname}'] = a.replace('\n', '; ')
                        if len(collected_text) == 6:
                            write_pdf(calendar_week, jahr, name, type='weekly')
                            write_pdf(calendar_week, jahr, name, type='daily')
                            collected_text = [prompt_zusammenfassung]
                            calendar_week = date_object.strftime("%U")
                        continue
                    else:
                        write_pdf(calendar_week, jahr, name, type='weekly')
                        write_pdf(calendar_week, jahr, name, type='daily')
                        collected_text = [prompt_zusammenfassung, a]
                        form_values[f'{tagname}'] = a.replace('\n', '; ')
                        calendar_week = date_object.strftime('%U')
            form_values.clear()

    run(['zip', '-r', '/root/pdf_filler/berichtsheft.zip', '/root/pdf_filler/saved/'])
    zip_file = {'file': open('berichtsheft.zip', "rb")}
    upload = requests.post('https://api.letsupload.cc/upload', files=zip_file)

    return (upload.json()['data']['file']['url']['short'])

if __name__ == "__main__":
    try:
        openai.api_key = os.environ['OPENAI_API_KEY']
    except KeyError:
        print('Please provide an OPENAI API key with EXPORT OPENAI_API_KEY = Your Key')
    else:
        main('Max Weimann')
        #app.run(host="0.0.0.0", debug=True)

    
                
                





