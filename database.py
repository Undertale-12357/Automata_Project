import sqlite3
import json
import logging
from fa import FiniteAutomaton

logging.basicConfig(filename='fa_tool.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class FADatabase:
    def __init__(self):
        self.db_path = "fa_tool.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        logging.info("Database connection established")

    def init_db(self):
        try:
            cursor = self.conn.cursor()
            # Check if Automata table has the correct schema
            cursor.execute("PRAGMA table_info(Automata)")
            columns = [info[1] for info in cursor.fetchall()]
            expected_columns = ['id', 'name', 'states', 'alphabet', 'transitions', 'start_state', 'final_states', 'fa_type']
            if set(columns) != set(expected_columns):
                logging.info("Automata table schema is outdated, dropping and recreating")
                cursor.execute("DROP TABLE IF EXISTS Automata")
                cursor.execute("DROP TABLE IF EXISTS Transitions")
                cursor.execute("DROP TABLE IF EXISTS Input_Tests")
                cursor.execute("DROP TABLE IF EXISTS Automaton_Conversions")
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Automata (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    states TEXT NOT NULL,
                    alphabet TEXT NOT NULL,
                    transitions TEXT NOT NULL,
                    start_state TEXT NOT NULL,
                    final_states TEXT NOT NULL,
                    fa_type TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Transitions (
                    fa_id TEXT,
                    state TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    target_state TEXT NOT NULL,
                    FOREIGN KEY (fa_id) REFERENCES Automata(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Input_Tests (
                    fa_id TEXT,
                    input_string TEXT NOT NULL,
                    accepted BOOLEAN NOT NULL,
                    test_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (fa_id) REFERENCES Automata(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Automaton_Conversions (
                    source_id TEXT,
                    result_id TEXT,
                    conversion_type TEXT NOT NULL,
                    conversion_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES Automata(id) ON DELETE CASCADE,
                    FOREIGN KEY (result_id) REFERENCES Automata(id) ON DELETE CASCADE
                )
            ''')
            self.conn.commit()
            logging.info("Database schema initialized successfully")
            
            # Verify schema
            cursor.execute("PRAGMA table_info(Automata)")
            columns = [info[1] for info in cursor.fetchall()]
            if set(columns) != set(expected_columns):
                logging.error(f"Schema verification failed: Expected columns {expected_columns}, got {columns}")
                raise sqlite3.DatabaseError("Failed to create Automata table with correct schema")
            logging.info(f"Verified Automata table columns: {columns}")
        except sqlite3.Error as e:
            logging.error(f"Failed to initialize database: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"General error initializing database: {str(e)}")
            raise

    def verify_schema(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA foreign_key_list(Automaton_Conversions)")
            fk_info = cursor.fetchall()
            logging.info(f"Foreign key in Automaton_Conversions: {fk_info}")
            cursor.execute("PRAGMA foreign_key_check")
            violations = cursor.fetchall()
            if violations:
                logging.warning(f"Foreign key violations detected: {violations}")
                for table, rowid, parent, fkid in violations:
                    cursor.execute(f"DELETE FROM {table} WHERE rowid = ?", (rowid,))
                self.conn.commit()
                logging.info("Foreign key violations resolved by deleting offending rows")
        except sqlite3.Error as e:
            logging.error(f"Schema verification failed: {str(e)}")
            raise

    def save_fa(self, fa):
        logging.info(f"Attempting to save FA with ID {fa.id}")
        try:
            cursor = self.conn.cursor()
            # Ensure transitions are in the correct format
            transitions_json = json.dumps(fa.transitions)
            cursor.execute('''
                INSERT OR REPLACE INTO Automata (id, name, states, alphabet, transitions, start_state, final_states, fa_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fa.id,
                fa.name,
                json.dumps(fa.states),
                json.dumps(fa.alphabet),
                transitions_json,
                fa.start_state,
                json.dumps(fa.final_states),
                fa.fa_type
            ))
            logging.info(f"Inserted FA {fa.id} into Automata table")

            # Delete existing transitions for this FA to avoid duplicates
            cursor.execute("DELETE FROM Transitions WHERE fa_id = ?", (fa.id,))
            logging.info(f"Deleted existing transitions for FA {fa.id}")

            # Insert transitions
            for state, trans in fa.transitions.items():
                for symbol, targets in trans.items():
                    if isinstance(targets, str):
                        targets = [targets]
                    for target in targets:
                        cursor.execute('''
                            INSERT INTO Transitions (fa_id, state, symbol, target_state)
                            VALUES (?, ?, ?, ?)
                        ''', (fa.id, state, symbol, target))
            logging.info(f"Inserted transitions for FA {fa.id}")

            self.conn.commit()
            logging.info(f"FA {fa.id} saved successfully")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Database error saving FA {fa.id}: {str(e)}")
            raise
        except Exception as e:
            self.conn.rollback()
            logging.error(f"General error saving FA {fa.id}: {str(e)}")
            raise

    def load_all_fas(self):
        logging.info("Loading all FAs from database")
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name, states, alphabet, transitions, start_state, final_states, fa_type FROM Automata")
            fas = []
            for row in cursor.fetchall():
                id, name, states_json, alphabet_json, transitions_json, start_state, final_states_json, fa_type = row
                try:
                    states = json.loads(states_json)
                    alphabet = json.loads(alphabet_json)
                    transitions = json.loads(transitions_json)
                    final_states = json.loads(final_states_json)
                    fa = FiniteAutomaton(id, name, states, alphabet, transitions, start_state, final_states)
                    fa.fa_type = fa_type
                    fas.append(fa)
                    logging.info(f"Loaded FA {id} successfully")
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON for FA {id}: {str(e)}")
                    continue
            logging.info(f"Loaded {len(fas)} FAs from database")
            return fas
        except sqlite3.Error as e:
            logging.error(f"Database error loading FAs: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"General error loading FAs: {str(e)}")
            raise

    def delete_fa(self, fa_id):
        logging.info(f"Attempting to delete FA {fa_id}")
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Automata WHERE id = ?", (fa_id,))
            if cursor.rowcount == 0:
                logging.warning(f"No FA found with ID {fa_id} for deletion")
                raise ValueError(f"No FA found with ID {fa_id}")
            self.conn.commit()
            logging.info(f"FA {fa_id} deleted successfully from Automata table")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Database error deleting FA {fa_id}: {str(e)}")
            raise
        except Exception as e:
            self.conn.rollback()
            logging.error(f"General error deleting FA {fa_id}: {str(e)}")
            raise

    def save_conversion(self, source_id, result_id, conversion_type):
        logging.info(f"Saving conversion: source_id={source_id}, result_id={result_id}, type={conversion_type}")
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO Automaton_Conversions (source_id, result_id, conversion_type)
                VALUES (?, ?, ?)
            ''', (source_id, result_id, conversion_type))
            self.conn.commit()
            logging.info(f"Conversion saved: {source_id} -> {result_id} ({conversion_type})")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Database error saving conversion {source_id} -> {result_id}: {str(e)}")
            raise
        except Exception as e:
            self.conn.rollback()
            logging.error(f"General error saving conversion {source_id} -> {result_id}: {str(e)}")
            raise

    def generate_next_fa_id(self):
        logging.info("Generating next FA ID")
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM Automata ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                last_id = row[0]
                if last_id.startswith("FA"):
                    num = int(last_id[2:]) + 1
                    new_id = f"FA{num:04d}"
                else:
                    num = int(last_id) + 1
                    new_id = f"{num:04d}"
            else:
                new_id = "0001"
            logging.info(f"Generated new FA ID: {new_id}")
            return new_id
        except sqlite3.Error as e:
            logging.error(f"Database error generating next FA ID: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"General error generating next FA ID: {str(e)}")
            raise

    def save_input_test(self, fa_id, input_string, accepted):
        logging.info(f"Saving input test for FA {fa_id}: input={input_string}, accepted={accepted}")
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO Input_Tests (fa_id, input_string, accepted)
                VALUES (?, ?, ?)
            ''', (fa_id, input_string, accepted))
            self.conn.commit()
            logging.info(f"Input test saved for FA {fa_id}")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Database error saving input test for FA {fa_id}: {str(e)}")
            raise
        except Exception as e:
            self.conn.rollback()
            logging.error(f"General error saving input test for FA {fa_id}: {str(e)}")
            raise

    def __del__(self):
        logging.info("Closing database connection")
        self.conn.close()
