import json, os
import mysql.connector
# from fa_base import FiniteAutomaton

'''
    class FiniteAutomaton:
    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[str, Dict[str, Set[str]]]
    start_state: str
    final_states: Set[str]
    
    Equivalent to 
    
    class FiniteAutomaton:
    states: ["" , ""]
    alphabet: ["" , ""]
    transitions: {
        "q0": 
    }
'''








# ── Connection helpers ───────────────────────────────────────────────────
def _get_conn():
    return mysql.connector.connect(
        host     = os.getenv("FA_DB_HOST", "localhost"),
        user     = os.getenv("FA_DB_USER", "fa_user"),
        password = os.getenv("FA_DB_PASS", "secret"),
        database = os.getenv("FA_DB_NAME", "finite_automata")
    )

# ── Schema (run once) ────────────────────────────────────────────────────
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS automata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) UNIQUE,
    is_dfa BOOLEAN,
    start_state VARCHAR(64),
    final_states TEXT,        -- JSON list
    alphabet TEXT,            -- JSON list
    transitions LONGTEXT      -- JSON dict
);
"""

def init_db():
    with _get_conn() as cnx:
        cur = cnx.cursor()
        cur.execute(SCHEMA_SQL)
        cnx.commit()

# ── CRUD ─────────────────────────────────────────────────────────────────
def save(name: str, fa: FiniteAutomaton):
    data = (
        name,
        fa.is_dfa(),
        fa.start_state,
        json.dumps(list(fa.final_states)),
        json.dumps(list(fa.alphabet)),
        json.dumps(fa.transitions)
    )
    with _get_conn() as cnx:
        cur = cnx.cursor()
        cur.execute("""
            INSERT INTO automata
              (name, is_dfa, start_state, final_states, alphabet, transitions)
              VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              is_dfa=VALUES(is_dfa),
              start_state=VALUES(start_state),
              final_states=VALUES(final_states),
              alphabet=VALUES(alphabet),
              transitions=VALUES(transitions)
        """, data)
        cnx.commit()

def load(name: str) -> FiniteAutomaton | None:
    with _get_conn() as cnx:
        cur = cnx.cursor(dictionary=True)
        cur.execute("SELECT * FROM automata WHERE name=%s", (name,))
        row = cur.fetchone()
    if not row:
        return None
    return FiniteAutomaton(
        states=set(json.loads(row["transitions"]).keys()),
        alphabet=set(json.loads(row["alphabet"])),
        transitions=json.loads(row["transitions"]),
        start_state=row["start_state"],
        final_states=set(json.loads(row["final_states"]))
    )
