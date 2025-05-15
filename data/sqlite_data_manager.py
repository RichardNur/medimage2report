from abc import ABC
from flask_login import LoginManager, UserMixin
from data.models.models import User, ImageAnalysisPDF, ProcessedImageAnalysisData,db

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
        """
        Delete a user by ID.

        :param id:
        :return:
        """
        pass

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
        return ImageAnalysisPDF.query.filter_by(user_id=user_id).all()

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

    def add_processed_data(self, id, pdf_data_id, company_name, sequences, method_used, body_region,
                           modality, report_section_short, report_section_long, report_quality_score, created_at):
        try:
            entry = ProcessedImageAnalysisData(
                id=id,
                pdf_data_id=pdf_data_id,
                company_name=company_name,
                sequences=sequences,
                method_used=method_used,
                body_region=body_region,
                modality=modality,
                report_section_short=report_section_short,
                report_section_long=report_section_long,
                report_quality_score=report_quality_score,
                created_at=created_at
            )
            db.session.add(entry)
            db.session.commit()
            return entry
        except Exception as e:
            db.session.rollback()
            raise e

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

        :param id:
        :param pdf_data_id:
        :param error_type:
        :param error_message:
        :param timestamp:
        :return:
        """
        pass

    def get_errors_by_pdf_id(self, pdf_data_id):
        """
        Retrieve error logs related to a specific PDF entry.

        :param pdf_data_id:
        :return:
        """
        pass

    def delete_error(self, id):
        """
        Delete an error log.

        :param id:
        :return:
        """
        pass