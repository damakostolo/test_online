from datetime import datetime
from flask_login import UserMixin
from .extensions import db, login_manager, bcrypt


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    created_tests = db.relationship("Test", backref="creator", lazy=True)
    attempts = db.relationship("TestAttempt", backref="student", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)


class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    time_limit = db.Column(db.Integer, nullable=True)  # minutes
    published = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    questions = db.relationship("Question", backref="test", lazy=True, cascade="all, delete")
    attempts = db.relationship("TestAttempt", backref="test", lazy=True)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("test.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    options = db.relationship(
        "AnswerOption", backref="question", lazy=True, cascade="all, delete-orphan"
    )


class AnswerOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)


class TestAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey("test.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship(
        "StudentAnswer", backref="attempt", lazy=True, cascade="all, delete-orphan"
    )


class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("test_attempt.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    selected_option_ids = db.Column(db.String(255), nullable=True)
    text_answer = db.Column(db.Text, nullable=True)
    is_correct = db.Column(db.Boolean, default=False)
    question = db.relationship("Question")
