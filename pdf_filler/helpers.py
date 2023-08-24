from flask import redirect, render_template, request, session
from functools import wraps
import os
from datetime import datetime, timedelta

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def check_time(timestamp) -> bool:
    current_time = datetime.now()
    elapsed_time = current_time - timestamp
    return elapsed_time >= timedelta(hours=24)

def is_old(file_path: str) -> bool:
    stat_result = os.stat(file_path)
    last_modification_time = datetime.fromtimestamp(stat_result.st_mtime)
    current_time = datetime.now()
    time_difference = current_time - last_modification_time
    return time_difference > timedelta(hours=24)