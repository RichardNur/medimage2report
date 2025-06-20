from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class User(db.Model):
    """
    User Model representing system users.
    Primary Key: id
    """
    __tablename__ = 'USERS'

    id = Column(String(26), primary_key=True, nullable=False, unique=True)
    email = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(String(150), nullable=True)
    created_at = Column(DateTime, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f'<User {self.name} ({self.email})>'

    # Flask-Login required properties
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class ImageAnalysisPDF(db.Model):
    """
    Stores uploaded image analysis PDFs before processing.
    """
    __tablename__ = 'PDF_IMAGE_ANALYSIS_DATA'

    id = Column(String(26), primary_key=True)
    user_id = Column(String(26), ForeignKey('USERS.id'), nullable=False)
    original_filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    raw_pdf_blob = Column(Text, nullable=True)  # Can be switched to LargeBinary for raw bytes
    processing_status = Column(String(100), nullable=True)

    def __repr__(self):
        return f'<ImageAnalysisPDF {self.original_filename}>'


class ProcessedImageAnalysisData(db.Model):
    __tablename__ = 'PROCESSED_IMAGE_ANALYSIS_DATA'

    id = Column(String(26), primary_key=True)
    pdf_data_id = Column(String(26), ForeignKey('PDF_IMAGE_ANALYSIS_DATA.id'), nullable=False)

    company_name = Column(String(100), nullable=True)
    sequences    = Column(String(255), nullable=True)
    method_used  = Column(String(100), nullable=True)
    body_region  = Column(String(100), nullable=True)
    modality     = Column(String(100), nullable=True)

    # --- English Reports (Original) ---
    report_section_short_openai = Column(Text, nullable=True)
    report_section_long_openai  = Column(Text, nullable=True)
    report_section_short_gemini = Column(Text, nullable=True)
    report_section_long_gemini  = Column(Text, nullable=True)

    # --- GERMAN REPORTS (NEW) ---
    report_section_short_openai_de = Column(Text, nullable=True)
    report_section_long_openai_de  = Column(Text, nullable=True)
    report_section_short_gemini_de = Column(Text, nullable=True)
    report_section_long_gemini_de  = Column(Text, nullable=True)

    report_quality_score = Column(String(10), nullable=True)
    created_at           = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    pdf_data = relationship("ImageAnalysisPDF", backref="processed_reports")

    def __repr__(self):
        return f'<ProcessedData {self.id}>'


class Finding(db.Model):
    """
    Captures individual structured findings from processed image data.
    """
    __tablename__ = 'FINDINGS'

    id = Column(String(26), primary_key=True)
    processed_data_id = Column(String(26), ForeignKey('PROCESSED_IMAGE_ANALYSIS_DATA.id'), nullable=False)
    finding_type = Column(String(100), nullable=False)
    location = Column(String(100), nullable=True)
    value = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    significance = Column(String(255), nullable=True)

    def __repr__(self):
        return f'<Finding {self.finding_type} at {self.location}>'


class ErrorLog(db.Model):
    """
    Logs technical errors that occur during PDF processing.
    """
    __tablename__ = 'ERROR_LOGS'

    id = Column(String(26), primary_key=True)
    pdf_data_id = Column(String(26), ForeignKey('PDF_IMAGE_ANALYSIS_DATA.id'), nullable=False)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<ErrorLog {self.error_type} at {self.timestamp}>'