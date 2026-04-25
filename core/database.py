from core.db import DB
def get_db():
    return DB.get_session()