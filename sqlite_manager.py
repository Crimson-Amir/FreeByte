import sqlite3
from database_sqlalchemy import SessionLocal
import models_sqlalchemy as model
from sqlalchemy import update

class ManageDb:
    def __init__(self, db_name: str = "test"):
        self.db_name = db_name + ".db"


    @staticmethod
    def init_name(name):
        if isinstance(name, str):
            return name.replace("'", "").replace('"', "")
        else:
            return name


    def create_table(self, table: dict):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for key, val in table.items():
                coul = [f"{name} {v}" for name, v in val.items()]
                cursor.execute("CREATE TABLE IF NOT EXISTS {0} ({1})".format(key, ", ".join(coul)))
            db.commit()


    def select(self, column: str = "*", table: str = "sqlite_master",
               where: str = None, distinct: bool = False, order_by: str = None,
               limit: int = None):
        distinct_ = "DISTINCT " if distinct else ''
        order_by_ = f'ORDER BY {order_by}' if order_by else ''
        limit_ = f'LIMIT {limit}' if limit else ''
        where_ = f'WHERE {where}' if where else ''

        sql = f"SELECT {distinct_}{column} FROM {table} {where_} {order_by_} {limit_}"

        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            cursor.execute(sql)
            db_values = cursor.fetchall()
        return db_values


    def insert(self, table: str, rows: dict):
        column = ', '.join(rows.keys())
        values = [f"'{self.init_name(val)}'" for val in rows.values()]

        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            cursor.execute(f'INSERT INTO {table} ({column}) VALUES ({", ".join(values)})')
            db.commit()
        return cursor.lastrowid


    def delete(self, table: dict):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for key, value in table.items():
                cursor.execute(f"DELETE FROM {key} WHERE {value[0]}='{value[1]}'")
            db.commit()


    def advanced_delete(self, table):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for key, value in table.items():
                where = ''
                for arg in value:
                    key_ = arg[0]
                    val_ = arg[1] if type(arg[1]) is int else f'"{arg[1]}"'
                    where += f'{key_} = {val_} AND '
                cursor.execute(f"DELETE FROM {key} WHERE {where[:-4]}")
            db.commit()


    def drop_table(self, table: str):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            db.commit()


    def update(self, table, where):
        where = f'where {where}' or None

        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for key, value in table.items():
                for k, v in value.items():
                    text = f"UPDATE {key} SET {k} = '{self.init_name(v)}' {where}"
                    cursor.execute(text)
                db.commit()
        return cursor.lastrowid


    def custom(self, order: str, return_fetcall=True):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            cursor.execute(order)
            db.commit()
        if return_fetcall:
            return cursor.fetchall()


    def custom_multi(self, *order):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for order_ in order:
                cursor.execute(order_)
                db.commit()


sqlite_manager = ManageDb('v2ray')
get_all_user = sqlite_manager.custom('select name,user_name,chat_id,wallet,invited_by from User')

with SessionLocal() as session:
    with session.begin():
        user_id = []
        for user in get_all_user:

            name,user_name,chat_id,wallet,invited_by = user
            if user_name == 'None':
                user_name = None

            if chat_id in user_id or chat_id == 6450325872:
                continue

            new_user = model.UserDetail(
                first_name=name,
                username=user_name,
                chat_id=chat_id,
                wallet=wallet,
                language='fa'
            )
            session.add(new_user)
            session.flush()
            session.refresh(new_user)

            user_config = model.UserConfig(
                chat_id=new_user.chat_id,
                user_level=3
            )
            session.add(user_config)
            user_id.append(chat_id)

            sqlite_manager.custom(f'update UserDetail set wallet = 0 where chat_id = {chat_id}')
#

with SessionLocal() as session:
    with session.begin():
        user_id = []
        for user in get_all_user:

            invited_by, chat_id = user[4], user[2]
            if invited_by == 'None':
                invited_by = None

            if chat_id in user_id:
                continue

            stmt = (
                update(model.UserDetail)
                .where(model.UserDetail.chat_id == chat_id)
                .values(
                    invited_by=invited_by
                )
            )
            session.execute(stmt)