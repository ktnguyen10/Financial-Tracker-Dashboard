import os
import string
from flask import current_app as server
from flask import Flask, Blueprint, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from helpers import login_required
from gen_database import init_database, read_file_to_db, dict_factory


UPLOAD_FOLDER = os.path.join('financial_dashboard/staticFiles', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'csv'}
# flask_app.register_blueprint(dash_app, url_prefix="/dashboard")

# server = Flask(__name__)
server.secret_key = 'abc123'
conn, curs = init_database()
server.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
server.config["SESSION_TYPE"] = "filesystem"
Session(server)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def flash_n_print(message):
    flash(message)
    print(message)


@server.route("/")
@login_required
def homepage():
    return render_template("homepage.html")


@server.route("/login", methods=["GET", "POST"])
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

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@server.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@server.route('/upload', methods=['GET', 'POST'])
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
            print(file.filename)
            if file.filename == '':
                flash_n_print('No files')
                return render_template('upload.html')
            if file and allowed_file(file.filename):
                official_filename = secure_filename(file.filename)
                filenames.append(official_filename)

                # Rename the file in case of spaces
                if file.filename != official_filename:
                    file.filename = official_filename
                print(file.filename + ' = ' + official_filename)
                file.save(os.path.join(server.config['UPLOAD_FOLDER'], official_filename))
                session['uploaded_data_file_path'] = os.path.join(server.config['UPLOAD_FOLDER'], official_filename)
                read_file_to_db(conn, curs, session.get('uploaded_data_file_path', None), session.get("user_id"))
                # file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        flash_n_print('Files uploaded successfully')
        return render_template('uploaded.html', filenames=filenames)
    else:
        return render_template('upload.html')


@server.route("/uploaded", methods=["POST"])
@login_required
def uploaded_file():
    """Return to stock quote page."""
    if request.method == "POST":
        return render_template("uploaded.html")


@server.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash('Please enter a username')
            return redirect('register')

        curs.execute("SELECT username FROM users")
        if request.form.get("username") in [i["username"] for i in curs.fetchall()]:
            flash('Username already taken')
            return redirect('register')

        # Ensure password was submitted
        if not request.form.get("password"):
            flash('Please enter a password')
            return redirect('register')

        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            flash('Must confirm password')
            return redirect('register')

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            flash('Passwords must match')
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
                flash('password must contain at least 1 number or 1 capital letter')
                return redirect('register')

        # Hash password
        pw_hash = generate_password_hash(request.form.get("password"))

        # Insert user information into users table with initial cash value of 10000
        curs.execute(
            "INSERT INTO users (username, hash) VALUES(?, ?)",
            (str(request.form.get("username")), pw_hash)
        )
        conn.commit()
        # Notify that registration is complete!
        print('Successful Registration!')

        return redirect("/login")
    else:
        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("register.html")

