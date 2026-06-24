from flask import *
from werkzeug.security import generate_password_hash
from db import conn
app = Flask(__name__)
app.secret_key="krishna123"

from auth.routes import auth
app.register_blueprint(auth)

from jobs.routes import jobs
app.register_blueprint(jobs)
@app.route("/dashboard",methods=["GET"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    role = session["role"]
    if role == "recruiter":
        return redirect(url_for("jobs.recruiter"))
    return redirect(url_for("jobs.candidate"))
if __name__ == "__main__":
    app.run(debug=True)