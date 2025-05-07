from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, ForeignKey, Text

db = SQLAlchemy()

class User(db.Model):
    """
    User Model representing the system's users.
    Primary Key: user_id
    """
    __tablename__ = 'USERS'

    user_id = Column(String(26), primary_key=True, nullable=False, unique=True)
    email = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(String(150), nullable=True)
    created_at = Column(String(19))  # Format: 05/07/2025 13:44:32
    last_login = Column(String(19))

    def __repr__(self):
        return f'<User {self.name} ({self.email})>'


class ImageAnalysisPDF(db.Model):
    """
    PDF Image Data Model represents the unprocessed input data uploaded by Users.
    """
    __tablename__ = 'PDF_IMAGE_ANALYSIS_DATA'

    id = Column(String(26), primary_key=True)
    user_id = Column(String(26), ForeignKey('Users.user_id'), nullable=False)
    original_filename = Column(String(255), nullable=False)
    upload_date = Column(String(19))
    raw_pdf_blob = Column(Text, nullable=True)
    processing_status = Column(String(100), nullable=True)

    def __repr__(self):
        return f'<ImageAnalysisPDF {self.original_filename}>'


class ProcessedImageAnalysisData(db.Model):
    """
    Stores AI-processed output of the PDF/image data.
    """
    __tablename__ = 'PROCESSED_IMAGE_ANALYSIS_DATA'

    id = Column(String(26), primary_key=True)
    pdf_data_id = Column(String(26), ForeignKey('PDF_IMAGE_ANALYSIS_DATA.id'), nullable=False)
    company_name = Column(String(100))
    sequences = Column(String(255))
    method_used = Column(String(100))
    body_region = Column(String(100))
    modality = Column(String(100))
    report_section_short = Column(Text)
    report_section_long = Column(Text)
    report_quality_score = Column(String(10))
    created_at = Column(String(19))

    def __repr__(self):
        return f'<ProcessedData {self.id}>'


class Finding(db.Model):
    """
    Captures individual structured findings extracted from processed data.
    """
    __tablename__ = 'FINDINGS'

    id = Column(String(26), primary_key=True)
    processed_data_id = Column(String(26), ForeignKey('PROCESSED_IMAGE_ANALYSIS_DATA.id'), nullable=False)
    finding_type = Column(String(100))
    location = Column(String(100))
    value = Column(String(50))
    unit = Column(String(50))
    significance = Column(String(255))

    def __repr__(self):
        return f'<Finding {self.finding_type} at {self.location}>'


class ErrorLog(db.Model):
    """
    Logs technical errors that occur during file processing.
    """
    __tablename__ = 'ERROR_LOGS'

    id = Column(String(26), primary_key=True)
    pdf_data_id = Column(String(26), ForeignKey('PDF_IMAGE_ANALYSIS_DATA.id'), nullable=False)
    error_type = Column(String(100))
    error_message = Column(Text)
    timestamp = Column(String(19))

    def __repr__(self):
        return f'<ErrorLog {self.error_type} at {self.timestamp}>'