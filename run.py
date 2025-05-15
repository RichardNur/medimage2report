from data.sqlite_data_manager import DataManagerInterface
from flask import Flask, redirect, url_for, render_template, abort, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from data.models.models import User, db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
from utils.helpers import generate_unique_id
from app.services.pdf_processing import extract_pdf_text, build_prompt, call_openai
import os
from sqlalchemy.orm import Session



# Set base paths
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'app', 'templates')
static_dir = os.path.join(base_dir, 'app', 'static')
db_file_name = os.path.join(base_dir, 'data', 'medimage2report.db')

# Ensure data/ directory exists
os.makedirs(os.path.dirname(db_file_name), exist_ok=True)

# Initialize Flask app
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Initialize Data Manager
data_manager = DataManagerInterface(db_file_name, app)

# Handle Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        session: Session = db.session
        return session.get(User, user_id)


@app.route('/', methods=['GET', 'POST'])
def index():
    # Handle login form on home page
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        try:
            user = data_manager.user_manager.get_user_by_email(email)
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                user.last_login = datetime.now(UTC)
                data_manager.user_manager.update_user(user.id, last_login=user.last_login)
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials', 'danger')
        except Exception as e:
            current_app.logger.exception("Login error: %s", str(e))
            flash('An error occurred. Please try again later.', 'danger')

    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('status_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        name  = request.form.get('name', '').strip()
        pwd   = request.form.get('password', '')
        role  = 'user'

        # Basic validation
        if not email or not pwd:
            flash('Email and password are required.', 'warning')
            return render_template('register.html')

        try:
            # check for existing user
            if data_manager.user_manager.get_user_by_email(email):
                flash('Email already registered.', 'warning')
                return render_template('register.html')

            uid = generate_unique_id()  # your helper for a 26-char ID
            pwd_hash = generate_password_hash(pwd)
            created = datetime.now(UTC)

            data_manager.user_manager.add_user( id=uid, email=email, password_hash=pwd_hash, name=name, role=role, created_at=created)
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('index'))

        except Exception:
            current_app.logger.exception("Registration error")
            flash('Registration failed. Please try again later.', 'danger')

    return render_template('register.html')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    """
    Upload Route:
    - Display drag-and-drop interface
    - Accept PDF file (POST)
    - Save to PDF_IMAGE_ANALYSIS_DATA
    - Redirect to request.url
    """
    if request.method == 'POST':
        file = request.files.get('pdf_file')
        if not file or not file.filename.lower().endswith('.pdf'):
            flash('Please upload a PDF file.', 'warning')
            return redirect(request.url)
        try:
            pid = generate_unique_id()
            blob = file.read()
            now = datetime.now(UTC)
            data_manager.pdf_manager.add_pdf(
                id=pid,
                user_id=current_user.id,
                original_filename=file.filename,
                upload_date=now,
                raw_pdf_blob=blob,
                processing_status='uploaded'
            )
            return redirect(url_for('process_pdf', pdf_id=pid))

        except Exception:
            current_app.logger.exception("Upload error")
            flash('Upload failed. Try again.', 'danger')
            return redirect(request.url)

    return render_template('upload_pdf.html')


@app.route('/process/<pdf_id>', methods=['GET', 'POST'])
@login_required
def process_pdf(pdf_id):
    """
    Process Route:
    - Triggered by redirect from /upload (GET)
    - Extract content from uploaded PDF
    - Build prompt and call OpenAI
    - Store the processed output
    - Redirect to /view_report/<processed_id> or error page
    """
    try:
        entry = data_manager.pdf_manager.get_pdf(pdf_id)
        if not entry or entry.user_id != current_user.id:
            abort(404)

        # Update status to "processing"
        data_manager.pdf_manager.update_processing_status(pdf_id, 'processing')

        # Step 1: Extract content from PDF

        """
        FIX TEXT-EXTRACTION FROM PDF!!!!
        """

        text_data = extract_pdf_text(entry.raw_pdf_blob)

        # Step 2: Build prompt and call OpenAI
        prompt = build_prompt(text_data)
        ai_response = call_openai(prompt)

        # Step 3: Save processed result
        proc_id = generate_unique_id()
        now = datetime.now(UTC)
        data_manager.processed_manager.add_processed_data(
            id=proc_id,
            pdf_data_id=pdf_id,
            company_name=ai_response['company'],
            sequences=ai_response['sequences'],
            method_used=ai_response['method'],
            body_region=ai_response['region'],
            modality=ai_response['modality'],
            report_section_short=ai_response['short_text'],
            report_section_long=ai_response['long_text'],
            report_quality_score=ai_response['quality'],
            created_at=now
        )

        # Update PDF status
        data_manager.pdf_manager.update_processing_status(pdf_id, 'processed')

        return redirect(url_for('view_report', processed_id=proc_id))

    except Exception:
        current_app.logger.exception("Processing error")
        data_manager.pdf_manager.update_processing_status(pdf_id, 'error')
        return redirect(url_for('error_log', pdf_id=pdf_id))


@app.route('/report/<processed_id>', methods=['GET'])
@login_required
def view_report(processed_id):
    try:
        report = data_manager.processed_manager.get_processed_data(processed_id)
        if not report or report.pdf_data.user_id != current_user.id:
            abort(404)
        return render_template('report.html', report=report)

    except Exception:
        current_app.logger.exception("View report error")
        flash('Unable to load report.', 'danger')
        return redirect(url_for('status_dashboard'))


@app.route('/status', methods=['GET'])
@login_required
def status_dashboard():
    """
    Status Route:
    - Show user uploads, their status (uploaded/processed/failed)
    - Link to reports or error logs
    """
    try:
        uploads   = data_manager.pdf_manager.get_pdfs_by_user(current_user.id)
        processed = {p.pdf_data_id for p in data_manager.processed_manager.list_all()}
        return render_template('status.html',
                               uploads=uploads,
                               processed_ids=processed)
    except Exception:
        current_app.logger.exception("Status error")
        flash('Could not fetch dashboard.', 'danger')
        return render_template('status.html', uploads=[])


@app.route('/errors/<pdf_id>', methods=['GET'])
@login_required
def error_log(pdf_id):
    """
    Error View Route:
    - Display error logs related to a specific PDF
    """
    try:
        errors = data_manager.errorlog_manager.get_errors_by_pdf_id(pdf_id)
        errors = errors or []
        return render_template('errors.html', errors=errors, pdf_id=pdf_id)
    except Exception:
        current_app.logger.exception("Error log view")
        flash('Unable to load error logs.', 'danger')
        return redirect(url_for('status_dashboard'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip() #email?
        pwd  = request.form.get('password', '')
        try:
            updates = {}
            if name:
                updates['name'] = name
            if pwd:
                updates['password_hash'] = generate_password_hash(pwd)
            if updates:
                data_manager.user_manager.update_user(current_user.id, **updates)
                flash('Profile updated.', 'success')
            return redirect(url_for('profile'))
        except Exception:
            current_app.logger.exception("Profile update error")
            flash('Update failed.', 'danger')
    return render_template('profile.html', user=current_user)


@app.route('/findings/<processed_id>', methods=['GET'])
@login_required
def view_findings(processed_id):
    """
    View Findings:
    - Show detailed structured findings table
    """
    try:
        report = data_manager.processed_manager.get_processed_data(processed_id)
        if not report or report.pdf_data.user_id != current_user.id:
            abort(404)
        findings = data_manager.finding_manager.get_findings_by_processed_id(processed_id)
        return render_template('findings.html', findings=findings, report=report)
    except Exception:
        current_app.logger.exception("View findings error")
        flash('Unable to load findings.', 'danger')
        return redirect(url_for('view_report', processed_id=processed_id))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5005)


"""
    -------- FEATURES: (?) --------
"""


# @app.route('/admin', methods=['GET'])
# @login_required
# def admin_dashboard():
#     """
#     Admin Dashboard Route:
#     - List all user uploads, reports, and error logs
#     - Only accessible to admin users
#     """
#     if current_user.role != 'admin':
#         abort(403)  # Forbidden
#     all_uploads = ImageAnalysisPDF.query.all()
#     return render_template('admin.html', uploads=all_uploads)
#
#
# @app.route('/api/pdf/<pdf_id>', methods=['GET'])
# @login_required
# def api_pdf_data(pdf_id):
#     """
#     API Route:
#     - Return raw uploaded PDF data and metadata as JSON
#     """
#     pdf_entry = ImageAnalysisPDF.query.filter_by(id=pdf_id).first_or_404()
#     return jsonify({
#         'id': pdf_entry.id,
#         'filename': pdf_entry.original_filename,
#         'upload_date': pdf_entry.upload_date.isoformat(),
#         'status': pdf_entry.processing_status,
#         'user_id': pdf_entry.user_id
#     })



# Login is handled in index.html

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('status_dashboard'))
#
#     if request.method == 'POST':
#         email    = request.form.get('email', '').strip()
#         password = request.form.get('password', '')
#
#         try:
#             user = data_manager.user_manager.get_user_by_email(email)
#             if user and check_password_hash(user.password_hash, password):
#                 login_user(user)
#                 user.last_login = datetime.utcnow()
#                 data_manager.user_manager.update_user(user.id, last_login=user.last_login)
#                 return redirect(url_for('status_dashboard'))
#             flash('Invalid email or password.', 'danger')
#         except Exception:
#             current_app.logger.exception("Login error")
#             flash('Login failed. Please try again later.', 'danger')
#
#     return render_template('login.html')