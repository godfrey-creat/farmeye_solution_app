# app/errors.py

from flask import jsonify, render_template


def init_app(app):
    """Initialize error handlers for the app"""

    @app.errorhandler(404)
    def not_found_error(error):
        # Check if the request wants JSON
        if request_wants_json():
            return jsonify({"error": "Not found", "code": 404}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Check if the request wants JSON
        if request_wants_json():
            return jsonify({"error": "Internal server error", "code": 500}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        # Check if the request wants JSON
        if request_wants_json():
            return jsonify({"error": "Forbidden", "code": 403}), 403
        return render_template("errors/403.html"), 403


def request_wants_json():
    """Check if the request prefers JSON response"""
    from flask import request

    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json" or request.path.startswith("/api/")

    # Check Accept header for preferred response type
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return (
        best == "application/json"
        and request.accept_mimetypes[best] > request.accept_mimetypes["text/html"]
    )