from flask import * 
from werkzeug.security import generate_password_hash ,check_password_hash
from db import conn 
auth = Blueprint("auth", __name__)

@auth.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name  = request.form["name"]
        email  = request.form["email"]
        password  = request.form["password"]
        confirm  = request.form["confirm"]
        role = request.form["role"]
        if password != confirm:
            flash("Password Does Not Match" , "Error")
            return render_template("register.html")
        
        query = """
                SELECT *
                FROM USERS
                WHERE EMAIL = %s
                """
        values = (email,)
        cur = conn.cursor()
        cur.execute(query , values)
        found = cur.fetchone()
        if found:
            flash("Email Already Registered","Error")
            return render_template("register.html")
        hashed_password = generate_password_hash(password)
        query = """
                INSERT INTO USERS
                (USERNAME , EMAIL , PASSWORD , ROLE)
                VALUES
                (%s,%s,%s,%s)
                """
        values = (name , email , hashed_password , role)
        cur = conn.cursor()
        cur.execute(query,values)
        conn.commit()
        flash("User Registered Sucessfully","Success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email  = request.form["email"]
        password  = request.form["password"]
        
        query = """
                SELECT *
                FROM USERS
                WHERE EMAIL = %s
                """
        values = (email,)
        cur = conn.cursor()
        cur.execute(query , values)
        found = cur.fetchone()
        if found:
            stored_pass = found[3]
            if check_password_hash(stored_pass,password):
                session["user_id"] = found[0]
                session["email"] = found[2]
                session["role"] = found[4]
                flash("Login Sucessfull","Success")
                return redirect(url_for("dashboard"))
            flash("Invalid Email / Password","Error")
            return render_template("login.html")
        flash("User Not Found","Error")
        return render_template("login.html")
    return render_template("login.html")

@auth.route("/logout", methods=["POST"])
def logout():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    session.clear()
    flash("Logout Sucessfully","Success")
    return redirect(url_for("auth.login"))