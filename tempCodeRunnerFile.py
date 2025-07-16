import mysql.connector
from fa_database import init_all_tables, load_automaton_by_id, save_automaton_to_db, save_input_test, save_conversion
from fa_logic import FiniteAutomaton
from gui import AutomatonGUI
from ttkbootstrap.dialogs import Messagebox
from automaton_manager import get_connection
import ttkbootstrap as tb

def manage_automaton(action: str, **kwargs) -> dict:
    """
    Interface function for automaton operations.
    Actions: create, load, simulate, check_type, convert, minimize, list, check_id.
    """
    try:
        if action == "create":
            id = kwargs.get("id")
            name = kwargs.get("name")
            states = kwargs.get("states")
            alphabet = kwargs.get("alphabet")
            transitions = kwargs.get("transitions")
            start_state = kwargs.get("start_state")
            accept_states = kwargs.get("accept_states")
            is_dfa = kwargs.get("is_dfa")
            if not all([id, name, states, alphabet, transitions, start_state, accept_states]):
                return {"error": "All fields are required."}
            if start_state not in states:
                return {"error": f"Start state '{start_state}' not in states."}
            if not set(accept_states).issubset(states):
                return {"error": "Accept states must be a subset of states."}
            for state in transitions:
                if state not in states:
                    return {"error": f"Invalid state '{state}' in transitions."}
                for sym in transitions[state]:
                    if sym != "ε" and sym not in alphabet:
                        return {"error": f"Invalid symbol '{sym}' in transitions."}
                    targets = transitions[state][sym] if isinstance(transitions[state][sym], list) else [transitions[state][sym]]
                    for target in targets:
                        if target not in states:
                            return {"error": f"Invalid target state '{target}' in transitions."}
            automaton = FiniteAutomaton(id, name, states, alphabet, transitions, start_state, accept_states, is_dfa)
            automaton_id = save_automaton_to_db(automaton)
            automaton.id = id  # Keep user_id
            return {"automaton": automaton}

        elif action == "load":
            id = kwargs.get("id")
            automaton = load_automaton_by_id(id)
            if not automaton:
                return {"error": f"Automaton with ID '{id}' not found."}
            return {"automaton": automaton}

        elif action == "simulate":
            automaton = kwargs.get("automaton")
            input_string = kwargs.get("input_string")
            if not automaton or input_string is None:
                return {"error": "Automaton and input string required."}
            result = automaton.simulate(input_string)
            save_input_test(int(automaton.id), input_string, result)
            return {"result": result}

        elif action == "check_type":
            automaton = kwargs.get("automaton")
            if not automaton:
                return {"error": "No automaton provided."}
            return {"type": automaton.is_dfa_check()}

        elif action == "convert":
            automaton = kwargs.get("automaton")
            if not automaton:
                return {"error": "No automaton provided."}
            if automaton.is_dfa:
                return {"error": "Automaton is already a DFA."}
            dfa = automaton.convert_to_dfa()
            dfa_id = save_automaton_to_db(dfa)
            save_conversion(int(automaton.id), dfa_id, "NFA_TO_DFA")
            dfa.id = f"{automaton.id}_dfa"
            return {"automaton": dfa}

        elif action == "minimize":
            automaton = kwargs.get("automaton")
            if not automaton:
                return {"error": "No automaton provided."}
            if not automaton.is_dfa:
                return {"error": "Minimization requires a DFA."}
            minimized = automaton.minimize()
            minimized_id = save_automaton_to_db(minimized)
            save_conversion(int(automaton.id), minimized_id, "DFA_MINIMIZATION")
            minimized.id = f"{automaton.id}_min"
            return {"automaton": minimized}

        elif action == "list":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM NFAs")
            automata = [load_automaton_by_id(row[0]) for row in cursor.fetchall()]
            conn.close()
            return {"automata": [fa for fa in automata if fa]}

        elif action == "check_id":
            id = kwargs.get("id")
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM NFAs WHERE user_id = %s", (id,))
            exists = cursor.fetchone() is not None
            conn.close()
            if exists:
                return {"error": f"ID '{id}' already exists."}
            return {"success": True}

        else:
            return {"error": "Invalid action."}
    except mysql.connector.Error as e:
        return {"error": f"Database error: {e}"}
    except Exception as e:
        return {"error": f"Error: {e}"}

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="@@Arifin012",
        database="Automata",
        auth_plugin="mysql_native_password"
    )

if __name__ == "__main__":
    try:
        init_all_tables()
    except Exception as e:
        Messagebox.show_error(f"Failed to initialize database: {e}", title="Error")
        exit(1)
    root = tb.Window()
    app = AutomatonGUI(root)
    root.mainloop()