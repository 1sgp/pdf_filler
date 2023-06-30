from PyPDF2 import PdfReader, PdfWriter
import datetime
from subprocess import run
import requests
import openai
import os
import textwrap
from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Limit the rate to the render function
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2 per day", "1 per hour"],
    storage_uri="memory://",
)

version = 'v0.1.0-alpha2'

# Flask middleware because i'm behind a proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

@app.route('/')
@limiter.limit("1/second", override_defaults=True)
def index():
    return render_template('index.html', version=version)

@app.route('/render', methods=["GET"])
def render():
    if request.method == 'GET':
        fname, lname = request.args.get('validationCustom01'), request.args.get('validationCustom02')
        name = f'{fname} {lname}'
        return str(name)
        # return str(main(name))

def write_zusammenfassung(collected_text):
    # create a chat completion
    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": ''.join(collected_text)}])

    # print the chat completion
    return chat_completion.choices[0].message.content

def get_sunday_of_week(week, year):
    sunday = datetime.datetime.strptime(f'{year}-W{week}-7', '%G-W%V-%u')
    return sunday.strftime('%d.%m.%Y')

def write_weekly(calendar_week, jahr, name):
    global collected_text
    # Read the PDF file
    reader = PdfReader('weekly.pdf')
    #Open the writer
    writer = PdfWriter()
    # Read pages
    page = reader.pages[0]
    page2 = reader.pages[1]

    writer.add_page(page)
    writer.add_page(page2)

    split_string = textwrap.wrap(write_zusammenfassung(collected_text), width=82)
    for i, line in enumerate(split_string):
        values_weekly[f'B{i + 1}'] = line
    values_weekly['Kalenderwoche'] = calendar_week
    values_weekly['Ausbildungsnachweis'] = str(int(calendar_week) - 24)
    values_weekly['76'] = '40'
    values_weekly['78'] = '40'
    values_weekly['Datum'] = get_sunday_of_week(calendar_week, jahr)
    values_weekly['Name'] = str(name)


    

    pdf_name_weekly = f'Wöchentliches Berichtsheft KW{calendar_week}.pdf'

    form = reader.get_form_text_fields()

    writer.update_page_form_field_values(writer.pages[0], values_weekly)

    with open(os.path.join(save, pdf_name_weekly), "wb") as output_stream:
        writer.write(output_stream)

    values_weekly.clear()

def write_daily(calendar_week, jahr, name):
    global collected_text
    # Read the PDF file
    reader = PdfReader('daily.pdf')
    #Open the writer
    writer = PdfWriter()
    # Read pages
    page = reader.pages[0]
    page2 = reader.pages[1]

    writer.add_page(page)
    writer.add_page(page2)
    i = 0
    m = 0
    values_daily_new = {}

    for k, v in values_daily.items():
        splitted_text = textwrap.wrap(v, width = 82)
        for i, line in enumerate(splitted_text):
            values_daily_new[f'{k}{i + 1}'] = line
            m += 1
        m += 1
    values_daily_new['Kalenderwoche'] = calendar_week
    values_daily_new['Ausbildungsnachweis'] = str(int(calendar_week) - 24)
    # values_daily['76'] = '40'
    # values_daily['78'] = '40'
    values_daily_new['Datum'] = get_sunday_of_week(calendar_week, jahr)
    values_daily_new['Name'] = str(name)

    pdf_name_daily = f'Tägliches Berichtsheft KW{calendar_week}.pdf'

    form = reader.get_form_text_fields()

    writer.update_page_form_field_values(writer.pages[0], values_daily_new)

    with open(os.path.join(save, pdf_name_daily), "wb") as output_stream:
        writer.write(output_stream)

    values_daily.clear()
    values_daily_new.clear()

def main(name):
    print(name)
    global raw, save, collected_text, values_daily, values_weekly
    raw = '/root/pdf_filler/raw'
    save = '/root/pdf_filler/saved'

    prompt_zusammenfassung = 'Fasse folgenden Text zusammen und lasse keine Fachbegriffe aus. Schreibe es fuer ein Ausbildungsnachweis.'
    collected_text = [prompt_zusammenfassung]
    # Get the current date
    current_date = datetime.date.today()

    # Determine the actual calendar week
    calendar_week = str(current_date.isocalendar()[1])

    values_weekly = {}
    values_daily = {}
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
                        values_daily[f'{tagname}'] = a.replace('\n', '; ')
                        if len(collected_text) == 6:
                            write_weekly(calendar_week, jahr, name)
                            write_daily(calendar_week, jahr, name)
                            collected_text = [prompt_zusammenfassung]
                            calendar_week = date_object.strftime("%U")
                        continue
                    else:
                        write_weekly(calendar_week, jahr, name)
                        write_daily(calendar_week, jahr, name)
                        collected_text = [prompt_zusammenfassung, a]
                        values_daily[f'{tagname}'] = a.replace('\n', '; ')
                        calendar_week = date_object.strftime('%U')

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
        app.run(host="0.0.0.0", debug=True)
                
                





