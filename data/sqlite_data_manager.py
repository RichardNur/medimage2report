from data_manager_interface import DataManagerInterface


class UserDataManager(DataManagerInterface):
    """
    Manages User table operations.
    """

    def __init__(self, db_file_name):
        pass

    def add_user(self, id, email, password_hash, name, role, created_at, last_login):
        """
        Add a new user.

        :param id:
        :param email:
        :param password_hash:
        :param name:
        :param role:
        :param created_at:
        :param last_login:
        :return:
        """
        pass

    def update_user(self, id, **kwargs):
        """
        Update existing user fields.

        :param id:
        :param kwargs: Fields to update
        :return:
        """
        pass

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

    def get_user_info(self, id):
        """
        Get a single user's info.

        :param id:
        :return:
        """
        pass


class PDFDataManager(DataManagerInterface):
    """
    Manages ImageAnalysisPDF table operations.
    """

    def __init__(self):
        pass

    def add_pdf(self, id, user_id, original_filename, upload_date, raw_pdf_blob, processing_status):
        """
        Add uploaded PDF metadata.

        :param id:
        :param user_id:
        :param original_filename:
        :param upload_date:
        :param raw_pdf_blob:
        :param processing_status:
        :return:
        """
        pass

    def get_pdf(self, pdf_id):
        """
        Retrieve a PDF entry by ID.

        :param pdf_id:
        :return:
        """
        pass

    def delete_pdf(self, id):
        """
        Delete PDF by ID.

        :param id:
        :return:
        """
        pass

    def update_processing_status(self, pdf_id, new_status):
        """
        Update processing status of a PDF entry.

        :param pdf_id:
        :param new_status:
        :return:
        """
        pass


class ProcessedDataManager(DataManagerInterface):
    """
    Manages ProcessedImageAnalysisData table operations.
    """

    def __init__(self):
        pass

    def add_processed_data(self, id, pdf_data_id, company_name, sequences, method_used, body_region,
                           modality, report_section_short, report_section_long, report_quality_score, created_at):
        """
        Add processed image analysis data.

        :return:
        """
        pass

    def get_processed_data(self, id):
        """
        Retrieve processed data by ID.

        :param id:
        :return:
        """
        pass

    def delete_processed_data(self, id):
        """
        Delete processed data by ID.

        :param id:
        :return:
        """
        pass

    def list_processed_reports_by_pdf(self, pdf_data_id):
        """
        List all processed entries for a given PDF.

        :param pdf_data_id:
        :return:
        """
        pass


class FindingDataManager(DataManagerInterface):
    """
    Manages Findings table operations.
    """

    def __init__(self):
        pass

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


class ErrorLogManager(DataManagerInterface):
    """
    Manages ErrorLog table operations.
    """

    def __init__(self):
        pass

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