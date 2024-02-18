import os
import string
import sqlite3
from helpers import login_required
from login_manager import LoginManager
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask_session import Session
from financial_dashboard import app
from financial_dashboard.routes import curs, conn
from financial_dashboard.database import Database
from financial_dashboard.budget import Budget
from financial_dashboard.dashboard.data_cleanup import gen_dataframe
from flask import flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash


ALLOWED_EXTENSIONS = {'txt', 'csv'}
Session(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def flash_n_print(message):
    flash(message + '\n')
    print(message + '\n')


@app.route("/")
def index():
    lm = LoginManager()
    if lm.get_current_user() != 'no_login':
        return redirect('/homepage')
    else:
        return redirect('/login')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash('Please enter a valid username')
            return redirect('/login')

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('Please enter a valid password')
            return redirect('/login')

        # Query database for username
        curs.execute(
            "SELECT * FROM users WHERE username LIKE (?)", (request.form.get("username"),)
        )
        rows = curs.fetchall()
        print(len(rows))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash_n_print('Invalid username and/or password')
            return redirect('/login')

        # Remember which user has logged in
        session["user_id"] = rows[0]["username"]
        lm = LoginManager()
        lm.store_current_user(session["user_id"])

        # Redirect user to home page
        return redirect("/homepage")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/link_to_dash")
@login_required
def render_dashboard():
    return redirect('/dashboard/')


@app.route("/homepage")
@login_required
def homepage():
    lm = LoginManager()
    username = lm.get_current_user()
    data, _, _, _ = gen_dataframe(curs, username)
    current_month = datetime.now().month
    current_year = datetime.now().year

    previous_month = (datetime.utcnow().replace(day=1) - timedelta(days=1)).month
    if previous_month == 12:
        previous_year = datetime.now().year - 1
    else:
        previous_year = current_year

    try:
        filtered_data = data[(data['date'].dt.month == current_month) &
                             (data['date'].dt.year == current_year) &
                             (data['custom_category'] != 'Payment')]
        spend = filtered_data['amount'].sum()

        filtered_data = data[(data['date'].dt.month == previous_month) &
                             (data['date'].dt.year == previous_year) &
                             (data['custom_category'] != 'Payment') &
                             (data["description"].apply(lambda x: 'payment' not in x.lower()))]
        previous_spend = filtered_data['amount'].sum()
    except AttributeError:
        spend = 0
        previous_spend = 0

    return render_template("homepage.html",
                           username=username, spend="$" + str(round(spend, 2)), curr_month=current_month,
                           curr_year=current_year, prev_spend="$" + str(round(previous_spend, 2)),
                           prev_month=previous_month, prev_year=previous_year)


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    lm = LoginManager()
    lm.store_current_user('')
    # Redirect user to login form
    return redirect("/")


@app.route("/profile")
@login_required
def user_profile():
    # to update
    return render_template("/profile")


@app.route("/budget")
@login_required
def see_budget():
    # to update
    budget = Budget()
    return render_template("/budget", budget=budget)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash_n_print('No file part')
            return render_template('upload.html')
        files = request.files.getlist("file")

        # List of files to display on webpage
        filenames = []
        for file in files:
            # print(file.filename)
            if file.filename == '':
                flash_n_print('No files')
                return render_template('upload.html')
            if file and allowed_file(file.filename):
                official_filename = secure_filename(file.filename)
                filenames.append(official_filename)

                # Rename the file in case of spaces
                if file.filename != official_filename:
                    file.filename = official_filename
                # print(file.filename + ' = ' + official_filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], official_filename))
                session['uploaded_data_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], official_filename)
                try:
                    db = Database()
                    db.read_file_to_db(session.get('uploaded_data_file_path', None), session.get("user_id"))
                except sqlite3.OperationalError:
                    flash_n_print('Failed to upload data to the database. Check column and type compatibility!')
                except:
                    flash_n_print('Failed to upload file(s). Ensure that they are in the correct format!')

                # file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        flash_n_print('Files uploaded successfully')
        return render_template('uploaded.html', filenames=filenames)
    else:
        return render_template('upload.html')


@app.route("/uploaded", methods=["POST"])
@login_required
def uploaded_file():
    """Return to stock quote page."""
    if request.method == "POST":
        return render_template("uploaded.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash_n_print('Please enter a username')
            return redirect('register')

        curs.execute("SELECT username FROM users")
        if request.form.get("username") in [i["username"] for i in curs.fetchall()]:
            flash_n_print('Username already taken')
            return redirect('register')

        # Ensure password was submitted
        if not request.form.get("password"):
            flash_n_print('Please enter a password')
            return redirect('register')

        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            flash_n_print('Must confirm password')
            return redirect('register')

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            flash_n_print('Passwords must match')
            return redirect('register')

        elif not request.form.get("annualIncome"):
            flash_n_print('Please enter an annual income!')
            return redirect('register')

        # check password strength
        elif request.form.get("password"):
            count = 0
            for char in request.form.get("password"):
                if char in string.ascii_uppercase or char.isnumeric():
                    break
                else:
                    count += 1
            if count == len(request.form.get("password")):
                flash_n_print('password must contain at least 1 number or 1 capital letter')
                return redirect('register')

        # Hash password
        pw_hash = generate_password_hash(request.form.get("password"))

        # Get income
        annual_income = request.form.get("annualIncome")
        if not request.form.get("sideIncome"):
            side_income = 0
        else:
            side_income = request.form.get("sideIncome")

        # Insert user information into users table with initial cash value of 10000
        curs.execute(
            "INSERT INTO users (username, hash, annual_income, side_income) VALUES(?, ?, ?, ?)",
            (str(request.form.get("username")), pw_hash, annual_income, side_income)
        )
        conn.commit()
        # Notify that registration is complete!
        flash_n_print('Successful Registration!')

        return redirect("/login")
    else:
        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("register.html")

