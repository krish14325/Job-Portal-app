from flask import *
from db import conn 
from werkzeug.utils import secure_filename
import os
jobs = Blueprint("jobs" , __name__)

@jobs.route("/recruiter" , methods=["GET","POST"])
def recruiter():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    if request.method == "POST":
        return redirect(url_for("jobs.createjob"))
    return render_template("recruiter.html")

@jobs.route("/candidate" , methods=["GET"])
def candidate():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    return render_template("candidate.html")

@jobs.route("/alljobs",methods=["GET","POST"])
def alljobs():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    if request.method == "GET":
        query = """
            SELECT *
            FROM JOBS
            """
        cur = conn.cursor()
        cur.execute(query)
        found = cur.fetchall()
        if not found:
            flash("No Jobs Created","Error")
            return render_template("alljobs.html")
        return render_template("alljobs.html" , job=found)
@jobs.route("/jobdetails",methods=["GET","POST"])
def jobdetails():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    role = session["role"]
    if request.method=="GET":
        jobid = request.args.get("jobid")
        title = request.args.get("title")
        query = """
                SELECT JOBS.TITLE , JOBS.DESCRIPTION , JOBS.LOCATION , JOBS.SALARY , USERS.USERNAME , JOB_ID
                FROM JOBS
                JOIN USERS
                ON JOBS.RECRUITER_ID = USERS.USER_ID
                WHERE USER_ID = %s AND TITLE = %s
                """
        values = (jobid, title)
        cur = conn.cursor()
        cur.execute(query , values)
        found = cur.fetchone()
        if not found:
            flash("Job Does Not Exist","Error")
            return render_template("jobdetail.html" , jobs=found)
        return render_template("jobdetail.html",jobs=found)
    if role!= "candidate":
        flash("Only Candidates Can Apply", "Error")
        return redirect(url_for("jobs.alljobs"))
    job_id = request.form["job_id"]
    query = """
            SELECT *
            FROM APPLICATIONS
            WHERE JOB_ID = %s AND CANDIDATE_ID = %s
            """
    values = (job_id,user)
    cur = conn.cursor()
    cur.execute(query,values)
    application = cur.fetchone()
    if application:
        flash("You Have Already Applied For This Job","Error")
        return redirect(url_for("jobs.alljobs"))
    query = """
            SELECT RESUME
            FROM USERS
            WHERE USER_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query,values)
    resume = cur.fetchone()
    if not resume or not resume[0]:
        flash("Please Upload Your Resume","Error")
        return render_template("jobdetail.html", jobs=None)
    query = """
            INSERT INTO APPLICATIONS
            (JOB_ID , CANDIDATE_ID , RESUME)
            VALUES
            (%s,%s,%s)
            """
    values = ( job_id , user , resume[0])
    cur = conn.cursor()
    cur.execute(query , values)
    conn.commit()
    flash("Applied Sucessfully","Success")
    return redirect(url_for("jobs.alljobs"))

@jobs.route("/createjobs" , methods=["GET","POST"])
def createjob():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session['user_id']
    if request.method == "POST":
        recruiter_id = request.form["id"]
        title = request.form["title"]
        Description = request.form["Description"]
        location = request.form["location"]
        salary = request.form["salary"]
        role = session["role"]
        query = """
                SELECT * 
                FROM USERS
                WHERE USER_ID = %s AND ROLE = %s
                """
        values = (recruiter_id, role)
        cur = conn.cursor()
        cur.execute(query,values)
        found  = cur.fetchone()
        if found:
            query = """
                    INSERT INTO JOBS
                    (RECRUITER_ID , TITLE , DESCRIPTION , LOCATION , SALARY)
                    values
                    (%s,%s,%s,%s,%s)
                    """
            values = (recruiter_id , title , Description , location , salary)
            cur = conn.cursor()
            cur.execute(query,values)
            conn.commit()
            flash("Job Posted" ,"Success")
            return redirect(url_for("dashboard"))
        flash("Recruiter Not Found","Error")
        return redirect(url_for("jobs.createjob"))
    return render_template("createjob.html")

@jobs.route("/viewjobs", methods=["GET","POST"])
def viewjobs():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    if request.method == "POST":
        return redirect(url_for("dashboard"))
    query = """
            SELECT *
            FROM JOBS
            WHERE RECRUITER_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query,values)
    found = cur.fetchall()
    if found:
        return render_template("viewjobs.html" , job=found)
    flash("No Jobs Created","Error")
    return render_template("viewjobs.html")

@jobs.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logout Sucessfully","Success")
    return redirect(url_for("auth.login"))
    
@jobs.route("/uploadresume", methods=["GET", "POST"])
def uploadresume():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]
    if request.method == "POST":
        resume = request.files["resume"]
        if resume.filename == "":
            flash("No File Selected", "Error")
            return redirect(url_for("jobs.uploadresume"))
        filename = f"{user_id}_{secure_filename(resume.filename)}"
        filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            filename
        )
        resume.save(filepath)
        query = """
        UPDATE USERS
        SET RESUME = %s
        WHERE USER_ID = %s
        """
        values = (filename, user_id)
        cur = conn.cursor()
        cur.execute(query, values)
        conn.commit()
        flash("Resume Uploaded Successfully", "Success")
        return redirect(url_for("dashboard"))
    return render_template("uploadresume.html")