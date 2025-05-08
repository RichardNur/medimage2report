# from data.data_manager_interface import DataManagerInterface
from data.sqlite_data_manager import DataManagerInterface
from flask import redirect, url_for, render_template, jsonify, abort, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from data.models.models import ImageAnalysisPDF



if __name__ == "__main__":
    db_file_name = 'data/medimage2report.db'
    data_manager = DataManagerInterface(db_file_name)
    app = data_manager.app

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Home Route - Sections:
    Info, LogIn/SignUp (POST/GET), Example
    """
    pass

@app.route('/register', methods=['GET', 'POST'])
def register():
    # form validation
    # hash password
    # create user and store in db
    # redirect to login
    pass

@app.route('/login', methods=['GET', 'POST'])
def login():
    # check credentials
    # login_user(user)
    pass

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    """
    Upload Route:
    - Display drag-and-drop interface
    - Accept PDF file (POST)
    - Save to PDF_IMAGE_ANALYSIS_DATA
    - Redirect to '/process/<pdf_id>'
    """
    pass

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    """
    Upload Route:
    - Display drag-and-drop interface
    - Accept PDF file (POST)
    - Save to PDF_IMAGE_ANALYSIS_DATA
    - Redirect to '/process/<pdf_id>'
    """
    pass

@app.route('/process/<pdf_id>', methods=['POST'])
@login_required
def process_pdf(pdf_id):
    """
    Process Route:
    - Load PDF content from DB
    - Extract data (e.g., via PyMuPDF or pdfminer)
    - Compose and send OpenAI prompt
    - Save response to PROCESSED_IMAGE_ANALYSIS_DATA
    - Redirect to results view
    """
    pass

@app.route('/report/<processed_id>', methods=['GET'])
@login_required
def view_report(processed_id):
    """
    Report Route:
    - Display the short and long report sections
    - Also show structured findings (if any)
    """
    pass

@app.route('/status', methods=['GET'])
@login_required
def status_dashboard():
    """
    Status Route:
    - Show user uploads, their status (uploaded/processed/failed)
    - Link to reports or error logs
    """
    pass

@app.route('/errors/<pdf_id>', methods=['GET'])
@login_required
def error_log(pdf_id):
    """
    Error View Route:
    - Display error logs related to a specific PDF
    """
    pass

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

"""
    -------- FEATURES: (?) --------
"""

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Profile Route:
    - GET: Show user info
    - POST: Allow user to update name or change password
    """
    if request.method == 'POST':
        # Handle name/password change
        pass
    return render_template('profile.html', user=current_user)

@app.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    """
    Admin Dashboard Route:
    - List all user uploads, reports, and error logs
    - Only accessible to admin users
    """
    if current_user.role != 'admin':
        abort(403)  # Forbidden
    all_uploads = ImageAnalysisPDF.query.all()
    return render_template('admin.html', uploads=all_uploads)


@app.route('/findings/<processed_id>', methods=['GET'])
@login_required
def view_findings(processed_id):
    """
    Findings Route:
    - Show detailed structured findings table
    """
    pass


@app.route('/api/pdf/<pdf_id>', methods=['GET'])
@login_required
def api_pdf_data(pdf_id):
    """
    API Route:
    - Return raw uploaded PDF data and metadata as JSON
    """
    pdf_entry = ImageAnalysisPDF.query.filter_by(id=pdf_id).first_or_404()
    return jsonify({
        'id': pdf_entry.id,
        'filename': pdf_entry.original_filename,
        'upload_date': pdf_entry.upload_date.isoformat(),
        'status': pdf_entry.processing_status,
        'user_id': pdf_entry.user_id
    })

