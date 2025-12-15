from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort,
)
from flask_login import login_required, current_user
from ..forms import TestForm, QuestionForm
from ..models import Test, Question, AnswerOption, TestAttempt, StudentAnswer
from ..extensions import db


def teacher_required():
    if not current_user.is_authenticated or current_user.role != "teacher":
        abort(403)


def student_required():
    if not current_user.is_authenticated or current_user.role != "student":
        abort(403)


tests_bp = Blueprint("tests", __name__, url_prefix="/tests")


@tests_bp.route("/")
@login_required
def list_tests():
    if current_user.role == "teacher":
        tests = Test.query.filter_by(creator_id=current_user.id).all()
    else:
        tests = Test.query.filter_by(published=True).all()
    return render_template("test_list.html", tests=tests)


@tests_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_test():
    teacher_required()
    form = TestForm()
    if form.validate_on_submit():
        test = Test(
            title=form.title.data,
            description=form.description.data,
            time_limit=form.time_limit.data or None,
            published=form.published.data,
            creator_id=current_user.id,
        )
        db.session.add(test)
        db.session.commit()
        flash("Test created. Add questions next.", "success")
        return redirect(url_for("tests.edit_test", test_id=test.id))
    return render_template("test_form.html", form=form, test=None)


@tests_bp.route("/<int:test_id>/edit", methods=["GET", "POST"])
@login_required
def edit_test(test_id):
    teacher_required()
    test = Test.query.get_or_404(test_id)
    if test.creator_id != current_user.id:
        abort(403)
    form = TestForm(obj=test)
    if form.validate_on_submit():
        form.populate_obj(test)
        db.session.commit()
        flash("Test updated.", "success")
        return redirect(url_for("tests.edit_test", test_id=test.id))
    return render_template("test_form.html", form=form, test=test)


@tests_bp.route("/<int:test_id>/delete", methods=["POST"])
@login_required
def delete_test(test_id):
    teacher_required()
    test = Test.query.get_or_404(test_id)
    if test.creator_id != current_user.id:
        abort(403)
    db.session.delete(test)
    db.session.commit()
    flash("Test deleted.", "info")
    return redirect(url_for("tests.list_tests"))


@tests_bp.route("/<int:test_id>/questions/new", methods=["GET", "POST"])
@login_required
def add_question(test_id):
    teacher_required()
    test = Test.query.get_or_404(test_id)
    if test.creator_id != current_user.id:
        abort(403)
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            text=form.text.data,
            question_type=form.question_type.data,
            test_id=test.id,
        )
        db.session.add(question)
        db.session.flush()

        for option_form in form.options:
            if option_form.text.data or form.question_type.data != "short":
                option = AnswerOption(
                    text=option_form.text.data or "",
                    is_correct=option_form.is_correct.data,
                    question_id=question.id,
                )
                db.session.add(option)
        db.session.commit()
        flash("Question added.", "success")
        return redirect(url_for("tests.edit_test", test_id=test.id))
    return render_template("question_form.html", form=form, test=test)


@tests_bp.route("/<int:test_id>/questions/<int:question_id>/delete", methods=["POST"])
@login_required
def delete_question(test_id, question_id):
    teacher_required()
    question = Question.query.get_or_404(question_id)
    if question.test.creator_id != current_user.id:
        abort(403)
    db.session.delete(question)
    db.session.commit()
    flash("Question removed.", "info")
    return redirect(url_for("tests.edit_test", test_id=test_id))


def build_answer_form(test):
    from flask_wtf import FlaskForm
    from wtforms import RadioField, SelectMultipleField, widgets, StringField, SubmitField

    class AnswerForm(FlaskForm):
        submit = SubmitField("Submit")

    for question in test.questions:
        field_name = f"question_{question.id}"
        if question.question_type == "single":
            choices = [(str(opt.id), opt.text) for opt in question.options]
            setattr(AnswerForm, field_name, RadioField(question.text, choices=choices, coerce=str))
        elif question.question_type == "multiple":
            choices = [(str(opt.id), opt.text) for opt in question.options]
            setattr(
                AnswerForm,
                field_name,
                SelectMultipleField(
                    question.text,
                    choices=choices,
                    option_widget=widgets.CheckboxInput(),
                    widget=widgets.ListWidget(prefix_label=False),
                    coerce=str,
                ),
            )
        elif question.question_type == "truefalse":
            choices = [(str(opt.id), opt.text) for opt in question.options]
            setattr(AnswerForm, field_name, RadioField(question.text, choices=choices, coerce=str))
        else:
            setattr(AnswerForm, field_name, StringField(question.text))
    return AnswerForm()


@tests_bp.route("/<int:test_id>/take", methods=["GET", "POST"])
@login_required
def take_test(test_id):
    student_required()
    test = Test.query.get_or_404(test_id)
    if not test.published:
        abort(403)
    form = build_answer_form(test)
    if form.validate_on_submit():
        total_questions = len(test.questions)
        correct_answers = 0
        attempt = TestAttempt(user_id=current_user.id, test_id=test.id, score=0)
        db.session.add(attempt)
        db.session.flush()

        for question in test.questions:
            field_name = f"question_{question.id}"
            field = getattr(form, field_name)
            selected_ids = []
            text_answer = None
            is_correct = False
            if question.question_type in {"single", "truefalse"}:
                selected_ids = [field.data] if field.data else []
                correct_ids = [str(opt.id) for opt in question.options if opt.is_correct]
                is_correct = selected_ids == correct_ids
            elif question.question_type == "multiple":
                selected_ids = field.data or []
                correct_ids = sorted([str(opt.id) for opt in question.options if opt.is_correct])
                is_correct = sorted(selected_ids) == correct_ids
            else:
                text_answer = field.data or ""
                correct_text = (question.options[0].text or "").strip().lower() if question.options else ""
                is_correct = text_answer.strip().lower() == correct_text

            if is_correct:
                correct_answers += 1

            db.session.add(
                StudentAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option_ids=",".join(selected_ids) if selected_ids else None,
                    text_answer=text_answer,
                    is_correct=is_correct,
                )
            )

        attempt.score = (correct_answers / total_questions * 100) if total_questions else 0
        db.session.commit()
        flash("Test submitted.", "success")
        return redirect(url_for("results.view_attempt", attempt_id=attempt.id))
    return render_template("take_test.html", test=test, form=form)
