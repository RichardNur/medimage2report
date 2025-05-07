import datetime

class UserDataManager():
    """

    """
    def __init__(self, db_filepath):
        """

        """
        pass

    def get_all_users(self):
        """

        :return:
        """
        pass

    def create_user(self, id, email, password_hash, role, created_at, last_login=datetime.datetime.now().ctime()):
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


if __name__ == "__main__":
    print(datetime.datetime.now().ctime().split()[1:])
    print("Format: " + str(len("05/07/2025 13:44:32")))