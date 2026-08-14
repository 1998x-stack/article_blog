import json
from flask import Blueprint, request, jsonify, session
import models
from slug import slugify

bp = Blueprint("api", __name__)


@bp.post("/admin/import_json")
def import_json():
    if not session.get("admin_id"):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        payload = json.loads(request.get_data(as_text=True) or "[]")
    except (json.JSONDecodeError, ValueError):
        return jsonify({"error": "Invalid JSON"}), 400
    if not isinstance(payload, list):
        return jsonify({"error": "JSON must be a list"}), 400
    added = 0
    for i, item in enumerate(payload):
        title = (item.get("title") or "").strip()
        content = (item.get("content") or "").strip()
        raw_tags = item.get("tags", "")
        tags = raw_tags if isinstance(raw_tags, list) else [t for t in raw_tags.split(",") if t]
        if not title or not content:
            return jsonify({"error": f"Missing fields in article {i + 1}"}), 400
        models.create_article(title, slugify(title), content,
                              (item.get("excerpt") or "")[:160], tags)
        added += 1
    return jsonify({"success": f"Imported {added} articles", "added": added}), 201