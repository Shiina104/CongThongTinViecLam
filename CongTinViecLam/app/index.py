from flask import render_template
from app import app, db, login_manager
from app.models import User, Candidate, Employer, CV, Job, Application

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    # recent_jobs = Job.query.filter_by(status='active').order_by(Job.created_at.desc()).limit(10).all()
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)