# db.py  ── single source of truth for MySQL connections + pretty IDs
import os, uuid, mysql.connector

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS" , "@@Arifin012"),
        database=os.getenv("DB_NAME" , "Automata"),
        auth_plugin="mysql_native_password",
        autocommit=True,
    )

def make_public_id(name: str | None = None) -> str:
    if name:
        slug = "".join(c.lower() for c in name if c.isalnum() or c in "-_")
        return slug[:32] or uuid.uuid4().hex
    return uuid.uuid4().hex
