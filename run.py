import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, redirect, url_for, render_template, abort, request, flash, current_app, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from data.models.models import User, ErrorLog, db
from data.sqlite_data_manager import DataManagerInterface
from utils.helpers import generate_unique_id
from app.services.pdf_processing import extract_pdf_content, build_prompt, call_openai, call_gemini


# Load .env as early as possible
load_dotenv()

# -----------------------------------------------------------------------------
# App configuration & initialization
# -----------------------------------------------------------------------------
base_dir     = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'app', 'templates')
static_dir   = os.path.join(base_dir, 'app', 'static')
db_file      = os.path.join(base_dir, 'data', 'medimage2report.db')

# ensure data dir
os.makedirs(os.path.dirname(db_file), exist_ok=True)

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config.update({
    'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,      # 10 MB
    'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_file}',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SECRET_KEY': os.getenv('FLASK_SECRET_KEY', generate_unique_id()),  # fallback if unset
})

# Initialize Data Manager
data_manager = DataManagerInterface(db_file, app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'  # or 'login'


# -----------------------------------------------------------------------------
# Error‐logging helper
# -----------------------------------------------------------------------------
def _log_pdf_error(pdf_id: str, exc: Exception):
    """
    Persist an entry in ERROR_LOGS for this PDF and mark its status 'error'.
    """
    try:
        err = ErrorLog(
            id=generate_unique_id(),
            pdf_data_id=pdf_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(err)
        db.session.commit()
    except Exception as db_err:
        # If logging itself fails, write to the main app logger
        logging.exception("Failed to write to ERROR_LOGS: %s", db_err)

    # finally, attempt e mark the PDF itself as errored
    try:
        data_manager.pdf_manager.update_processing_status(pdf_id, 'error')
    except Exception:
        # swallow, there's nothing more we can do
        pass

# -----------------------------------------------------------------------------
# User‐loader for Flask‐Login
# -----------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    with app.app_context():
        return db.session.get(User, user_id)


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Login page & handler.
    """
    if request.method == 'POST':
        email    = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''

        if not email or not password:
            flash('Email and password are required.', 'warning')
            return render_template('index.html')

        try:
            user = data_manager.user_manager.get_user_by_email(email)
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                user.last_login = datetime.now(timezone.utc)
                data_manager.user_manager.update_user(user.id, last_login=user.last_login)
                return redirect(url_for('status'))
            else:
                flash('Invalid email or password.', 'danger')
        except Exception as e:
            current_app.logger.exception("Login error")
            flash('An internal error occurred. Please try again later.', 'danger')

    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration Route:
    - Show registration form (GET)
    - Handle new user signup (POST)
    """
    # If already logged in, send the user to their dashboard
    if current_user.is_authenticated:
        return redirect(url_for('status'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        name  = (request.form.get('name')  or '').strip()
        pwd   = request.form.get('password') or ''
        role  = 'user'

        # Basic validation
        if not email or not pwd:
            flash('Email and password are required.', 'warning')
            return render_template('register.html', email=email, name=name)

        try:
            # Prevent duplicate registrations
            if data_manager.user_manager.get_user_by_email(email):
                flash('That email is already registered.', 'warning')
                return render_template('register.html', email=email, name=name)

            uid       = generate_unique_id()
            pwd_hash  = generate_password_hash(pwd)
            created   = datetime.now(timezone.utc)

            data_manager.user_manager.add_user(
                id=uid,
                email=email,
                password_hash=pwd_hash,
                name=name,
                role=role,
                created_at=created
            )

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            current_app.logger.exception("Registration error")
            flash('An internal error occurred. Please try again later.', 'danger')
            # fall through to re-render form

    return render_template('register.html')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    """
    Upload Route:
    - GET:  Render drag-and-drop PDF upload form
    - POST: Validate & save uploaded PDF, then kick off processing
    """
    if request.method == 'POST':
        uploaded_file = request.files.get('pdf_file')

        # Validate presence and extension
        if not uploaded_file or not uploaded_file.filename.lower().endswith('.pdf'):
            flash('Please select a valid PDF file to upload.', 'warning')
            return render_template('upload_pdf.html')

        blob = uploaded_file.read()
        if not blob:
            flash('Uploaded file appears to be empty.', 'warning')
            return render_template('upload_pdf.html')

        pid = generate_unique_id()
        now = datetime.now(timezone.utc)

        try:
            data_manager.pdf_manager.add_pdf(
                id=pid,
                user_id=current_user.id,
                original_filename=uploaded_file.filename,
                upload_date=now,
                raw_pdf_blob=blob,
                processing_status='uploaded'
            )
            return redirect(url_for('process_pdf', pdf_id=pid))

        except Exception as e:
            current_app.logger.exception("Upload error")
            flash('Failed to save PDF. Please try again later.', 'danger')
            return render_template('upload_pdf.html')

    # GET request
    return render_template('upload_pdf.html')


@app.route('/process/<pdf_id>', methods=['GET', 'POST'])
@login_required
def process_pdf(pdf_id):
    """
    Process Route:
    - Triggered after upload
    - Extract content from uploaded PDF
    - Build prompt and call OpenAI
    - Store the processed output
    - Redirect to /view_report/<processed_id> or error page
    """
    try:
        entry = data_manager.pdf_manager.get_pdf(pdf_id)
        if not entry or entry.user_id != current_user.id:
            abort(404)

        # 1) mark as processing
        data_manager.pdf_manager.update_processing_status(pdf_id, 'processing')

        # 2) extract text
        extracted = extract_pdf_content(entry.raw_pdf_blob, lang="deu")
        if not extracted or not extracted.get('raw_text'):
            raise ValueError("No usable text extracted from PDF.")

        # 3) build prompt & call GPT
        prompt = build_prompt(extracted)
        ai_response = call_gemini(prompt)

        # 4) persist AI output
        proc_id = generate_unique_id()
        now = datetime.now(timezone.utc)
        sequences = ai_response.get('sequences', [])
        if isinstance(sequences, list):
            sequences = ", ".join(sequences)

        data_manager.processed_manager.add_processed_data(
            id=proc_id,
            pdf_data_id=pdf_id,
            company_name   = ai_response.get('company'),
            sequences      = sequences,
            method_used    = ai_response.get('method'),
            body_region    = ai_response.get('region'),
            modality       = ai_response.get('modality'),
            report_section_short = ai_response.get('short_text'),
            report_section_long  = ai_response.get('long_text'),
            report_quality_score = ai_response.get('quality'),
            created_at=now
        )

        # 5) mark as done
        data_manager.pdf_manager.update_processing_status(pdf_id, 'processed')
        return redirect(url_for('view_report', processed_id=proc_id))

    except Exception as exc:
        # 1) log full traceback
        current_app.logger.exception("Processing error on PDF %s", pdf_id)

        # 2) persist error + update status
        _log_pdf_error(pdf_id, exc)

        # 3) send user to the error‐view
        flash("An error occurred during processing. See error log for details.", "warning")
        return redirect(url_for('error_log', pdf_id=pdf_id))



@app.route('/status', methods=['GET'])
@login_required
def status():
    """
    Status Route:
    - Show current user’s uploads and their processing status.
    - Report links load on demand; errors are accessible separately.
    """
    try:
        uploads = data_manager.pdf_manager.get_pdfs_by_user(current_user.id)
    except Exception as e:
        current_app.logger.exception("Status error: %s", e)
        flash('Could not load your uploads. Please try again later.', 'danger')
        uploads = []
    return render_template('status.html', uploads=uploads)


@app.route('/errors/<pdf_id>', methods=['GET'])
@login_required
def error_log(pdf_id):
    """
    Error View Route:
    - Show processing errors for a given PDF.
    - If the PDF does not belong to the current user, return 404.
    """
    # Verify ownership
    entry = data_manager.pdf_manager.get_pdf(pdf_id)
    if not entry or entry.user_id != current_user.id:
        abort(404)

    try:
        errors = data_manager.errorlog_manager.get_errors_by_pdf_id(pdf_id) or []
        # Determine whether a report exists for this PDF
        processed_ids = {
            proc.pdf_data_id
            for proc in data_manager.processed_manager.list_all()
            if proc.pdf_data.user_id == current_user.id
        }
        return render_template(
            'errors.html',
            errors=errors,
            pdf_id=pdf_id,
            processed_ids=processed_ids
        )
    except Exception as e:
        current_app.logger.exception("Error log view failed: %s", e)
        flash('Unable to load error log. Please try again later.', 'danger')
        return redirect(url_for('status'))


@app.route('/errors/<pdf_id>/clear', methods=['POST'])
@login_required
def clear_errors(pdf_id):
    """
    Clears all error log entries for the specified PDF,
    then reloads the error-log view.
    """
    # Verify ownership
    entry = data_manager.pdf_manager.get_pdf(pdf_id)
    if not entry or entry.user_id != current_user.id:
        abort(404)

    try:
        data_manager.errorlog_manager.clear_errors_by_pdf_id(pdf_id)
        flash('All error logs cleared successfully.', 'success')
    except Exception as e:
        current_app.logger.exception("Failed to clear error logs: %s", e)
        flash('Could not clear error logs. Please try again.', 'danger')

    return redirect(url_for('error_log', pdf_id=pdf_id))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Profile Route:
    - GET: Show current user's profile form
    - POST: Update name and/or password
    """
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        pwd  = request.form.get('password', '')
        try:
            updates = {}
            if name:
                updates['name'] = name
            if pwd:
                updates['password_hash'] = generate_password_hash(pwd)
            if updates:
                updated = data_manager.user_manager.update_user(current_user.id, **updates)
                if updated:
                    flash('Profile updated successfully.', 'success')
                else:
                    flash('No changes were applied.', 'info')
            return redirect(url_for('profile'))
        except Exception as e:
            current_app.logger.exception("Profile update error: %s", e)
            flash('Could not update profile. Please try again later.', 'danger')
            return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


@app.route('/view_report/<processed_id>', methods=['GET'])
@login_required
def view_report(processed_id):
    """
    View Route:
    - Display the AI-generated structured report (short + long, meta info).
    """
    try:
        report = data_manager.processed_manager.get_processed_data(processed_id)
        # Ownership check
        if not report or report.pdf_data.user_id != current_user.id:
            abort(404)
        return render_template('view_report.html', report=report)
    except Exception as e:
        current_app.logger.exception("View report error: %s", e)
        flash('Unable to load the report. Please try again later.', 'danger')
        return redirect(url_for('status'))


@app.route('/pdf/<pdf_id>')
@login_required
def serve_pdf(pdf_id):
    """
    PDF Serve Route:
    - Return the original uploaded PDF in-browser.
    """
    try:
        entry = data_manager.pdf_manager.get_pdf(pdf_id)
        if not entry or entry.user_id != current_user.id:
            abort(404)
        return Response(
            entry.raw_pdf_blob,
            mimetype='application/pdf',
            headers={"Content-Disposition": f"inline; filename={entry.original_filename}"}
        )
    except Exception as e:
        current_app.logger.exception("Serve PDF error: %s", e)
        flash('Could not load PDF. Please try again later.', 'danger')
        return redirect(url_for('status'))


@app.route('/view_report_by_pdf/<pdf_id>', methods=['GET'])
@login_required
def view_report_by_pdf_id(pdf_id):
    """
    Redirect Route:
    - Find processed_id for the given pdf_id and redirect to view_report.
    """
    try:
        processed = data_manager.processed_manager.get_by_pdf_id(pdf_id)
        if not processed or processed.pdf_data.user_id != current_user.id:
            abort(404)
        return redirect(url_for('view_report', processed_id=processed.id))
    except Exception as e:
        current_app.logger.exception("Redirect to report failed: %s", e)
        flash('Could not find the report. Please try again later.', 'danger')
        return redirect(url_for('status'))


@app.route('/logout')
@login_required
def logout():
    """
    Logout Route:
    - Logs out the current user and returns to the home page.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


if __name__ == "__main__":
    # Use environment-configured host/port if available
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5005))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes')
    app.run(debug=debug, host=host, port=port)

