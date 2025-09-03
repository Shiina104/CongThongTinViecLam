from flask import render_template, redirect, session, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user

from app import app, login_manager
from app.dao import auth_user, register_user
from app.models import User, Candidate, CV, Application, UserRole


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
            user = register_user(username=username, password=password, role=UserRole.CANDIDATE, full_name=full_name,
                                 email=email, phone=phone)
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
                                 company_name=company_name, company_address=company_address,
                                 contact_person=contact_person)
            login_user(user)
            session['user_type'] = 'employer'
            flash('Đăng ký thành công!', 'success')
            return redirect(url_for('employer_dashboard'))

    return render_template('register_employer.html')


# ỨNG VIÊN NỘP HỒ SƠ
@app.route("/api/apply", methods=["POST"])
@login_required
def apply_job():
    if session.get("user_type") != "candidate":
        return jsonify({"error": "Chỉ ứng viên mới được nộp hồ sơ"}), 403

    job_id = request.json.get("job_id")
    cv_id = request.json.get("cv_id")

    if not job_id or not cv_id:
        return jsonify({"error": "Thiếu job_id hoặc cv_id"}), 400

    candidate = Candidate.query.filter_by(user_id=current_user.id).first()
    if not candidate:
        return jsonify({"error": "Ứng viên không tồn tại"}), 404

    # Kiểm tra Job tồn tại
    job = Job.query.get(job_id)
    if not job or job.status != "active":
        return jsonify({"error": "Công việc không khả dụng"}), 404

    # Kiểm tra CV có thuộc về ứng viên không
    cv = CV.query.get(cv_id)
    if not cv:
        return jsonify({"error": "CV không tồn tại"}), 404

    # Tạo Application
    application = Application(job_id=job_id, candidate_id=candidate.id, cv_id=cv_id)
    try:
        db.session.add(application)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Bạn đã ứng tuyển công việc này rồi"}), 400

    return jsonify({"message": "Ứng tuyển thành công!", "application_id": application.id}), 201


# NHÀ TUYỂN DỤNG DUYỆT HỒ SƠ
@app.route("/api/application/<int:app_id>/review", methods=["PUT"])
@login_required
def review_application(app_id):
    if session.get("user_type") != "employer":
        return jsonify({"error": "Chỉ nhà tuyển dụng mới được duyệt hồ sơ"}), 403

    new_status = request.json.get("status")
    if new_status not in ["reviewed", "accepted", "rejected"]:
        return jsonify({"error": "Trạng thái không hợp lệ"}), 400

    application = Application.query.get(app_id)
    if not application:
        return jsonify({"error": "Hồ sơ không tồn tại"}), 404

    # Kiểm tra job này có thuộc về employer hiện tại không
    job = Job.query.get(application.job_id)
    if job.employer.user_id != current_user.id:
        return jsonify({"error": "Bạn không có quyền duyệt hồ sơ này"}), 403

    # Cập nhật trạng thái
    application.status = new_status
    db.session.commit()

    return jsonify({"message": f"Hồ sơ đã cập nhật sang trạng thái {new_status}"}), 200


from flask import jsonify, request
from flask_login import login_required
from app.models import Job, Employer
from app import db


# EMPLOYER ĐĂNG TIN TUYỂN DỤNG
@app.route("/api/jobs", methods=["POST"])
@login_required
def create_job():
    if session.get("user_type") != "employer":
        return jsonify({"error": "Chỉ nhà tuyển dụng mới được đăng tin"}), 403

    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    requirements = data.get("requirements")
    location = data.get("location")
    salary = data.get("salary")

    if not title or not description:
        return jsonify({"error": "Thiếu title hoặc description"}), 400

    # Tìm employer từ current_user
    employer = Employer.query.filter_by(user_id=current_user.id).first()
    if not employer:
        return jsonify({"error": "Không tìm thấy employer"}), 404

    job = Job(
        employer_id=employer.id,
        title=title,
        description=description,
        requirements=requirements,
        location=location,
        salary=salary,
        status="active"  # hoặc "pending" nếu bạn muốn duyệt thủ công
    )

    db.session.add(job)
    db.session.commit()

    return jsonify({
        "message": "Đăng tin thành công!",
        "job_id": job.id,
        "title": job.title,
        "status": job.status
    }), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
