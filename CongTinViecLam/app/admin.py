from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from wtforms import SelectField

from app.models import User, Candidate, Employer, UserRole, Job, JobStatus, Application
from flask_admin import Admin, BaseView, expose
from app import db, app
from flask import render_template, redirect, url_for, request, jsonify

admin = Admin(app=app, name='Job_portal Admin', template_mode='bootstrap4')


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.__eq__(UserRole.ADMIN)


class UserView(AdminView):
    column_list = ('id','username', 'password', 'role', 'created_at', 'is_active')
    form_overrides = {
        'role': SelectField
    }
    form_args = {
        'role': {
            'choices': [(v.value, v.name) for v in UserRole]
        }
    }


class CandidateView(AdminView):
    column_list = ('id','user_id', 'full_name', 'phone', 'email')


class EmployerView(AdminView):
    column_list = ('id','user_id', 'company_name', 'company_address', 'contact_person')


class JobView(AdminView):
    column_list = ('id','employer_id', 'title', 'description', 'posted_date', 'status')
    form_overrides = {
        'status': SelectField
    }
    form_args = {
        'status': {
            'choices': [(v.value, v.name) for v in JobStatus]
        }
    }


class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


class LogoutView(AuthenticatedView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')


admin.add_view(UserView(User, db.session))
admin.add_view(CandidateView(Candidate, db.session))
admin.add_view(EmployerView(Employer, db.session))
admin.add_view(JobView(Job, db.session))
admin.add_view(LogoutView(name='Đăng xuất'))