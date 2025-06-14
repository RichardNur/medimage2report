from abc import ABC
from datetime import datetime, timezone
from flask_login import LoginManager
from data.models.models import User, ImageAnalysisPDF, ProcessedImageAnalysisData, ErrorLog, db
from utils.helpers import generate_unique_id


class DataManagerInterface(ABC):
    """
    An abstract base class that defines the interface for data management operations.
    """

    def __init__(self, db_file_name, app):
        """
        Initializes the SQLiteDataManager, sets up Flask and SQLAlchemy,
        and creates database tables if they don't exist.

        Args:
            db_file_name (str): The SQLite database file path.
        """

        self.app = app
        self.app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{db_file_name}'
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config['SECRET_KEY'] = '6b809f7762e4a672f4d57d951d87c67bff1991ee9eea687d' # for flash messages

        # Initialize all data managers
        self.user_manager = UserDataManager()
        self.pdf_manager = PDFDataManager()
        self.processed_manager = ProcessedDataManager()
        self.finding_manager = FindingDataManager()
        self.errorlog_manager = ErrorLogManager()

        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = 'login'  # endpoint name for login

        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()


class UserDataManager:
    """
    Manages User table operations.
    """

    def add_user(self, id, email, password_hash, name, role, created_at):
        try:
            user = User(
                id=id,
                email=email,
                password_hash=password_hash,
                name=name,
                role=role,
                created_at=created_at,
                last_login=None
            )
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise e

    def get_user_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def update_user(self, id, **kwargs):
        try:
            user = User.query.get(id)
            if not user:
                return None
            for key, value in kwargs.items():
                setattr(user, key, value)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise e

    def delete_user(self, id):
        try:
            user = User.query.get(id)
            if not user:
                return False
            db.session.delete(user)
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()

            # Log the error directly via the ErrorLog model
            err = ErrorLog(
                id=generate_unique_id(),
                pdf_data_id=None,                            # no PDF in this context
                error_type="UserDeletionError",
                error_message=str(e),
                timestamp=datetime.now(timezone.utc)         # timezone‐aware
            )
            db.session.add(err)
            db.session.commit()

            # re-raise so caller still sees the exception if they want to handle it
            raise

    def get_all_users(self):
        """
        Retrieve all users.

        :return:
        """
        pass



class PDFDataManager:
    """
    Manages ImageAnalysisPDF table operations.
    """

    def add_pdf(self, id, user_id, original_filename, upload_date, raw_pdf_blob, processing_status):
        try:
            pdf_entry = ImageAnalysisPDF(
                id=id,
                user_id=user_id,
                original_filename=original_filename,
                upload_date=upload_date,
                raw_pdf_blob=raw_pdf_blob,
                processing_status=processing_status
            )
            db.session.add(pdf_entry)
            db.session.commit()
            return pdf_entry
        except Exception as e:
            db.session.rollback()
            raise e

    def get_pdfs_by_user(self, user_id):
        return (
            ImageAnalysisPDF.query
            .filter_by(user_id=user_id)
            .order_by(ImageAnalysisPDF.upload_date.desc())
            .all()
        )

    def get_pdf(self, pdf_id):
        return ImageAnalysisPDF.query.filter_by(id=pdf_id).first()

    def delete_pdf(self, id):
        try:
            pdf_entry = self.get_pdf(id)
            if pdf_entry:
                db.session.delete(pdf_entry)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

    def update_processing_status(self, pdf_id, new_status):
        try:
            pdf_entry = self.get_pdf(pdf_id)
            if pdf_entry:
                pdf_entry.processing_status = new_status
                db.session.commit()
                return pdf_entry
            return None
        except Exception as e:
            db.session.rollback()
            raise e








class ProcessedDataManager:
    """
    Manages ProcessedImageAnalysisData table operations.
    """

    def add_processed_data(
        self,
        id, pdf_data_id, company_name, sequences, method_used, body_region,
        modality,
        report_section_short_openai, report_section_long_openai,
        report_section_short_gemini, report_section_long_gemini,
        # --- Add new German fields to the method signature ---
        report_section_short_openai_de, report_section_long_openai_de,
        report_section_short_gemini_de, report_section_long_gemini_de,
        report_quality_score, created_at
    ):
        try:
            entry = ProcessedImageAnalysisData(
                id=id,
                pdf_data_id=pdf_data_id,
                company_name=company_name,
                sequences=sequences,
                method_used=method_used,
                body_region=body_region,
                modality=modality,
                # English fields
                report_section_short_openai=report_section_short_openai,
                report_section_long_openai=report_section_long_openai,
                report_section_short_gemini=report_section_short_gemini,
                report_section_long_gemini=report_section_long_gemini,
                # --- Assign new German fields ---
                report_section_short_openai_de=report_section_short_openai_de,
                report_section_long_openai_de=report_section_long_openai_de,
                report_section_short_gemini_de=report_section_short_gemini_de,
                report_section_long_gemini_de=report_section_long_gemini_de,
                # Remaining fields
                report_quality_score=report_quality_score,
                created_at=created_at
            )
            db.session.add(entry)
            db.session.commit()
            return entry
        except Exception:
            db.session.rollback()
            raise

    def get_processed_data(self, id):
        return ProcessedImageAnalysisData.query.get(id)

    def delete_processed_data(self, id):
        try:
            entry = ProcessedImageAnalysisData.query.get(id)
            if entry:
                db.session.delete(entry)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

    def list_all(self):
        """
        Return all processed reports from the database.
        """
        return ProcessedImageAnalysisData.query.all()

    def get_by_pdf_id(self, pdf_id):
        """
        Return the first processed report matching the given PDF ID.
        Assumes a 1:1 relationship between PDF and processed report.
        """
        return ProcessedImageAnalysisData.query.filter_by(pdf_data_id=pdf_id).first()




class FindingDataManager:
    """
    Manages Findings table operations.
    """

    def add_finding(self, id, processed_data_id, finding_type, location, value, unit, significance):
        """
        Add structured finding from processed output.

        :return:
        """
        pass

    def get_findings_by_processed_id(self, processed_data_id):
        """
        Retrieve findings associated with processed data.

        :param processed_data_id:
        :return:
        """
        pass

    def delete_finding(self, id):
        """
        Delete a finding by ID.

        :param id:
        :return:
        """
        pass


class ErrorLogManager:
    """
    Manages ErrorLog table operations.
    """
    def log_error(self, id, pdf_data_id, error_type, error_message, timestamp):
        """
        Log an error that occurred during processing.
        """
        from data.models.models import ErrorLog
        entry = ErrorLog(
            id=id,
            pdf_data_id=pdf_data_id,
            error_type=error_type,
            error_message=error_message,
            timestamp=timestamp
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def get_errors_by_pdf_id(self, pdf_data_id):
        """
        Retrieve error logs related to a specific PDF entry.
        """
        from data.models.models import ErrorLog
        return (
            ErrorLog.query
            .filter_by(pdf_data_id=pdf_data_id)
            .order_by(ErrorLog.timestamp.desc())
            .all()
        )

    def delete_error(self, id):
        """
        Delete a single error log by its ID.
        """
        from data.models.models import ErrorLog
        entry = ErrorLog.query.get(id)
        if entry:
            db.session.delete(entry)
            db.session.commit()
            return True
        return False

    def clear_errors_by_pdf_id(self, pdf_data_id):
        """
        Delete all error logs for a given PDF.
        """
        from data.models.models import ErrorLog
        entries = ErrorLog.query.filter_by(pdf_data_id=pdf_data_id).all()
        for entry in entries:
            db.session.delete(entry)
        db.session.commit()
        return len(entries)