# Very early alpha stage of a IHK FISI/FIAE? PDF Form Berichtsheft filler

This is only for improve in coding and cause we're lazy to write this shitty forms

## Known Bugs?
- PDF's only look fine in chrome. Firefox okay but looks ugly. Acrobat only shows text if you click on it. 

### Todo
Look at projects page but a little list
- [] Login Form / User Interface
- [] Add own notes to different berichtshefte
- [] Option to recreate the AI completion if not satisfied
- [] Login into your moodle to see HOMEOFFICE Calculator (@1sqp)
- [] make readme pretty x3

and more to come

#### Contribute code

1. Fork the repository on GitHub and clone your fork

2. Install a venv and the package dependencies
```bash
cd pdf_filler && python -m venv .venv && source .venv/bin/activate && python -r requirements.txt
```

3. Set your OpenAI API Key Environment variable
```bash
export OPENAI_API_KEY='Your Key'
```

4. Push to your fork and make a pull request to my repo :)

Special thanks to @1sgp for your contributions.