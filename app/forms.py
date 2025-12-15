from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from wtforms import FieldList, FormField
from .models import User
from .extensions import db


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email")
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    role = SelectField("Role", choices=[("student", "Student"), ("teacher", "Teacher")])
    submit = SubmitField("Register")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username already exists.")

    def validate_email(self, email):
        if email.data and User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class TestForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description")
    time_limit = IntegerField("Time limit (minutes)")
    published = BooleanField("Published")
    submit = SubmitField("Save")


class OptionForm(FlaskForm):
    text = StringField("Option text", validators=[Length(max=255)])
    is_correct = BooleanField("Correct")


class QuestionForm(FlaskForm):
    text = TextAreaField("Question", validators=[DataRequired()])
    question_type = SelectField(
        "Type",
        choices=[
            ("single", "Single choice"),
            ("multiple", "Multiple choice"),
            ("truefalse", "True / False"),
            ("short", "Short text"),
        ],
        validators=[DataRequired()],
    )
    options = FieldList(FormField(OptionForm), min_entries=4, max_entries=6)
    submit = SubmitField("Add question")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        if self.question_type.data in {"single", "multiple", "truefalse"}:
            any_text = any(opt.text.data for opt in self.options)
            any_correct = any(opt.is_correct.data for opt in self.options)
            if not any_text:
                self.text.errors.append("Provide at least one option.")
                return False
            if not any_correct:
                self.text.errors.append("Mark at least one correct option.")
                return False
        else:
            # short answer expects one correct text in first option
            if not self.options[0].text.data:
                self.text.errors.append("Provide expected answer text.")
                return False
        return True


class PublishForm(FlaskForm):
    published = BooleanField("Published")
    submit = SubmitField("Update")
