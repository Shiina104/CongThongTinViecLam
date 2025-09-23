from werkzeug.security import generate_password_hash, check_password_hash
from app import db, app
from sqlalchemy import Column, Integer, String
from flask_login import UserMixin
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    CANDIDATE = 'candidate'
    EMPLOYER = 'employer'
    ADMIN = 'admin'


class JobStatus(Enum):
    active = 'active'
    inactive = 'inactive'
    pending = 'pending'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    #Relationship
    candidate = db.relationship('Candidate', backref='user', uselist=False, cascade="all, delete-orphan")
    employer = db.relationship('Employer', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(password, self.password)

    def get_id(self):
        return str(self.id)


class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(10), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)

    applications = db.relationship('Application', backref='candidate', lazy=True)


class Employer(db.Model):
    __tablename__ = 'employers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    company_address = db.Column(db.Text, nullable=True)
    contact_person = db.Column(db.String(255), nullable=True)

    jobs = db.relationship('Job', backref='employer', lazy=True)


class CV(db.Model):
    __tablename__ = 'cvs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    title = Column(String(100), nullable=False)
    position = db.Column(db.String(255))

    full_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))

    objective = db.Column(db.Text)
    skills = Column(String(255), nullable=True)
    experience = db.Column(db.Text)  # Format: company|position|period|description|||...
    education = db.Column(db.Text)  # Format: school|degree|period|description|||...

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = db.relationship('Candidate', backref='cvs', lazy=True)
    applications = db.relationship('Application', backref='cv', lazy=True)


class Job(db.Model):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employers.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    location = db.Column(db.String(255))
    salary = db.Column(db.Numeric(10, 2))
    posted_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum(JobStatus), default='pending')

    applications = db.relationship('Application', backref='job', lazy=True)


class Application(db.Model):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    cv_id = db.Column(db.Integer, db.ForeignKey('cvs.id'), nullable=False)
    applied_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum('pending', 'reviewed', 'accepted', 'rejected'), default='pending')

    __table_args__ = (
        db.UniqueConstraint('job_id', 'candidate_id', name='unique_application'),
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        import hashlib

        u = User(username='admin', password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                 role=UserRole.ADMIN)
        db.session.add(u)
        db.session.commit()