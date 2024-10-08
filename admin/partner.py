import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crud import admin_crud
from database_sqlalchemy import SessionLocal

class Partner:
    def __init__(self):
        with SessionLocal() as session:
            self.list_of_partner = {}
            self.refresh_partner(session)

    def refresh_partner(self, session):
        partners = admin_crud.get_all_active_partner(session)
        for partner in partners:
            self.list_of_partner[partner.owner.chat_id] = partner


partners = Partner()