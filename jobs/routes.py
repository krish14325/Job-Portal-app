from flask import *
from db import conn 
from werkzeug.utils import secure_filename
import os
from flask import send_from_directory
jobs = Blueprint("jobs" , __name__)

@jobs.route("/recruiter" , methods=["GET","POST"])
def recruiter():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    if request.method == "POST":
        return redirect(url_for("jobs.createjob"))
    query = """
            SELECT USERNAME
            FROM 
            USERS
            WHERE USER_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    username = cur.fetchone()
    query = """
            SELECT COUNT(*)
            FROM JOBS
            WHERE RECRUITER_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    found = cur.fetchone()
    query = """
            SELECT COUNT(*)
            FROM APPLICATIONS
            JOIN JOBS
            ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
            WHERE RECRUITER_ID = %s AND STATUS = "accepted"
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    accept = cur.fetchone()
    query = """
            SELECT COUNT(*)
            FROM APPLICATIONS
            JOIN JOBS
            ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
            WHERE RECRUITER_ID = %s AND STATUS = "rejected"
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    reject = cur.fetchone()
    query = """
            SELECT COUNT(*)
            FROM APPLICATIONS
            JOIN JOBS
            ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
            WHERE RECRUITER_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    applicants = cur.fetchone()
    return render_template("recruiter.html" ,applicants=applicants[0], total=found[0] , accepted=accept[0] , rejected=reject[0] , username=username[0])

@jobs.route("/candidate" , methods=["GET"])
def candidate():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    query = """
            SELECT USERNAME
            FROM 
            USERS
            WHERE USER_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    username = cur.fetchone()
    query = """
            SELECT COUNT(*)
            FROM 
            APPLICATIONS
            WHERE CANDIDATE_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    found = cur.fetchone()
    query = """
            SELECT COUNT(*)
            FROM 
            APPLICATIONS
            WHERE CANDIDATE_ID = %s AND STATUS = "accepted"
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    accept = cur.fetchone()
    query = """
            SELECT COUNT(*)
            FROM 
            APPLICATIONS
            WHERE CANDIDATE_ID = %s AND STATUS = "rejected"
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    reject = cur.fetchone()
    query = """
            SELECT *
            FROM JOBS
            ORDER BY RAND()
            LIMIT 2
            """
    cur = conn.cursor()
    cur.execute(query)
    job = cur.fetchall()
    return render_template("candidate.html" ,job=job, total=found[0] , accepted=accept[0] , rejected=reject[0] , username=username[0])

    
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

@jobs.route("/viewapplicants", methods=["GET","POST"])
def viewapplicants():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    
    if request.method == "GET":
        query = """
                SELECT JOBS.TITLE , USERS.USERNAME , USERS.EMAIL , APPLICATIONS.APPLIED_AT , APPLICATIONS.RESUME , APPLICATIONS.APPLICATION_ID
                FROM APPLICATIONS
                JOIN JOBS
                ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
                JOIN USERS
                ON APPLICATIONS.CANDIDATE_ID = USERS.USER_ID
                WHERE RECRUITER_ID = %s
                """
        values = (user , )
        cur = conn.cursor()
        cur.execute(query, values)
        found = cur.fetchall()
        if found:
            return render_template("viewapplicants.html", application=found)
        flash("No Applicants Applied Yet","Error")
        return render_template("viewapplicants.html",application=None)
    
@jobs.route("/uploads/<filename>")
def uploadfilename(filename):
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )
    
@jobs.route("/deletejob",methods=["POST"])
def deletejob():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    job_id = request.form["job_id"]
    print(job_id)
    query = """
                SELECT * 
                FROM JOBS
                WHERE RECRUITER_ID = %s AND JOB_ID = %s
                """
    values = (user , job_id)
    cur = conn.cursor()
    cur.execute(query,values)
    found = cur.fetchone()
    if found:
        query = """
                    DELETE 
                    FROM JOBS 
                    WHERE RECRUITER_ID = %s AND JOB_ID = %s
                    """
        values = (user , job_id)
        cur = conn.cursor()
        cur.execute(query,values)
        conn.commit()
        flash("Job Removed Sucessfully","Success")
        return redirect(url_for("jobs.viewjobs"))
    flash("Job Not Found","Error")
    return redirect(url_for("jobs.viewjobs"))

@jobs.route("/myapplications",methods=["GET"])
def myapplications():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    query = """
            SELECT JOBS.TITLE , JOBS.LOCATION , JOBS.SALARY , STATUS
            FROM APPLICATIONS
            JOIN JOBS
            ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
            WHERE CANDIDATE_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query,values)
    found = cur.fetchall()
    if not found:
        flash("No Jobs Applied","Error")
        return render_template("myapplications.html",applications=None)
    return render_template("myapplications.html",applications=found)

@jobs.route("/status", methods=["POST"])
def status():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    email = request.form["email"]
    application_id = request.form["application_id"]  # ✅ get directly from form

    if "accepted" in request.form:
        new_status = "accepted"
        message = "Resume Accepted"
    elif "rejected" in request.form:
        new_status = "rejected"
        message = "Resume Rejected"
    else:
        flash("Invalid Action", "Error")
        return redirect(url_for("jobs.viewapplicants"))

    cur = conn.cursor(buffered=True)

    # verify candidate exists
    cur.execute("SELECT USER_ID FROM USERS WHERE EMAIL = %s", (email,))
    found = cur.fetchone()
    if not found:
        flash("User Not Found", "Error")
        return redirect(url_for("jobs.viewapplicants"))

    # update using application_id directly — no need to search for it!
    cur.execute(
        "UPDATE APPLICATIONS SET STATUS = %s WHERE APPLICATION_ID = %s",
        (new_status, application_id)
    )
    conn.commit()
    flash(message, "Success")
    return redirect(url_for("jobs.viewapplicants"))

@jobs.route("/shortlisted" , methods=["GET"])
def shortlisted():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    query = """
            SELECT JOBS.TITLE ,LOCATION , SALARY ,  STATUS
            FROM APPLICATIONS
            JOIN JOBS
            ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
            WHERE CANDIDATE_ID = %s AND STATUS = "accepted";
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    found = cur.fetchall()
    if not found:
        return render_template("accepted.html" , accepted=None)
    return render_template("accepted.html",accepted=found)

@jobs.route("/rejected" , methods=["GET"])
def rejected():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    query = """
            SELECT JOBS.TITLE ,LOCATION , SALARY ,  STATUS
            FROM APPLICATIONS
            JOIN JOBS
            ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
            WHERE CANDIDATE_ID = %s AND STATUS = "rejected";
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query , values)
    found = cur.fetchall()
    if not found:
        return render_template("rejected.html" , accepted=None)
    return render_template("rejected.html",accepted=found)
    
@jobs.route("/postedjobs",methods=["GET"])
def postedjobs():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    query = """
            SELECT * 
            FROM JOBS
            WHERE RECRUITER_ID = %s
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query,values)
    found = cur.fetchall()
    if not found:
        return render_template("postedjobs.html" , posted=None)
    return render_template("postedjobs.html" , posted=found )

@jobs.route("/accepted",methods=["GET"])
def acceptedjobs():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    query = """
            SELECT USERNAME , TITLE , SALARY , STATUS
            FROM APPLICATIONS
            JOIN JOBS
            ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
            JOIN USERS
            ON APPLICATIONS.CANDIDATE_ID = USERS.USER_ID
            WHERE RECRUITER_ID = %s AND STATUS = "accepted";
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query,values)
    found = cur.fetchall()
    if not found:
        return render_template("acceptedresume.html" , posted=None)
    return render_template("acceptedresume.html" , posted=found )

@jobs.route("/rejectedresume",methods=["GET"])
def rejectedapplicants():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = session["user_id"]
    query = """
            SELECT USERNAME , TITLE , SALARY , STATUS
            FROM APPLICATIONS
            JOIN JOBS
            ON APPLICATIONS.JOB_ID = JOBS.JOB_ID
            JOIN USERS
            ON APPLICATIONS.CANDIDATE_ID = USERS.USER_ID
            WHERE RECRUITER_ID = %s AND STATUS = "rejected";
            """
    values = (user,)
    cur = conn.cursor()
    cur.execute(query,values)
    found = cur.fetchall()
    if not found:
        return render_template("rejectedresume.html" , posted=None)
    return render_template("rejectedresume.html" , posted=found )