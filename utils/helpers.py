# utils/helpers.py
import uuid

def generate_unique_id():
    return uuid.uuid4().hex[:26]