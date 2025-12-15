from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from ..models import TestAttempt, Test

results_bp = Blueprint("results", __name__, url_prefix="/results")


@results_bp.route("/")
@login_required
def my_results():
    if current_user.role == "teacher":
        attempts = TestAttempt.query.join(Test).filter(Test.creator_id == current_user.id).all()
    else:
        attempts = TestAttempt.query.filter_by(user_id=current_user.id).all()
    return render_template("results.html", attempts=attempts)


@results_bp.route("/<int:attempt_id>")
@login_required
def view_attempt(attempt_id):
    attempt = TestAttempt.query.get_or_404(attempt_id)
    if current_user.role == "teacher":
        if attempt.test.creator_id != current_user.id:
            abort(403)
    elif attempt.user_id != current_user.id:
        abort(403)
    return render_template("attempt_detail.html", attempt=attempt)
