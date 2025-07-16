# ─────────────────────────────────────────────────────────────────────────────
# fa_database.py
#
# All DB I/O for NFAs / DFAs.
# Requires db.py (get_connection, make_public_id) and fa_logic.FiniteAutomaton.
# ─────────────────────────────────────────────────────────────────────────────
from typing import Optional
from db import get_connection, make_public_id
from fa_logic import FiniteAutomaton


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  DDL helper – call once at app start‑up                     │
# ╰──────────────────────────────────────────────────────────────────────────╯
def init_all_tables() -> None:
    """Create every table if it does not already exist."""
    ddl = [
        """
        CREATE TABLE IF NOT EXISTS NFAs (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            public_id  VARCHAR(64) UNIQUE,
            name       VARCHAR(255) NOT NULL,
            type       ENUM('NFA','DFA') NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS NFA_States (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            nfa_id    INT,
            state     VARCHAR(255),
            is_start  BOOLEAN DEFAULT FALSE,
            is_final  BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (nfa_id) REFERENCES NFAs(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS NFA_Transitions (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            nfa_id          INT,
            from_state_id   INT,
            symbol          VARCHAR(32),
            to_state_id     INT,
            FOREIGN KEY (nfa_id) REFERENCES NFAs(id) ON DELETE CASCADE,
            FOREIGN KEY (from_state_id) REFERENCES NFA_States(id),
            FOREIGN KEY (to_state_id)   REFERENCES NFA_States(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS NFA_InputTests (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            nfa_id        INT,
            input_string  TEXT,
            is_accepted   BOOLEAN,
            tested_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nfa_id) REFERENCES NFAs(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS NFA_Conversions (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            source_nfa_id     INT,
            result_dfa_id     INT,
            conversion_type   VARCHAR(64),
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_nfa_id) REFERENCES NFAs(id),
            FOREIGN KEY (result_dfa_id) REFERENCES NFAs(id)
        )
        """,
    ]

    conn = get_connection()
    cur = conn.cursor()
    for stmt in ddl:
        cur.execute(stmt)
    cur.close()
    conn.close()


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  INSERT helpers                                                         │
# ╰──────────────────────────────────────────────────────────────────────────╯
def create_automaton(name: str,
                     kind: str = "NFA",
                     public_id: Optional[str] = None) -> tuple[int, str]:
    public_id = public_id or make_public_id(name)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO NFAs (public_id, name, type) VALUES (%s, %s, %s)",
        (public_id, name, kind),
    )
    pk = cur.lastrowid
    cur.close()
    conn.close()
    return pk, public_id


def add_state(nfa_id: int, name: str,
              is_start: bool, is_accept: bool) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO NFA_States (nfa_id, state, is_start, is_final) "
        "VALUES (%s, %s, %s, %s)",
        (nfa_id, name, is_start, is_accept),
    )
    pk = cur.lastrowid
    cur.close()
    conn.close()
    return pk


def add_transition(nfa_id: int, src_id: int,
                   sym: str, tgt_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO NFA_Transitions "
        "(nfa_id, from_state_id, symbol, to_state_id) "
        "VALUES (%s, %s, %s, %s)",
        (nfa_id, src_id, sym, tgt_id),
    )
    cur.close()
    conn.close()


def save_input_test(nfa_id: int, s: str, ok: bool) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO NFA_InputTests (nfa_id, input_string, is_accepted) "
        "VALUES (%s, %s, %s)",
        (nfa_id, s, ok),
    )
    cur.close()
    conn.close()


def save_conversion(src_pk: int, dst_pk: int, ctype: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO NFA_Conversions "
        "(source_nfa_id, result_dfa_id, conversion_type) "
        "VALUES (%s, %s, %s)",
        (src_pk, dst_pk, ctype),
    )
    cur.close()
    conn.close()


# ╭──────────────────────────────────────────────────────────────────────────╮
# │  High‑level save/load helpers                                           │
# ╰──────────────────────────────────────────────────────────────────────────╯
def save_automaton_to_db(fa: FiniteAutomaton) -> tuple[int, str]:
    pk, pubid = create_automaton(
        fa.name,
        "DFA" if fa.is_dfa else "NFA",
        fa.id,
    )
    fa.id = pubid

    # insert states
    id_map = {
        s: add_state(pk, s, s == fa.start_state, s in fa.accept_states)
        for s in fa.states
    }

    # insert transitions
    for src, mp in fa.transitions.items():
        for sym, dsts in mp.items():
            dst_iter = dsts if isinstance(dsts, (list, set)) else [dsts]
            for dst in dst_iter:
                add_transition(pk, id_map[src], sym, id_map[dst])

    return pk, pubid


def load_automaton_by_id(public_id: str) -> Optional[FiniteAutomaton]:
    """Return FiniteAutomaton object or None if not found."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # header
    cur.execute(
        "SELECT id, name, type FROM NFAs WHERE public_id=%s",
        (public_id,),
    )
    head = cur.fetchone()
    if not head:
        cur.close()
        conn.close()
        return None

    nfa_pk = head["id"]
    name = head["name"]
    is_dfa = head["type"] == "DFA"

    # states
    cur.execute(
        "SELECT * FROM NFA_States WHERE nfa_id=%s",
        (nfa_pk,),
    )
    states, accept, start, id_to_name = set(), set(), None, {}
    for row in cur.fetchall():
        sid = row["id"]
        st_name = row["state"]
        id_to_name[sid] = st_name
        states.add(st_name)
        if row["is_start"]:
            start = st_name
        if row["is_final"]:
            accept.add(st_name)

    # transitions
    cur.execute(
        "SELECT * FROM NFA_Transitions WHERE nfa_id=%s",
        (nfa_pk,),
    )
    transitions = {s: {} for s in states}
    for row in cur.fetchall():
        src = id_to_name[row["from_state_id"]]
        tgt = id_to_name[row["to_state_id"]]
        sym = row["symbol"] or "ε"
        transitions[src].setdefault(sym, set()).add(tgt)

    # collapse sets to single values for DFA
    if is_dfa:
        for src, mp in transitions.items():
            for sym in mp:
                vals = list(mp[sym])
                transitions[src][sym] = vals[0] if len(vals) == 1 else vals

    alphabet = {sym for mp in transitions.values() for sym in mp if sym != "ε"}

    cur.close()
    conn.close()

    fa = FiniteAutomaton(
        id=public_id,
        name=name,
        states=states,
        alphabet=alphabet,
        transitions=transitions,
        start_state=start,
        accept_states=accept,
        is_dfa=is_dfa,
    )
    fa.db_id = nfa_pk
    return fa
