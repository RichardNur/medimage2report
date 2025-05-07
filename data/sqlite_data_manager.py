from data_manager_interface import DataManagerInterface


class UserDataManager(DataManagerInterface):
    """

    """

    def __init__(self, db_file_name):
        pass

    def add_user(self, id, email, password_hash, role, created_at, last_login):
        """

        :param id:
        :param email:
        :param password_hash:
        :param role:
        :param created_at:
        :param last_login:
        :return:
        """
        pass

    def update_user(self, id):
        """

        :param id:
        :return:
        """
        pass

    def delete_user(self, id):
        """

        :param id:
        :return:
        """
        pass

    def get_all_users(self):
        """

        :return:
        """
        pass

    def get_user_info(self, id):
        """

        :param id:
        :return:
        """
        pass


class DataManagerPDF(DataManagerInterface):
    """

    """

    def __init__(self):
        pass

    def add_pdf(self, pdf_filename, upload_date):
        """
        add a user upload in PDF format to the database.

        :param pdf_filename:
        :param upload_date:
        :return:
        """
        pass

    def get_pdf(self, pdf_id):
        """

        :param pdf_id:
        :return:
        """
        pass

    def delete_pdf(self, id):
        """

        :param id:
        :return:
        """
        pass
