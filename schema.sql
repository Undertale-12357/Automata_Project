CREATE TABLE IF NOT EXISTS NFAs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    public_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type ENUM('NFA', 'DFA') NOT NULL
);

CREATE TABLE IF NOT EXISTS NFA_States (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nfa_id INT,
    state VARCHAR(50) NOT NULL,
    is_start BOOLEAN DEFAULT FALSE,
    is_final BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (nfa_id) REFERENCES NFAs(id)
);

CREATE TABLE IF NOT EXISTS NFA_Transitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nfa_id INT,
    from_state_id INT,
    symbol VARCHAR(10),
    to_state_id INT,
    FOREIGN KEY (nfa_id) REFERENCES NFAs(id),
    FOREIGN KEY (from_state_id) REFERENCES NFA_States(id),
    FOREIGN KEY (to_state_id) REFERENCES NFA_States(id)
);

CREATE TABLE IF NOT EXISTS NFA_InputTests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nfa_id INT,
    input_string VARCHAR(255) NOT NULL,
    is_accepted BOOLEAN NOT NULL,
    FOREIGN KEY (nfa_id) REFERENCES NFAs(id)
);

CREATE TABLE IF NOT EXISTS NFA_Conversions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_nfa_id INT,
    result_dfa_id INT,
    conversion_type VARCHAR(50) NOT NULL,
    FOREIGN KEY (source_nfa_id) REFERENCES NFAs(id),
    FOREIGN KEY (result_dfa_id) REFERENCES NFAs(id)
);