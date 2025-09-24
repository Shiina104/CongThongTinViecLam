import datetime

import flask
from flask import render_template, redirect, session, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user

from app import app, login_manager
from app.dao import auth_user, register_user
from app.models import User, Candidate, CV, Application, UserRole, Employer, Job, JobStatus


@app.context_processor
def inject_enums():
    return dict(UserRole=UserRole, JobStatus=JobStatus)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    recent_jobs = Job.query.filter_by(status='active').order_by(Job.posted_date.desc()).limit(10).all()
    return render_template("index.html", recent_jobs=recent_jobs)


# ĐĂNG KÝ/ĐĂNG NHẬP
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
        elif len(phone) != 10:
            flash('Số điện thoại phải là 10 con số', 'danger')
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


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        try:
            if current_user.role == UserRole.CANDIDATE:
                # Nếu user chưa có candidate thì tạo mới
                if not current_user.candidate:
                    candidate = Candidate(user_id=current_user.id)
                    db.session.add(candidate)
                    db.session.flush()
                    current_user.candidate = candidate

                current_user.candidate.full_name = request.form.get("full_name")
                current_user.candidate.email = request.form.get("email")
                current_user.candidate.phone = request.form.get("phone")
                current_user.candidate.address = request.form.get("address")

            elif current_user.role == UserRole.EMPLOYER:
                if not current_user.employer:
                    employer = Employer(user_id=current_user.id)
                    db.session.add(employer)
                    db.session.flush()
                    current_user.employer = employer

                current_user.employer.company_name = request.form.get("company_name")
                current_user.employer.company_address = request.form.get("company_address")
                current_user.employer.contact_person = request.form.get("contact_person")

            db.session.commit()
            flash("Cập nhật thông tin thành công!", "success")
            return redirect(url_for("profile"))

        except Exception as ex:
            db.session.rollback()
            flash("Có lỗi xảy ra khi cập nhật: " + str(ex), "danger")

    return render_template("profile.html")


# ỨNG VIÊN DASHBOARD
@app.route("/candidate/dashboard")
@login_required
def candidate_dashboard():
    if current_user.role != UserRole.CANDIDATE:
        flash('Bạn không có quyền truy cập trang này', 'danger')
        return redirect(url_for('index'))

    applications = Application.query.filter_by(candidate_id=current_user.candidate.id).order_by(Application.applied_date.desc()).all()
    cvs = CV.query.filter_by(candidate_id=current_user.candidate.id).all()

    return render_template('candidate_dashboard.html', applications=applications, cvs=cvs)


# ỨNG VIÊN TẠO CV
@app.route("/candidate/cv", methods=["GET", "POST"])
@app.route("/candidate/cv/<int:cv_id>", methods=["GET", "POST"])
@login_required
def manage_cv(cv_id=None):
    if current_user.role != UserRole.CANDIDATE:
        flash('Bạn không có quyền truy cập trang này', 'danger')
        return redirect(url_for('index'))

    cv = None
    if cv_id:
        cv = CV.query.filter_by(id=cv_id, candidate_id=current_user.candidate.id).first_or_404()

    if request.method == "POST":
        try:
            # Xử lý dữ liệu form
            title = request.form.get("title")
            position = request.form.get("position")
            full_name = request.form.get("full_name")
            email = request.form.get("email")
            phone = request.form.get("phone")
            objective = request.form.get("objective")
            skills = request.form.get("skills")

            # Xử lý kinh nghiệm làm việc (dạng mảng)
            experiences = []
            companies = request.form.getlist("company[]")
            positions = request.form.getlist("position[]")
            periods = request.form.getlist("period[]")
            descriptions = request.form.getlist("description[]")

            for i in range(len(companies)):
                if companies[i].strip():
                    exp_data = f"{companies[i]}|{positions[i]}|{periods[i]}|{descriptions[i]}"
                    experiences.append(exp_data)

            experience = "|||".join(experiences) if experiences else ""

            # Xử lý học vấn
            educations = []
            schools = request.form.getlist("school[]")
            degrees = request.form.getlist("degree[]")
            edu_periods = request.form.getlist("edu_period[]")
            edu_descriptions = request.form.getlist("edu_description[]")

            for i in range(len(schools)):
                if schools[i].strip():
                    edu_data = f"{schools[i]}|{degrees[i]}|{edu_periods[i]}|{edu_descriptions[i]}"
                    educations.append(edu_data)

            education = "|||".join(educations) if educations else ""

            if cv:
                # Cập nhật CV hiện có
                cv.title = title
                cv.position = position
                cv.full_name = full_name
                cv.email = email
                cv.phone = phone
                cv.objective = objective
                cv.skills = skills
                cv.experience = experience
                cv.education = education
                cv.updated_at = datetime.utcnow()

                flash('Cập nhật CV thành công!', 'success')
            else:
                # Tạo CV mới
                cv = CV(
                    candidate_id=current_user.candidate.id,
                    title=title,
                    position=position,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    objective=objective,
                    skills=skills,
                    experience=experience,
                    education=education
                )
                db.session.add(cv)
                flash('Tạo CV thành công!', 'success')

            db.session.commit()
            return redirect(url_for('candidate_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra khi lưu CV', 'danger')
            print(f"Error saving CV: {e}")

    return render_template('create_cv.html', cv=cv)


@app.route("/api/candidate/cvs", methods=["GET"])
@login_required
def api_cv():
    cv = None
    if current_user.role != UserRole.CANDIDATE:
        flash('Bạn không có quyền truy cập trang này', 'danger')

    try:
        cv = CV.query.filter_by(candidate_id=current_user.candidate.id).all()

        cvs = []
        for c in cv:
            cvs.append({
                "id": c.id,
                "title": c.title,
            })
        return jsonify(cvs)
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi lấy CV', 'danger')
        print(f"Error saving CV: {e}")

# Route xóa CV
@app.route("/candidate/cv/<int:cv_id>/delete", methods=["POST"])
@login_required
def delete_cv(cv_id):
    if current_user.role != UserRole.CANDIDATE:
        return jsonify({"error": "Unauthorized"}), 403

    cv = CV.query.filter_by(id=cv_id, candidate_id=current_user.candidate.id).first_or_404()

    try:
        db.session.delete(cv)
        db.session.commit()
        flash('Xóa CV thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi xóa CV', 'danger')

    return redirect(url_for('candidate_dashboard'))


# ROUTE XEM
@app.route("/api/cv/<int:cv_id>")
@login_required
def get_cv(cv_id):
    if current_user.role != UserRole.EMPLOYER:
        return jsonify({"error": "Unauthorized"}), 403

    cv = CV.query.get_or_404(cv_id)
    return jsonify({
        "id": cv.id,
        "title": cv.title,
        "full_name": cv.full_name,
        "email": cv.email,
        "phone": cv.phone,
        "objective": cv.objective,
        "skills": cv.skills,
        "experience": cv.experience,
        "education": cv.education,
    })


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
    if not job or job.status != JobStatus.active:
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


# NHÀ TUYỂN DỤNG DASHBOARD
@app.route('/employer/dashboard')
@login_required
def employer_dashboard():
    if current_user.role != UserRole.EMPLOYER:
        flash('Bạn không có quyền truy cập trang này', 'danger')
        return redirect(url_for('index'))

    jobs = Job.query.filter_by(employer_id=current_user.employer.id).all()

    total_applications = Application.query \
        .join(Job) \
        .filter(Job.employer_id == current_user.employer.id) \
        .count()

    return render_template('employer_dashboard.html',
                           jobs=jobs,
                           total_applications=total_applications)


# ROUTE ĐĂNG JOB
@app.route('/employer/job', methods=['GET', 'POST'])
@login_required
def create_job():
    if current_user.role != UserRole.EMPLOYER:
        flash('Bạn không có quyền truy cập trang này', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        requirements = request.form.get('requirements')
        location = request.form.get('location')
        salary = request.form.get('salary')
        work_type = request.form.get('work_type')
        experience_level = request.form.get('experience_level')
        benefits = request.form.get('benefits')

        job = Job(
            employer_id=current_user.employer.id,
            title=title,
            description=description,
            requirements=requirements,
            location=location,
            salary=salary,
            work_type=work_type,
            experience_level=experience_level,
            benefits=benefits,
            status='pending'
        )

        db.session.add(job)
        db.session.commit()

        flash('Đăng tin tuyển dụng thành công!', 'success')
        return redirect(url_for('employer_dashboard'))

    return render_template('create_job.html')


# ROUTE EDIT JOB
@app.route('/employer/job/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    if current_user.role != UserRole.EMPLOYER:
        flash('Bạn không có quyền truy cập trang này', 'danger')
        return redirect(url_for('index'))

    # Kiểm tra job thuộc về employer hiện tại
    job = Job.query.filter_by(id=job_id, employer_id=current_user.employer.id).first_or_404()

    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            title = request.form.get('title')
            description = request.form.get('description')
            requirements = request.form.get('requirements')
            location = request.form.get('location')
            salary = request.form.get('salary')
            work_type = request.form.get('work_type')
            experience_level = request.form.get('experience_level')
            benefits=request.form.get('benefits')
            status = request.form.get('status')

            # Validate dữ liệu
            if not title or not description:
                flash('Tiêu đề và mô tả không được để trống', 'danger')
                return render_template('edit_job.html', job=job)

            # Cập nhật thông tin job
            job.title = title
            job.description = description
            job.requirements = requirements
            job.location = location
            job.work_type = work_type
            job.experience_level = experience_level
            job.benefits = benefits
            job.status = status

            # Xử lý salary
            if salary and salary.strip():
                try:
                    # Remove dots and commas, convert to float
                    salary_clean = salary.replace('.', '').replace(',', '')
                    if salary_clean.isdigit():
                        job.salary = float(salary_clean)
                    else:
                        job.salary = None
                except ValueError:
                    job.salary = None
            else:
                job.salary = None

            job.updated_at = datetime.datetime.utcnow()

            db.session.commit()

            flash('Cập nhật tin tuyển dụng thành công!', 'success')
            return redirect(url_for('employer_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra khi cập nhật tin tuyển dụng', 'danger')
            print(f"Error updating job: {e}")

    return render_template('edit_job.html', job=job)


# ROUTE ĐỔI STATUS JOB
@app.route('/employer/job/<int:job_id>/toggle_status', methods=['POST'])
@login_required
def toggle_job_status(job_id):
    if current_user.role != UserRole.EMPLOYER:
        return jsonify({"error": "Unauthorized"}), 403

    job = Job.query.filter_by(id=job_id, employer_id=current_user.employer.id).first_or_404()

    try:
        # Toggle status between active and inactive
        if job.status == 'active':
            job.status = 'inactive'
            message = 'Đã tắt tin tuyển dụng'
        else:
            job.status = 'active'
            message = 'Đã kích hoạt tin tuyển dụng'

        job.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "success": True,
            "message": message,
            "new_status": job.status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Có lỗi xảy ra"}), 500


# ROUTE XÓA JOB
@app.route("/employer/job/<int:job_id>/delete", methods=["POST"])
@login_required
def delete_job(job_id):
    if current_user.role != UserRole.EMPLOYER:
        flash('Bạn không có quyền thực hiện hành động này', 'danger')
        return redirect(url_for('index'))

    job = Job.query.filter_by(id=job_id, employer_id=current_user.employer.id).first_or_404()

    try:
        # Xóa các application liên quan trước
        Application.query.filter_by(job_id=job_id).delete()
        db.session.delete(job)
        db.session.commit()
        flash('Xóa tin tuyển dụng thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi xóa tin tuyển dụng', 'danger')

    return redirect(url_for('employer_dashboard'))


# ROUTE XEM APPLY
@app.route('/employer/job/<int:job_id>/candidate')
@login_required
def job_candidates(job_id):
    if current_user.role != UserRole.EMPLOYER:
        flash('Bạn không có quyền truy cập trang này', 'danger')
        return redirect(url_for('index'))

    job = Job.query.filter_by(id=job_id, employer_id=current_user.employer.id).first_or_404()

    applications = Application.query.filter_by(job_id=job_id) \
        .order_by(Application.applied_date.desc()) \
        .all()

    return render_template('job_candidates.html',
                           job=job,
                           applications=applications)


# NHÀ TUYỂN DỤNG DUYỆT HỒ SƠ
@app.route("/api/application/<int:app_id>/review", methods=["PUT"])
@login_required
def review_application(app_id):
    if current_user.role != UserRole.EMPLOYER:
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


# API ĐĂNG TIN TUYỂN DỤNG
@app.route("/api/jobs", methods=["POST"])
@login_required
def create_jobs():
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




@app.route('/job')
def jobs():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    keyword = request.args.get('keyword', '')
    location = request.args.get('location', '')

    query = Job.query.filter_by(status='active')

    if keyword:
        query = query.filter(Job.title.ilike(f'%{keyword}%'))
    if location:
        query = query.filter(Job.location.ilike(f'%{location}%'))

    jobs = query.order_by(Job.posted_date.desc()).paginate(page=page, per_page=per_page)

    return render_template('job.html', jobs=jobs)


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    try:
        job = Job.query.get_or_404(job_id)

        if job.status != JobStatus.active:
            flash('Công việc này không còn tuyển dụng', 'warning')
            return redirect(url_for('jobs'))

        applied = False

        if current_user.is_authenticated and current_user.role == UserRole.CANDIDATE:
            applied = Application.query.filter_by(
                job_id=job_id,
                candidate_id=current_user.candidate.id
            ).first() is not None

        return render_template('job_detail.html', job=job, applied=applied)

    except Exception as e:
        flash('Có lỗi xảy ra khi tải thông tin công việc', 'error')
        return redirect(url_for('jobs'))


if __name__ == "__main__":
    from app import admin
    app.run(debug=True, port=5000)
