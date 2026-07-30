from flask import Flask, render_template, request, redirect
from database import get_connection

print(" App Started")

app = Flask(__name__)

# Database Connection Test
try:
    conn = get_connection()

    if conn.is_connected():
        print(" Database Connected Successfully")
        conn.close()

except Exception as e:
    print(" Database Error:", e)


# Login Page
@app.route("/")
def home():
    return render_template("login.html")


# Login Authentication
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM users WHERE username=%s AND password=%s"

    cursor.execute(sql, (username, password))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return redirect("/dashboard")
    else:
        return " Invalid Username or Password"


# Dashboard
@app.route("/dashboard")
def dashboard():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Total Students
    cursor.execute("""
        SELECT COUNT(*) AS total_students
        FROM students
    """)
    total_students = cursor.fetchone()["total_students"]


    # Total Fees Collected
    cursor.execute("""
        SELECT COALESCE(SUM(paid_amount), 0) AS total_collected
        FROM fees
    """)
    total_collected = cursor.fetchone()["total_collected"]


    # Total Pending Balance
    cursor.execute("""
        SELECT COALESCE(SUM(balance), 0) AS total_balance
        FROM fees
    """)
    total_balance = cursor.fetchone()["total_balance"]


    # Today's Attendance
    cursor.execute("""
        SELECT COUNT(*) AS today_attendance
        FROM attendance
        WHERE attendance_date = CURDATE()
    """)
    today_attendance = cursor.fetchone()["today_attendance"]


    # Total Behaviour Records
    cursor.execute("""
        SELECT COUNT(*) AS total_behaviour
        FROM behaviour
    """)
    total_behaviour = cursor.fetchone()["total_behaviour"]


    # Today's Sessions
    cursor.execute("""
        SELECT COUNT(*) AS today_sessions
        FROM sessions
        WHERE session_date = CURDATE()
    """)
    today_sessions = cursor.fetchone()["today_sessions"]


    cursor.close()
    conn.close()


    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_collected=total_collected,
        total_balance=total_balance,
        today_attendance=today_attendance,
        total_behaviour=total_behaviour,
        today_sessions=today_sessions
    )

@app.route("/students")
def students():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students ORDER BY student_id DESC")

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("students.html", students=students)

@app.route("/save_student", methods=["POST"])
def save_student():

    student_name = request.form["student_name"]
    mobile = request.form["mobile"]
    email = request.form["email"]
    course = request.form["course"]
    batch = request.form["batch"]
    joining_date = request.form["joining_date"]
    fees = request.form["fees"]
    status = request.form["status"]

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO students
    (student_name, mobile, email, course, batch, joining_date, fees, status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        student_name,
        mobile,
        email,
        course,
        batch,
        joining_date,
        fees,
        status
    )

    cursor.execute(sql, values)
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/students")

@app.route("/delete_student/<int:id>")
def delete_student(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE student_id=%s", (id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/students")
@app.route("/edit_student/<int:id>")
def edit_student(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE student_id=%s",
        (id,)
    )

    student = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "edit_student.html",
        student=student
    )
@app.route("/update_student/<int:id>", methods=["POST"])
def update_student(id):

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    UPDATE students
    SET student_name=%s,
        mobile=%s,
        email=%s,
        course=%s,
        batch=%s,
        joining_date=%s,
        fees=%s,
        status=%s
    WHERE student_id=%s
    """

    values = (
        request.form["student_name"],
        request.form["mobile"],
        request.form["email"],
        request.form["course"],
        request.form["batch"],
        request.form["joining_date"],
        request.form["fees"],
        request.form["status"],
        id
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/students")
@app.route("/attendance")
def attendance():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students ORDER BY student_name")

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("attendance.html", students=students)
@app.route("/save_attendance", methods=["POST"])
def save_attendance():

    attendance_date = request.form["attendance_date"]

    student_ids = request.form.getlist("student_id[]")
    statuses = request.form.getlist("status[]")
    remarks = request.form.getlist("remarks[]")

    conn = get_connection()
    cursor = conn.cursor()

    for i in range(len(student_ids)):

        sql = """
        INSERT INTO attendance
        (student_id, attendance_date, status, remarks)
        VALUES (%s,%s,%s,%s)
        """

        values = (
            student_ids[i],
            attendance_date,
            statuses[i],
            remarks[i]
        )

        cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/attendance")

@app.route("/fees")
def fees():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students ORDER BY student_name")
    students = cursor.fetchall()

    cursor.execute("""
        SELECT
            fees.*,
            students.student_name
        FROM fees
        JOIN students
        ON fees.student_id = students.student_id
        ORDER BY fee_id DESC
    """)

    fees = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "fees.html",
        students=students,
        fees=fees
    )

# Generate Fee Bill
@app.route("/fee_bill/<int:fee_id>")
def fee_bill(fee_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            fees.*,
            students.student_name,
            students.mobile,
            students.email
        FROM fees
        JOIN students
        ON fees.student_id = students.student_id
        WHERE fees.fee_id = %s
    """, (fee_id,))

    fee = cursor.fetchone()

    cursor.close()
    conn.close()

    if not fee:
        return "Fee Record Not Found"

    return render_template(
        "fee_bill.html",
        fee=fee
    )

@app.route("/save_fees", methods=["POST"])
def save_fees():

    student_id = request.form["student_id"]
    payment_date = request.form["payment_date"]
    total_fees = request.form["total_fees"]
    paid_amount = request.form["paid_amount"]
    balance = request.form["balance"]
    payment_mode = request.form["payment_mode"]
    remarks = request.form["remarks"]

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO fees
    (student_id, payment_date, total_fees, paid_amount,
    balance, payment_mode, remarks)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        student_id,
        payment_date,
        total_fees,
        paid_amount,
        balance,
        payment_mode,
        remarks
    )

    cursor.execute(sql, values)
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/fees")

@app.route("/delete_fee/<int:fee_id>")
def delete_fee(fee_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM fees WHERE fee_id = %s",
        (fee_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/fees")

@app.route("/edit_fee/<int:fee_id>")
def edit_fee(fee_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM fees WHERE fee_id = %s",
        (fee_id,)
    )

    fee = cursor.fetchone()

    cursor.close()
    conn.close()

    if not fee:
        return "Fee Record Not Found"

    return render_template(
        "edit_fee.html",
        fee=fee
    )


@app.route("/update_fee/<int:fee_id>", methods=["POST"])
def update_fee(fee_id):

    student_id = request.form["student_id"]
    payment_date = request.form["payment_date"]
    total_fees = request.form["total_fees"]
    paid_amount = request.form["paid_amount"]
    balance = request.form["balance"]
    payment_mode = request.form["payment_mode"]
    remarks = request.form["remarks"]

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    UPDATE fees
    SET student_id = %s,
        payment_date = %s,
        total_fees = %s,
        paid_amount = %s,
        balance = %s,
        payment_mode = %s,
        remarks = %s
    WHERE fee_id = %s
    """

    values = (
        student_id,
        payment_date,
        total_fees,
        paid_amount,
        balance,
        payment_mode,
        remarks,
        fee_id
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/fees")

@app.route("/behaviour")
def behaviour():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students ORDER BY student_name"
    )

    students = cursor.fetchall()

    cursor.execute("""
        SELECT
            behaviour.*,
            students.student_name
        FROM behaviour
        JOIN students
        ON behaviour.student_id = students.student_id
        ORDER BY behaviour_id DESC
    """)

    behaviours = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "behaviour.html",
        students=students,
        behaviours=behaviours
    )


@app.route("/save_behaviour", methods=["POST"])
def save_behaviour():

    student_id = request.form["student_id"]
    behaviour_date = request.form["behaviour_date"]
    behaviour = request.form["behaviour"]
    remarks = request.form["remarks"]
    faculty = request.form["faculty"]

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO behaviour
    (student_id, behaviour_date, behaviour, remarks, faculty)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        student_id,
        behaviour_date,
        behaviour,
        remarks,
        faculty
    )

    cursor.execute(sql, values)
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/behaviour")

@app.route("/delete_behaviour/<int:behaviour_id>")
def delete_behaviour(behaviour_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM behaviour WHERE behaviour_id = %s",
        (behaviour_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/behaviour")

@app.route("/edit_behaviour/<int:behaviour_id>")
def edit_behaviour(behaviour_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM behaviour WHERE behaviour_id = %s",
        (behaviour_id,)
    )

    behaviour = cursor.fetchone()

    cursor.close()
    conn.close()

    if not behaviour:
        return "Behaviour Record Not Found"

    return render_template(
        "edit_behaviour.html",
        behaviour=behaviour
    )


@app.route("/update_behaviour/<int:behaviour_id>", methods=["POST"])
def update_behaviour(behaviour_id):

    student_id = request.form["student_id"]
    behaviour_date = request.form["behaviour_date"]
    behaviour_name = request.form["behaviour"]
    remarks = request.form["remarks"]
    faculty = request.form["faculty"]

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    UPDATE behaviour
    SET student_id = %s,
        behaviour_date = %s,
        behaviour = %s,
        remarks = %s,
        faculty = %s
    WHERE behaviour_id = %s
    """

    values = (
        student_id,
        behaviour_date,
        behaviour_name,
        remarks,
        faculty,
        behaviour_id
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/behaviour")

# Sessions Page
@app.route("/sessions")
def sessions():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM sessions
        ORDER BY session_date DESC, start_time DESC
    """)

    session_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "sessions.html",
        sessions=session_list
    )


# Save Session
@app.route("/save_session", methods=["POST"])
def save_session():

    session_name = request.form["session_name"]
    faculty = request.form["faculty"]
    session_date = request.form["session_date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    topic = request.form["topic"]
    remarks = request.form["remarks"]

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO sessions
    (session_name, faculty, session_date,
     start_time, end_time, topic, remarks)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        session_name,
        faculty,
        session_date,
        start_time,
        end_time,
        topic,
        remarks
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/sessions")

# Delete Session
@app.route("/delete_session/<int:session_id>")
def delete_session(session_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM sessions WHERE session_id = %s",
        (session_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/sessions")



if __name__ == "__main__":
    app.run(debug=True)