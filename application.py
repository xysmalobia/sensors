import MySQLdb
import MySQLdb.cursors
import mydb

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# connect to mysql database
DB = mydb.disconnectSafeConnect(read_default_group='client', port=0, database='xysmalobia$default', cursorclass=MySQLdb.cursors.DictCursor)
db = DB.cursor()


@app.route("/")
@login_required
def index():
    """Show frontpage"""

    # query user_id and username
    user_id = session["user_id"]
    db.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    rows = db.fetchall()
    for row in rows:
        username = row['username']

        return render_template("index.html", username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        username = request.form.get("username")
        db.execute("SELECT COUNT(username) FROM users WHERE username=%s", (username,))
        results = db.fetchall()

        # Ensure username exists
        for result in results:
            count = result['COUNT(username)']
            if count != 1:
                return apology("invalid username", 403)

        # Ensure password is correct
        password = request.form.get("password")
        db.execute("SELECT hash FROM users WHERE username=%s", (username,))
        results = db.fetchall()

        for result in results:
            hash = result['hash']
            if not check_password_hash(hash, password):
                return apology("invalid password", 403)
                DB.commit()

        # Remember which user has logged in
        db.execute("SELECT * FROM users WHERE username=%s", (username,))
        rows = db.fetchall()
        for row in rows:
            session["user_id"] = row['id']

        user_id = session["user_id"]

        # Flash alert
        flash ("Successfully logged in.")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        return render_template("login.html")


@app.route("/chart")
@login_required
def chart():
    """show the latest charts with chart.js"""

    # get bm280 reads
    db.execute("SELECT temperature, humidity FROM sensor ORDER BY id DESC")
    values = db.fetchmany(size=15)

    db.execute("SELECT date FROM sensor ORDER BY id DESC")
    labels = db.fetchmany(size=15)

    # get particle reads
    db.execute("SELECT pm1, pm2, pm10 FROM sensor ORDER BY id DESC")
    particles = db.fetchmany(size=15)

    # get gas reads
    db.execute("SELECT gasr, gaso, gasn FROM sensor ORDER BY id DESC")
    gas = db.fetchmany(size=15)

    return render_template('chart.html', values=values, labels=labels, particles=particles, gas=gas)


@app.route("/readings")
@login_required
def readings():
    """show latest sensor readings"""

    user_id = session["user_id"]

    # get sensor reads
    db.execute("SELECT * FROM sensor ORDER BY id DESC")
    rows = db.fetchall()

    return render_template("readings.html", rows=rows)


@app.route("/profile")
@login_required
def profile():
    """show user profile"""

    # query user_id and username
    user_id = session["user_id"]
    db.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    rows = db.fetchall()
    for row in rows:
        username = row['username']

    return render_template("profile.html", username=username)


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """change user password"""

    if request.method == "POST":

        # query user_id and username
        user_id = session["user_id"]
        db.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        rows = db.fetchall()
        for row in rows:
            username = row['username']

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmatory password was submitted
        if not request.form.get("confirmation"):
            return apology("must provide password twice", 400)

        # Ensure password matches confirmation
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        password = request.form.get("password")
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        db.execute("UPDATE users SET hash = %s WHERE id = %s", (hash, user_id,))
        DB.commit()

        flash ("Password changed.")

        # Redirect user to home page
        return redirect("/")

    elif request.method == "GET":

        # query user_id and username
        user_id = session["user_id"]
        db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        rows = db.fetchall()
        for row in rows:
            username = row['username']
            DB.commit()

            return render_template("password.html", username=username)


@app.route("/setup")
@login_required
def setup():
    """Show workflow and setup"""

    return render_template("setup.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    flash ("Logged out.")

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached page via POST
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmatory password was submitted
        if not request.form.get("confirmation"):
            return apology("must provide password twice", 400)

        # Ensure password matches confirmation
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # Ensure username is not taken
        username = request.form.get("username")
        db.execute("SELECT COUNT(username) FROM users WHERE username = %s", (username,))

        # if not taken add user to db
        rows = db.fetchall()
        for row in rows:
            count = row['COUNT(username)']
            if count == 1:
                return apology("username is taken", 400)

            else:
                username = request.form.get("username")
                password = request.form.get("password")
                hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

                db.execute("INSERT INTO users (username, hash) VALUES(%s, %s)", (username, hash,))
                DB.commit()

        flash ("Successfully registered user.")

        # Redirect user to home page
        return redirect("/")

    elif request.method == "GET":
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
