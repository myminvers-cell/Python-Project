"""
UniVault: College Notes & University Exam Material Sharing Portal
Full-Stack Flask Application ready for Vercel Serverless and Local Execution.
"""

import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, send_file
from werkzeug.utils import secure_filename
from io import BytesIO
import io
import database
from pdf_generator import generate_notes_pdf
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "univault-super-secret-production-key-2026")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32MB max upload size

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "txt", "zip", "png", "jpg"}

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass

# Ensure database is ready upon startup
with app.app_context():
    try:
        database.init_db()
    except Exception as e:
        print(f"Database init warning: {e}")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def ensure_db_ready():
    """Ensure database is initialized on serverless cold starts."""
    pass


# -------------------------------------------------------------
# Frontend Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    """Renders the main portal web interface."""
    stats = database.get_stats()
    filters = database.get_filter_options()
    leaderboard = database.get_leaderboard(limit=5)
    materials_data = database.get_materials(page=1, per_page=12)
    return render_template(
        "index.html",
        stats=stats,
        filters=filters,
        leaderboard=leaderboard,
        initial_materials=materials_data.get("materials", []),
        initial_total=materials_data.get("total", 0)
    )


@app.route("/static/<path:filename>", endpoint="serve_static_asset")
def serve_static_asset(filename):
    """Explicit static file handler ensuring reliable asset delivery on Vercel."""
    return send_from_directory(app.static_folder, filename)


# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """Vercel & platform health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "UniVault Notes Portal API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "vercel" if os.environ.get("VERCEL") else "local"
    })


@app.route("/api/materials", methods=["GET"])
def list_materials():
    """
    Search and filter notes and exam materials.
    Query params: search, branch, semester, university, material_type, sort_by, page, per_page
    """
    search = request.args.get("search", "")
    branch = request.args.get("branch", "all")
    semester = request.args.get("semester", "all")
    university = request.args.get("university", "all")
    material_type = request.args.get("material_type", "all")
    sort_by = request.args.get("sort_by", "popular")
    
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(50, max(1, int(request.args.get("per_page", 12))))
    except ValueError:
        page = 1
        per_page = 12

    data = database.get_materials(
        search=search,
        branch=branch,
        semester=semester,
        university=university,
        material_type=material_type,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )
    return jsonify(data)


@app.route("/api/materials/<int:material_id>", methods=["GET"])
def get_material(material_id):
    """Fetch complete detail and reviews for a single material."""
    item = database.get_material_by_id(material_id)
    if not item:
        return jsonify({"error": "Material not found"}), 404

    # Automatically increment views counter
    database.increment_views(material_id)
    item["views_count"] += 1
    return jsonify(item)


@app.route("/api/materials", methods=["POST"])
def upload_material():
    """
    Upload and publish a new study note or exam paper.
    Supports JSON or Multipart Form data.
    Automatically detects real file size and PDF page count.
    """
    data = {}

    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict()

    # Handle file upload if present
    file_url = data.get("file_url", "").strip()
    file_type = "PDF"
    file_size_kb = 0
    page_count = 0
    file_data = None

    if "file" in request.files:
        file = request.files["file"]

        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = (
                f"{int(datetime.now(timezone.utc).timestamp())}_{filename}"
            )

            ext = filename.rsplit(".", 1)[1].upper()
            file_type = ext if ext in [
                "PDF", "DOCX", "PPTX", "ZIP", "TXT",
                "PNG", "JPG", "JPEG"
            ] else "PDF"

            # ---------------------------------------------------------
            # LOCAL STORAGE
            # ---------------------------------------------------------
            if not os.environ.get("VERCEL"):
                save_path = os.path.join(UPLOAD_FOLDER, unique_filename)

                try:
                    file.save(save_path)

                    file_url = f"/static/uploads/{unique_filename}"

                    # Real file size
                    actual_size_bytes = os.path.getsize(save_path)
                    file_size_kb = max(
                        1,
                        (actual_size_bytes + 1023) // 1024
                    )

                    # Real PDF page count
                    if file_type == "PDF" and PdfReader is not None:
                        try:
                            reader = PdfReader(save_path)
                            page_count = len(reader.pages)
                        except Exception as pdf_error:
                            print(
                                f"PDF page count warning: {pdf_error}"
                            )
                            page_count = 0

                except Exception as e:
                    print(f"Local file save error: {e}")
                    file_url = (
                        "https://raw.githubusercontent.com/"
                        "mathiasbynens/small/master/pdf.pdf"
                    )

            # ---------------------------------------------------------
            # VERCEL STORAGE
            # ---------------------------------------------------------
            else:
                # Read the ORIGINAL uploaded bytes into memory.
                file_data = file.read()

                # Real file size from uploaded bytes
                actual_size_bytes = len(file_data)

                file_size_kb = max(
                    1,
                    (actual_size_bytes + 1023) // 1024
                )

                # Real PDF page count from uploaded bytes
                if file_type == "PDF" and PdfReader is not None:
                    try:
                        reader = PdfReader(io.BytesIO(file_data))
                        page_count = len(reader.pages)
                    except Exception as pdf_error:
                        print(
                            f"PDF page count warning: {pdf_error}"
                        )
                        page_count = 0

                # IMPORTANT:
                # Keep this empty on Vercel so database.py can point
                # the material to /api/materials/<id>/file.
                file_url = ""

    # Default fallback only when there is no uploaded file
    if not file_url and file_data is None:
        file_url = (
            "https://raw.githubusercontent.com/"
            "mathiasbynens/small/master/pdf.pdf"
        )

    title = data.get("title", "").strip()
    subject_name = data.get("subject_name", "").strip()

    if not title or not subject_name:
        return jsonify({
            "error": "Title and Subject Name are required fields"
        }), 400

    # ---------------------------------------------------------
    # Allow manually supplied metadata only when real metadata
    # could not be detected.
    # ---------------------------------------------------------
    if file_size_kb <= 0:
        try:
            file_size_kb = max(
                1,
                int(data.get("file_size_kb", 1))
            )
        except (ValueError, TypeError):
            file_size_kb = 1

    if page_count <= 0:
        try:
            page_count = max(
                0,
                int(data.get("page_count", 0))
            )
        except (ValueError, TypeError):
            page_count = 0

    payload = {
        "title": title,
        "description": data.get(
            "description",
            "Student shared notes and study material."
        ),
        "subject_name": subject_name,
        "subject_code": data.get("subject_code", "GEN-101"),
        "branch": data.get(
            "branch",
            "Computer Science & Engineering"
        ),
        "semester": data.get(
            "semester",
            "Semester 1"
        ),
        "university": data.get(
            "university",
            "General University"
        ),
        "material_type": data.get(
            "material_type",
            "Lecture Notes"
        ),
        "academic_year": data.get(
            "academic_year",
            str(datetime.now().year)
        ),
        "file_url": file_url,
        "file_type": file_type,
        "file_size_kb": file_size_kb,
        "page_count": page_count,
        "uploader_name": data.get(
            "uploader_name",
            "Anonymous Scholar"
        ).strip() or "Anonymous Scholar",
        "uploader_avatar": (
            "https://images.unsplash.com/"
            "photo-1535713875002-d1d0cf377fde"
            "?w=100&auto=format&fit=crop&q=80"
        ),
        "tags": data.get("tags", ""),
        "preview_content": data.get(
            "preview_content",
            data.get("description", "Preview not available.")
        )
    }

    material_id = database.create_material(
        payload,
        file_data=file_data
    )

    return jsonify({
        "success": True,
        "message": "Material uploaded and published successfully!",
        "material_id": material_id,
        "file_size_kb": file_size_kb,
        "page_count": page_count
    }), 201




@app.route("/api/materials/<int:material_id>/file", methods=["GET"])
def download_material_file(material_id):
    """Download the original uploaded material file."""
    item = database.get_material_by_id(material_id)

    if not item:
        return jsonify({"error": "Material not found"}), 404

    file_data, stored_type = database.get_material_file_data(material_id)

    # Do NOT generate a replacement PDF.
    # The user must receive the original uploaded file.
    if not file_data:
        return jsonify({
            "error": "Original uploaded file is not available on the server."
        }), 404

    mime_types = {
        "PDF": "application/pdf",
        "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "PPTX": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "ZIP": "application/zip",
        "TXT": "text/plain",
        "PNG": "image/png",
        "JPG": "image/jpeg",
        "JPEG": "image/jpeg"
    }

    ext = (item.get("file_type") or stored_type or "PDF").upper()
    mime = mime_types.get(ext, "application/octet-stream")

    filename = secure_filename(
        item.get("title") or "univault-material"
    ) + "." + ext.lower()

    return send_file(
        BytesIO(bytes(file_data)),
        mimetype=mime,
        as_attachment=True,
        download_name=filename
    )

@app.route("/api/materials/<int:material_id>/upvote", methods=["POST"])
def upvote_material(material_id):
    """Upvote a note or exam paper."""
    new_count = database.increment_upvote(material_id)
    return jsonify({"success": True, "upvotes_count": new_count})


@app.route("/api/materials/<int:material_id>/download", methods=["POST"])
def track_download(material_id):
    """Track download and return the real file endpoint."""
    result = database.increment_download(material_id)

    return jsonify({
        "success": True,
        "downloads_count": result["downloads_count"],
        "file_url": url_for(
            "download_material_file",
            material_id=material_id
        )
    })


@app.route("/api/materials/<int:material_id>/reviews", methods=["POST"])
def submit_review(material_id):
    """Submit a rating and comment for a material."""
    data = request.get_json() or request.form.to_dict()
    author_name = data.get("author_name", "Student Scholar").strip()
    rating = int(data.get("rating", 5))
    comment = data.get("comment", "").strip()

    if not comment:
        return jsonify({"error": "Review comment cannot be empty"}), 400

    rating = max(1, min(5, rating))
    review_id = database.create_review(material_id, author_name, rating, comment)
    
    return jsonify({
        "success": True,
        "message": "Review submitted successfully!",
        "review_id": review_id
    }), 201


@app.route("/api/stats", methods=["GET"])
def get_platform_stats():
    """Get aggregated metrics and counts."""
    stats = database.get_stats()
    return jsonify(stats)


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard_data():
    """Get community leaderboard."""
    leaderboard = database.get_leaderboard(limit=10)
    return jsonify(leaderboard)


@app.route("/api/filter-options", methods=["GET"])
def get_filters():
    """Get distinct universities, branches, semesters, and types."""
    filters = database.get_filter_options()
    return jsonify(filters)

@app.route("/api/materials/<int:material_id>/file-debug", methods=["GET"])
def debug_material_file(material_id):
    file_data, stored_type = database.get_material_file_data(material_id)

    if not file_data:
        return jsonify({
            "material_id": material_id,
            "has_file": False,
            "message": "No BLOB found in the current Vercel database instance"
        }), 404

    return jsonify({
        "material_id": material_id,
        "has_file": True,
        "file_type": stored_type,
        "file_size_bytes": len(file_data),
        "file_size_kb": round(len(file_data) / 1024, 2)
    })

# -------------------------------------------------------------
# Local Dev Entry Point
# -------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==========================================================")
    print(f"🎓 UniVault Portal running at: http://127.0.0.1:{port}")
    print(f"==========================================================\n")
    app.run(host="0.0.0.0", port=port, debug=True)
