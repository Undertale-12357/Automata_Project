# automaton_manager.py  ── single façade the GUI talks to
from fa_database import (
    load_automaton_by_id,
    save_automaton_to_db,
    save_input_test,
    save_conversion,
)
from fa_logic import FiniteAutomaton
from db import get_connection


def manage_automaton(action: str, **kwargs) -> dict:
    conn = None
    try:
        if action == "create":
            fa = FiniteAutomaton(
                id=None,
                name=kwargs["name"],
                states=set(kwargs["states"]),
                alphabet=set(kwargs["alphabet"]),
                transitions=kwargs["transitions"],
                start_state=kwargs["start_state"],
                accept_states=set(kwargs["accept_states"]),
                is_dfa=kwargs["is_dfa"],
            )
            _, pubid = save_automaton_to_db(fa)
            fa.id = pubid
            return {"automaton": fa}

        if action == "list":
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, public_id FROM NFAs ORDER BY id DESC")
            automata = []
            for pk, pubid in cur.fetchall():
                fa = load_automaton_by_id(pubid)
                if fa:
                    fa.db_id = pk
                    automata.append(fa)
            return {"automata": automata}

        if action == "load":
            pubid = kwargs["id"]
            fa = load_automaton_by_id(pubid)
            return {"automaton": fa} if fa else {"error": f"Not found: {pubid}"}

        if action == "simulate":
            fa, s = kwargs["automaton"], kwargs["input_string"]
            result = fa.simulate(s)
            save_input_test(int(fa.db_id), s, result)
            return {"result": result}

        if action == "check_type":
            return {"type": kwargs["automaton"].is_dfa_check()}

        if action == "convert":
            fa = kwargs["automaton"]
            dfa = fa.convert_to_dfa()
            _, pubid = save_automaton_to_db(dfa)
            save_conversion(int(fa.db_id), int(dfa.db_id), "NFA_TO_DFA")
            dfa.id = pubid
            return {"automaton": dfa}

        if action == "minimize":
            fa = kwargs["automaton"]
            minfa = fa.minimize()
            _, pubid = save_automaton_to_db(minfa)
            save_conversion(int(fa.db_id), int(minfa.db_id), "DFA_MINIMIZATION")
            minfa.id = pubid
            return {"automaton": minfa}

        return {"error": "Invalid action."}

    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()
