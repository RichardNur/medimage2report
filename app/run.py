# from data.data_manager_interface import DataManagerInterface
from data.sqlite_data_manager import DataManagerInterface

if __name__ == "__main__":
    db_file_name = 'data/medimage2report.db'
    data_manager = DataManagerInterface(db_file_name)
    app = data_manager.app

@app.route('/')
def index():
    pass