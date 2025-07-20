CREATE TABLE IF NOT EXISTS Automata (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('NFA', 'DFA'))
);

CREATE TABLE IF NOT EXISTS Automaton_States (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automaton_id TEXT,
    state TEXT NOT NULL,
    is_start INTEGER DEFAULT 0,
    is_final INTEGER DEFAULT 0,
    FOREIGN KEY (automaton_id) REFERENCES Automata(id)
);

CREATE TABLE IF NOT EXISTS Automaton_Transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automaton_id TEXT,
    from_state_id INTEGER,
    symbol TEXT,
    to_state_id INTEGER,
    FOREIGN KEY (automaton_id) REFERENCES Automata(id),
    FOREIGN KEY (from_state_id) REFERENCES Automaton_States(id),
    FOREIGN KEY (to_state_id) REFERENCES Automaton_States(id)
);

CREATE TABLE IF NOT EXISTS Automaton_Alphabet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automaton_id TEXT,
    symbol TEXT NOT NULL,
    FOREIGN KEY (automaton_id) REFERENCES Automata(id)
);

CREATE TABLE IF NOT EXISTS Automaton_InputTests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    automaton_id TEXT,
    input_string TEXT NOT NULL,
    is_accepted INTEGER NOT NULL,
    FOREIGN KEY (automaton_id) REFERENCES Automata(id)
);

CREATE TABLE IF NOT EXISTS Automaton_Conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_automaton_id TEXT,
    result_automaton_id TEXT,
    conversion_type TEXT NOT NULL CHECK(conversion_type IN ('NFA_TO_DFA', 'DFA_MINIMIZATION')),
    FOREIGN KEY (source_automaton_id) REFERENCES Automata(id),
    FOREIGN KEY (result_automaton_id) REFERENCES Automata(id)