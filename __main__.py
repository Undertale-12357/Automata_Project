import mysql.connector
from fa_database import init_all_tables, load_automaton_by_id, save_automaton_to_db, save_input_test, save_conversion
from fa_logic import FiniteAutomaton
from gui import AutomatonGUI
from ttkbootstrap.dialogs import Messagebox
from automaton_manager import get_connection
import ttkbootstrap as tb
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def manage_automaton(action: str, **kwargs) -> dict:
    """
    Interface function for automaton operations.
    Actions: create, load, simulate, check_type, convert, minimize, list, check_id.
    """
    logger.debug(f"Executing action: {action} with kwargs: {kwargs}")
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
                logger.error("Missing required fields")
                return {"error": "All fields are required."}
            if start_state not in states:
                logger.error(f"Start state '{start_state}' not in states: {states}")
                return {"error": f"Start state '{start_state}' not in states."}
            if not set(accept_states).issubset(states):
                logger.error(f"Accept states {accept_states} not subset of states: {states}")
                return {"error": "Accept states must be a subset of states."}
            for state in transitions:
                if state not in states:
                    logger.error(f"Invalid state '{state}' in transitions")
                    return {"error": f"Invalid state '{state}' in transitions."}
                for sym in transitions[state]:
                    if sym != "ε" and sym not in alphabet:
                        logger.error(f"Invalid symbol '{sym}' in transitions for state {state}")
                        return {"error": f"Invalid symbol '{sym}' in transitions."}
                    targets = transitions[state][sym] if isinstance(transitions[state][sym], list) else [transitions[state][sym]]
                    for target in targets:
                        if target not in states:
                            logger.error(f"Invalid target state '{target}' in transitions for {state}, {sym}")
                            return {"error": f"Invalid target state '{target}' in transitions."}
            automaton = FiniteAutomaton(id, name, states, alphabet, transitions, start_state, accept_states, is_dfa)
            db_id = save_automaton_to_db(automaton)
            logger.debug(f"Automaton saved with DB ID: {db_id}")
            automaton.db_id = db_id  # Store database ID separately
            return {"automaton": automaton}

        elif action == "load":
            id = kwargs.get("id")
            automaton = load_automaton_by_id(id)
            if not automaton:
                logger.error(f"Automaton with ID '{id}' not found")
                return {"error": f"Automaton with ID '{id}' not found."}
            logger.debug(f"Loaded automaton: {automaton.id}")
            return {"automaton": automaton}

        elif action == "simulate":
            automaton = kwargs.get("automaton")
            input_string = kwargs.get("input_string")
            if not automaton or input_string is None:
                logger.error("Automaton or input string missing")
                return {"error": "Automaton and input string required."}
            result = automaton.simulate(input_string)
            save_input_test(int(automaton.id), input_string, result)
            logger.debug(f"Simulation result for '{input_string}': {result}")
            return {"result": result}

        elif action == "check_type":
            automaton = kwargs.get("automaton")
            if not automaton:
                logger.error("No automaton provided for check_type")
                return {"error": "No automaton provided."}
            is_dfa = automaton.is_dfa_check()
            logger.debug(f"Automaton type: {'DFA' if is_dfa else 'NFA'}")
            return {"type": is_dfa}

        elif action == "convert":
            automaton = kwargs.get("automaton")
            if not automaton:
                logger.error("No automaton provided for conversion")
                return {"error": "No automaton provided."}
            if automaton.is_dfa:
                logger.error("Cannot convert: Automaton is already a DFA")
                return {"error": "Automaton is already a DFA."}
            dfa = automaton.convert_to_dfa()
            dfa_id = save_automaton_to_db(dfa)
            save_conversion(int(automaton.id), dfa_id, "NFA_TO_DFA")
            dfa.id = f"{automaton.id}_dfa"
            logger.debug(f"Converted to DFA with ID: {dfa.id}")
            return {"automaton": dfa}

        elif action == "minimize":
            automaton = kwargs.get("automaton")
            if not automaton:
                logger.error("No automaton provided for minimization")
                return {"error": "No automaton provided."}
            if not automaton.is_dfa:
                logger.error("Minimization requires a DFA")
                return {"error": "Minimization requires a DFA."}
            minimized = automaton.minimize()
            minimized_id = save_automaton_to_db(minimized)
            save_conversion(int(automaton.id), minimized_id, "DFA_MINIMIZATION")
            minimized.id = f"{automaton.id}_min"
            logger.debug(f"Minimized DFA with ID: {minimized.id}")
            return {"automaton": minimized}

        elif action == "list":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM NFAs")
            automata = [load_automaton_by_id(row[0]) for row in cursor.fetchall()]
            conn.close()
            logger.debug(f"Listed {len(automata)} automata")
            return {"automata": [fa for fa in automata if fa]}

        elif action == "check_id":
            id = kwargs.get("id")
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM NFAs WHERE user_id = %s", (id,))
            exists = cursor.fetchone() is not None
            conn.close()
            if exists:
                logger.error(f"ID '{id}' already exists")
                return {"error": f"ID '{id}' already exists."}
            logger.debug(f"ID '{id}' is available")
            return {"success": True}

        else:
            logger.error(f"Invalid action: {action}")
            return {"error": "Invalid action."}
    except mysql.connector.Error as e:
        logger.error(f"Database error: {e}")
        return {"error": f"Database error: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Error: {e}"}

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="@@Arifin012",
            database="Automata",
            auth_plugin="mysql_native_password"
        )
        logger.debug("Database connection established")
        return conn
    except mysql.connector.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

if __name__ == "__main__":
    try:
        logger.info("Initializing database tables")
        init_all_tables()
        logger.info("Starting GUI")
        root = tb.Window(themename="superhero")
        app = AutomatonGUI(root)
        root.mainloop()
    except mysql.connector.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        Messagebox.show_error(f"Failed to initialize database: {e}", title="Error")
        exit(1)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        Messagebox.show_error(f"Failed to start application: {e}", title="Error")
        exit(1)