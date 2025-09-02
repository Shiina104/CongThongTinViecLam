from flask import render_template, redirect, request, session, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from app import app, db, login_manager
from app.dao import auth_user, register_user
from app.models import User, Candidate, Employer, CV, Job, Application, UserRole


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    # recent_jobs = Job.query.filter_by(status='active').order_by(Job.created_at.desc()).limit(10).all()
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    err_msg = None
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = auth_user(username=username, password=password)

        if user:
            login_user(user)

            if user.role == UserRole.CANDIDATE:
                session['user_type'] = 'candidate'
                return redirect(url_for('candidate_dashboard'))
            elif user.role == UserRole.EMPLOYER:
                session['user_type'] = 'employer'
                return redirect(url_for('employer_dashboard'))
            elif user.role == UserRole.ADMIN:
                session['user_type'] = 'admin'
                return redirect('/admin')
        else:
            err_msg = "Sai tài khoản hoặc mật khẩu."
    return render_template('login.html', err_msg=err_msg)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Bạn đã đăng xuất', 'info')
    return redirect('/')


@app.route("/register/candidate", methods=["GET", "POST"])
def register_candidate():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại', 'danger')
        else:
            user = register_user(username=username, password=password, role=UserRole.CANDIDATE, full_name=full_name, email=email, phone=phone)
            login_user(user)
            session['user_type'] = 'candidate'
            flash('Đăng ký thành công!', 'success')
            return redirect(url_for('candidate_dashboard'))

    return render_template('register_candidate.html')


@app.route("/register/employer", methods=["GET", "POST"])
def register_employer():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        company_name = request.form.get("company_name")
        company_address = request.form.get("company_address")
        contact_person = request.form.get("contact_person")

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại', 'danger')
        else:
            user = register_user(username=username, password=password, role=UserRole.EMPLOYER,
                                 company_name=company_name, company_address=company_address, contact_person=contact_person)
            login_user(user)
            session['user_type'] = 'employer'
            flash('Đăng ký thành công!', 'success')
            return redirect(url_for('employer_dashboard'))

    return render_template('register_employer.html')


if __name__ == "__main__":
    app.run(debug=True, port=5000)