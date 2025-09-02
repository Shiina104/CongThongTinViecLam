import json
from app import db, app
from app.models import User, Candidate, Employer, UserRole


def auth_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password) and user.is_active:
        return user
    return None

def register_user(username, password, role, **kwargs):
    user = User(username=username, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    if role == UserRole.CANDIDATE:
        candidate = Candidate(
            user_id=user.id,
            full_name=kwargs.get('full_name', ''),
            email=kwargs.get('email', ''),
            phone=kwargs.get('phone', ''),
            address=kwargs.get('address', '')
        )
        db.session.add(candidate)
    elif role == UserRole.EMPLOYER:
        employer = Employer(
            user_id=user.id,
            company_name=kwargs.get('company_name', ''),
            company_address=kwargs.get('company_address', ''),
            contact_person=kwargs.get('contact_person', '')
        )
        db.session.add(employer)

    db.session.commit()
    return user


if __name__ == "__main__":
    print("test")
    print(auth_user("user", "123"))
