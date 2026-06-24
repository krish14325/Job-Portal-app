from flask import *
from db import conn 
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
    jobid = request.form["jobid"]
    title = request.form["title"]
    print(jobid)
    print(title)
    query = """
            SELECT JOBS.TITLE , JOBS.DESCRIPTION , JOBS.LOCATION , JOBS.SALARY , USERS.USERNAME
            FROM JOBS
            JOIN USERS
            ON JOBS.RECRUITER_ID = USERS.USER_ID
            WHERE USER_ID = %s AND TITLE = %s
            """
    values = (jobid, title)
    cur = conn.cursor()
    cur.execute(query , values)
    found2 = cur.fetchone()
    if not found2:
        flash("Job Does Not Exist","Error")
        return render_template("jobdetail.html" , jobs=found2)
    return render_template("jobdetail.html",jobs=found2)

        
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
    
