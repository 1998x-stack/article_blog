from flask import Blueprint, render_template
from auth import require_admin

bp = Blueprint("admin", __name__)


@bp.route("/admin")
@require_admin
def dashboard():
    return render_template("admin/dashboard.html")