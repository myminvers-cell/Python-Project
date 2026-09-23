from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

# Add required imports
s = s.replace(
    "from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory",
    "from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, send_file"
)

s = s.replace(
    "from werkzeug.utils import secure_filename",
    "from werkzeug.utils import secure_filename\nfrom io import BytesIO"
)

# Add file_data variable
s = s.replace(
    "    file_size_kb = 2048\n\n    if \"file\" in request.files:",
    "    file_size_kb = 2048\n    file_data = None\n\n    if \"file\" in request.files:"
)

# Replace the Vercel fallback
s = s.replace(
    '''            else:
                # In serverless environment, fallback to standard link or demo URL
                file_url = "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf"''',
    '''            else:
                file_data = file.read()
                file_url = ""'''
)

# Use stored file data when creating material
s = s.replace(
    "    material_id = database.create_material(payload)",
    "    material_id = database.create_material(payload, file_data=file_data)"
)

# Insert download endpoint before the upvote endpoint
marker = '@app.route("/api/materials/<int:material_id>/upvote", methods=["POST"])'

route = '''@app.route("/api/materials/<int:material_id>/file", methods=["GET"])
def download_material_file(material_id):
    item = database.get_material_by_id(material_id)

    if not item:
        return jsonify({"error": "Material not found"}), 404

    file_data, stored_type = database.get_material_file_data(material_id)

    if file_data:
        mime_types = {
            "PDF": "application/pdf",
            "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "PPTX": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "ZIP": "application/zip"
        }

        ext = (item.get("file_type") or stored_type or "PDF").upper()
        mime = mime_types.get(ext, "application/octet-stream")
        filename = secure_filename(
            item.get("title") or "univault-material"
        ) + "." + ext.lower()

        return send_file(
            BytesIO(file_data),
            mimetype=mime,
            as_attachment=True,
            download_name=filename
        )

    pdf_bytes = generate_notes_pdf(item)
    filename = secure_filename(
        item.get("title") or "univault-material"
    ) + ".pdf"

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


'''

if marker not in s:
    raise SystemExit("ERROR: upvote route not found")

if 'def download_material_file(material_id):' not in s:
    s = s.replace(marker, route + marker)

p.write_text(s, encoding="utf-8")

print("app.py patched successfully")