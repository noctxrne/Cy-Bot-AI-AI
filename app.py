from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
from bot_backend import get_bot_response, process_pdf, remove_pdf_from_memory

app = Flask(__name__)
app.secret_key = "cyberlaw_secret"

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    # Clear chat on refresh
    session.pop("history", None)
    session["history"] = []
    return render_template("index.html", chat_history=session["history"])

@app.route("/get_response", methods=["POST"])
def get_response():
    user_msg = request.json["message"]
    has_pdf = request.json.get("has_pdf", False)
    
    bot_msg = get_bot_response(user_msg, has_pdf)
    print(f"Bot response/error: {bot_msg}")

    entry = {"user": user_msg, "bot": bot_msg}
    history = session.get("history", [])
    history.append(entry)
    session["history"] = history

    return jsonify({"bot": bot_msg})

@app.route("/clear", methods=["POST"])
def clear_chat():
    session.pop("history", None)
    return jsonify({"status": "cleared"})

@app.route("/get_history", methods=["GET"])
def get_history():
    return jsonify({"history": session.get("history", [])})

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})
    
    if file and allowed_file(file.filename):
        # Generate unique ID for the PDF
        pdf_id = str(uuid.uuid4())
        filename = secure_filename(f"{pdf_id}.pdf")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the PDF
        try:
            process_pdf(pdf_id, file_path)
            pdf_url = f"/uploads/{filename}"
            return jsonify({
                "success": True, 
                "pdf_id": pdf_id,
                "pdf_url": pdf_url
            })
        except Exception as e:
            # Clean up the file if processing failed
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": False, "error": "Invalid file type"})

@app.route("/remove_pdf", methods=["POST"])
def remove_pdf():
    pdf_id = request.json.get("pdf_id")
    if not pdf_id:
        return jsonify({"success": False, "error": "No PDF ID provided"})
    
    try:
        # Remove from memory
        remove_pdf_from_memory(pdf_id)
        
        # Remove file from disk
        filename = secure_filename(f"{pdf_id}.pdf")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)