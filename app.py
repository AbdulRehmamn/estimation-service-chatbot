"""
Construction Cost Estimating Chatbot Web Server
Flask application serving chat interface, plan upload handlers, and lead management APIs.
"""

import os
import json
import time
import threading
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

from chatbot import chatbot
from conversation import session_manager
from estimator_knowledge import estimator_kb
from lead_manager import lead_manager
from email_notifier import email_notifier
from intents import intent_detector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# On Vercel, file system is read-only except /tmp
IS_VERCEL = bool(os.environ.get("VERCEL"))
UPLOAD_FOLDER = "/tmp/uploads" if IS_VERCEL else os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "dwg", "dxf", "cad", "xlsx", "xls", "csv", "zip", "png", "jpg", "jpeg", "tif", "tiff"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB limit for large blueprint packages
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def safe_clean_filename(filename: str) -> str:
    """Sanitizes filename while preserving extension and handling unicode / edge cases."""
    if not filename:
        return f"blueprint_{int(time.time())}.pdf"

    base_name = os.path.basename(filename).strip()
    ext = ""
    if "." in base_name:
        ext = "." + base_name.rsplit(".", 1)[1].lower()
        stem = base_name.rsplit(".", 1)[0]
    else:
        stem = base_name

    sec_name = secure_filename(base_name)
    if sec_name and "." in sec_name:
        return sec_name

    clean_stem = "".join(c for c in stem if c.isalnum() or c in ("-", "_", " ")).strip()
    clean_stem = clean_stem.replace(" ", "_")
    if not clean_stem:
        clean_stem = f"blueprint_{int(time.time())}"

    return f"{clean_stem}{ext if ext else '.pdf'}"


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Serves the main chat application."""
    company_info = estimator_kb.company
    return render_template("index.html", company=company_info)


@app.route("/api/config", methods=["GET"])
def get_config():
    """Returns dynamic company knowledge base and services configuration."""
    return jsonify({
        "company": estimator_kb.company,
        "services": estimator_kb.get_service_list(),
        "trades": estimator_kb.get_trades_by_category()
    })


@app.route("/api/download/<path:filename>", methods=["GET"])
def download_file_endpoint(filename):
    """Allows contractors and estimators to directly download drawing files to their PC."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    """Handles chat messages from the user."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id")
    client_state = data.get("state")

    if not message:
        return jsonify({"error": "Empty message"}), 400

    state = session_manager.get_session(session_id, client_state=client_state)
    result = chatbot.process_message(message, state)
    return jsonify(result)


@app.route("/api/upload", methods=["POST"])
def upload_file_endpoint():
    """Receives plan / drawing sets uploaded by client with multi-file and 500MB support."""
    session_id = request.form.get("session_id") or request.headers.get("X-Session-ID")
    client_state_raw = request.form.get("state")
    client_state = None
    if client_state_raw:
        try:
            client_state = json.loads(client_state_raw)
        except Exception:
            pass

    if request.is_json:
        data = request.get_json() or {}
        session_id = data.get("session_id", session_id)
        client_state = data.get("state", client_state)

    state = session_manager.get_session(session_id, client_state=client_state)

    files = request.files.getlist("files") or request.files.getlist("file")
    if not files and request.files:
        for k in request.files:
            files.extend(request.files.getlist(k))

    metadata_list = []
    # Check if files metadata is passed (for large files up to 500 MB on serverless platforms)
    if request.form.get("files_metadata"):
        try:
            metadata_list = json.loads(request.form.get("files_metadata"))
        except Exception:
            pass
    elif request.is_json and request.get_json().get("files_metadata"):
        metadata_list = request.get_json().get("files_metadata", [])

    saved_files = []
    file_links_md = []

    # 1. Process standard multipart files
    for file in files:
        if file and file.filename:
            original_name = safe_clean_filename(file.filename)
            if allowed_file(original_name):
                timestamped_name = f"{int(time.time())}_{original_name}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], timestamped_name)
                try:
                    file.save(save_path)
                    file_size = os.path.getsize(save_path)
                except Exception as e:
                    print(f"[Upload] File save notice: {e}")
                    file_size = 0
                size_kb = round(file_size / 1024, 1)
                size_str = f"{round(size_kb / 1024, 2)} MB" if size_kb > 1024 else f"{size_kb} KB"
                download_url = f"/api/download/{timestamped_name}"

                entities_from_name = intent_detector.extract_entities_from_filename(original_name)
                state.update_from_entities(entities_from_name)
                state.add_uploaded_file(original_name, save_path, file_size, download_url=download_url)

                saved_files.append({
                    "filename": original_name,
                    "stored_name": timestamped_name,
                    "path": save_path,
                    "size_kb": size_kb,
                    "download_url": download_url
                })
                file_links_md.append(f"• [📥 {original_name}]({download_url}) ({size_str})")

    # 2. Process metadata entries (supports large drawings up to 500 MB on Vercel without payload limit errors)
    for meta in metadata_list:
        raw_meta_name = meta.get("filename", "blueprint.pdf")
        meta_name = safe_clean_filename(raw_meta_name)
        if allowed_file(meta_name) or meta_name.lower().endswith(('.pdf', '.dwg', '.dxf', '.cad', '.zip')):
            if any(sf["filename"] == meta_name for sf in saved_files):
                continue
            meta_size_bytes = meta.get("size_bytes", 0)
            size_kb = round(meta_size_bytes / 1024, 1)
            size_str = f"{round(size_kb / 1024, 2)} MB" if size_kb > 1024 else f"{size_kb} KB"
            download_url = meta.get("download_url") or f"/api/download/{meta_name}"
            entities_from_name = intent_detector.extract_entities_from_filename(meta_name)
            state.update_from_entities(entities_from_name)
            state.add_uploaded_file(meta_name, "", meta_size_bytes, download_url=download_url)

            saved_files.append({
                "filename": meta_name,
                "stored_name": meta_name,
                "path": "",
                "size_kb": size_kb,
                "download_url": download_url
            })
            file_links_md.append(f"• [📥 {meta_name}]({download_url}) ({size_str})")

    if not saved_files:
        return jsonify({"error": "No valid files uploaded. Please upload PDF, DWG, CAD, Excel, or ZIP files."}), 400

    # Build clear bot response with clickable download links
    detected_trades_str = ", ".join(state.trades) if state.trades else None
    trades_ack = f"\n\n🎯 **Identified Trade Scope**: **{detected_trades_str}**" if detected_trades_str else ""

    files_list_text = "\n".join(file_links_md)
    response_text = (
        f"📄 **Successfully received your project plans** ({len(saved_files)} file{'s' if len(saved_files) > 1 else ''}):\n"
        f"{files_list_text}"
        f"{trades_ack}\n\n"
        "Our estimating team can review these drawings to confirm project scope, pricing, and turnaround time.\n\n"
        "Could you please share your **Name, Company, and Email or Phone Number** so we can send the proposal once reviewed?"
    )
    quick_replies = ["Enter Contact Info", "When will I get the proposal?", "What trades do you estimate?"]

    # If lead is ready, update/save
    lead_summary = None
    if state.is_lead_ready():
        lead_record = lead_manager.save_lead(state)
        lead_summary = lead_record.get("summary_text")

    # Send instant email notification to seanray836@gmail.com
    # Note: On Vercel serverless functions, background daemon threads freeze when response returns.
    # We call email notification synchronously (with fast timeout=4s) so email delivery is guaranteed.
    try:
        email_notifier.notify_plan_upload(saved_files, state.to_dict())
    except Exception as e:
        print(f"[Upload] Notice: Email notification skipped: {e}")

    state.add_message("bot", response_text, {
        "action_type": "file_upload",
        "files": [f["filename"] for f in saved_files]
    })

    return jsonify({
        "response": response_text,
        "session_id": state.session_id,
        "files": saved_files,
        "state": state.to_dict(),
        "quick_replies": quick_replies,
        "lead_summary": lead_summary
    })


@app.route("/api/state/<session_id>", methods=["GET"])
def get_state_endpoint(session_id: str):
    """Returns the current conversation state and captured parameters."""
    state = session_manager.get_session(session_id)
    return jsonify(state.to_dict())


@app.route("/api/lead/submit", methods=["POST"])
def submit_lead_endpoint():
    """Manual or modal submission of contact info."""
    data = request.get_json() or {}
    session_id = data.get("session_id")
    state = session_manager.get_session(session_id)

    # Update state fields
    for field in ["name", "company", "email", "phone", "project_type", "square_footage", "bid_due_date"]:
        if data.get(field):
            setattr(state, field, data.get(field))

    if data.get("trades"):
        if isinstance(data.get("trades"), list):
            for t in data.get("trades"):
                if t not in state.trades:
                    state.trades.append(t)

    state.proposal_requested = True
    lead_record = lead_manager.save_lead(state)

    confirmation = (
        f"Thank you, {state.name or 'there'}! Your project details have been successfully submitted to our estimating department.\n\n"
        f"A senior estimator will review your requirements and reach out to you via {state.email or state.phone or 'email'}.\n\n"
        "Standard proposal turnaround is 2–3 business days. If you have additional addenda or drawing files, feel free to upload them anytime."
    )
    state.add_message("bot", confirmation, {"action_type": "lead_submission"})

    return jsonify({
        "success": True,
        "lead": lead_record,
        "response": confirmation,
        "state": state.to_dict()
    })


@app.route("/api/leads", methods=["GET"])
def get_leads_endpoint():
    """Returns stored leads list."""
    leads = lead_manager.get_all_leads()
    return jsonify(leads)


@app.route("/api/leads/export", methods=["GET"])
def export_leads_csv():
    """Downloads leads as CSV."""
    if os.path.exists(lead_manager.csv_path):
        return send_file(lead_manager.csv_path, as_attachment=True, download_name="estimating_leads.csv")
    return jsonify({"error": "No leads found"}), 404


@app.route("/api/reset", methods=["POST"])
def reset_endpoint():
    """Resets conversation state for a fresh session."""
    data = request.get_json() or {}
    session_id = data.get("session_id")
    new_state = session_manager.reset_session(session_id)
    return jsonify({"success": True, "session_id": new_state.session_id})


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "Estimation Service Chat Bot"})


if __name__ == "__main__":
    print("[Starting] Construction Estimating Chatbot Web Server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
