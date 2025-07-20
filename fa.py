import logging
from copy import deepcopy
from itertools import product

logging.basicConfig(filename='fa_tool.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class FiniteAutomaton:
    def __init__(self, id, name, states, alphabet, transitions, start_state, final_states):
        self.id = id
        self.name = name
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.final_states = final_states
        self.fa_type = "NFA" if any(isinstance(t, list) for s in transitions.values() for t in s.values()) else "DFA"
        logging.info(f"Initialized FA {self.id} as {self.fa_type}")

    def is_dfa(self):
        logging.info(f"Checking if FA {self.id} is DFA")
        if 'ε' in self.alphabet:
            logging.info(f"FA {self.id} is NFA due to epsilon transitions")
            return False
        for state in self.transitions:
            for symbol in self.alphabet:
                targets = self.transitions.get(state, {}).get(symbol, [])
                if isinstance(targets, list) and len(targets) > 1:
                    logging.info(f"FA {self.id} is NFA due to multiple transitions: {state} --{symbol}--> {targets}")
                    return False
                if isinstance(targets, list) and len(targets) == 0:
                    logging.info(f"FA {self.id} is NFA due to undefined transition: {state} --{symbol}--> []")
                    return False
        logging.info(f"FA {self.id} is DFA")
        return True

    def simulate(self, input_string):
        logging.info(f"Simulating input '{input_string}' on FA {self.id}")
        current_states = {self.start_state}
        if 'ε' in self.alphabet:
            current_states = self.epsilon_closure(current_states)
        for symbol in input_string:
            if symbol not in self.alphabet:
                logging.error(f"Invalid symbol '{symbol}' in input for FA {self.id}")
                raise ValueError(f"Invalid symbol '{symbol}'")
            next_states = set()
            for state in current_states:
                targets = self.transitions.get(state, {}).get(symbol, [])
                if isinstance(targets, str):
                    targets = [targets]
                next_states.update(targets)
            current_states = next_states
            if 'ε' in self.alphabet:
                current_states = self.epsilon_closure(current_states)
        result = any(state in self.final_states for state in current_states)
        logging.info(f"Simulation result for FA {self.id}: {'ACCEPTED' if result else 'REJECTED'}")
        return result

    def epsilon_closure(self, states):
        logging.info(f"Computing epsilon closure for states {states} in FA {self.id}")
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for target in self.transitions.get(state, {}).get('ε', []):
                if target not in closure:
                    closure.add(target)
                    stack.append(target)
        logging.info(f"Epsilon closure for {states}: {closure}")
        return closure

    def to_dfa(self, id_prefix="FA", id_counter=1, db=None):
        logging.info(f"Converting NFA {self.id} to DFA")
        if self.is_dfa():
            logging.info(f"FA {self.id} is already a DFA, returning copy")
            dfa = deepcopy(self)
            dfa.id = f"{id_prefix}{id_counter:04d}"
            dfa.name = f"{self.name}_DFA"
            dfa.fa_type = "DFA"
            return dfa

        # Subset construction
        dfa_states = []
        dfa_transitions = {}
        dfa_final_states = []
        state_map = {}  # Maps frozenset of NFA states to DFA state name
        queue = [frozenset(self.epsilon_closure({self.start_state}))]
        state_map[queue[0]] = "s0"
        dfa_states.append("s0")
        trap_state = "TRAP"
        alphabet_no_epsilon = [sym for sym in self.alphabet if sym != 'ε']

        while queue:
            current_nfa_states = queue.pop(0)
            current_dfa_state = state_map[current_nfa_states]
            dfa_transitions[current_dfa_state] = {}

            if any(s in self.final_states for s in current_nfa_states):
                dfa_final_states.append(current_dfa_state)

            for symbol in alphabet_no_epsilon:
                next_nfa_states = set()
                for state in current_nfa_states:
                    targets = self.transitions.get(state, {}).get(symbol, [])
                    if isinstance(targets, str):
                        targets = [targets]
                    next_nfa_states.update(self.epsilon_closure(set(targets)))
                
                if not next_nfa_states:
                    dfa_transitions[current_dfa_state][symbol] = trap_state
                    if trap_state not in dfa_states:
                        dfa_states.append(trap_state)
                        state_map[frozenset()] = trap_state
                else:
                    next_nfa_states_frozen = frozenset(next_nfa_states)
                    if next_nfa_states_frozen not in state_map:
                        new_state = f"s{len(dfa_states)}"
                        dfa_states.append(new_state)
                        state_map[next_nfa_states_frozen] = new_state
                        queue.append(next_nfa_states_frozen)
                    dfa_transitions[current_dfa_state][symbol] = state_map[next_nfa_states_frozen]

        if trap_state in dfa_states:
            dfa_transitions[trap_state] = {sym: trap_state for sym in alphabet_no_epsilon}

        dfa = FiniteAutomaton(
            id=f"{id_prefix}{id_counter:04d}",
            name=f"{self.name}_DFA",
            states=dfa_states,
            alphabet=alphabet_no_epsilon,
            transitions=dfa_transitions,
            start_state="s0",
            final_states=dfa_final_states
        )
        dfa.fa_type = "DFA"
        logging.info(f"Created DFA {dfa.id} with states {dfa_states}")
        if not dfa.is_dfa():
            logging.error(f"Conversion failed: FA {dfa.id} is not a DFA")
            raise ValueError(f"Conversion produced invalid DFA {dfa.id}")
        return dfa

    def minimize(self, id_prefix="FA", id_counter=1, db=None):
        logging.info(f"Minimizing DFA {self.id}")
        if not self.is_dfa():
            logging.error(f"FA {self.id} is not a DFA, cannot minimize")
            raise ValueError(f"Cannot minimize NFA {self.id}")

        reachable = self.get_reachable_states()
        if not reachable:
            logging.error(f"No reachable states in DFA {self.id}")
            raise ValueError(f"No reachable states in DFA {self.id}")

        partitions = self.partition_states(reachable)
        new_states = [f"s{i}" for i in range(len(partitions))]
        state_map = {state: new_states[i] for i, p in enumerate(partitions) for state in p}
        new_transitions = {}
        for i, partition in enumerate(partitions):
            rep_state = next(iter(partition))
            new_transitions[new_states[i]] = {
                sym: state_map[self.transitions[rep_state][sym]]
                for sym in self.alphabet
                if self.transitions.get(rep_state, {}).get(sym)
            }
        new_final_states = [state_map[state] for state in self.final_states if state in state_map]
        new_start_state = state_map.get(self.start_state, new_states[0])

        minimized = FiniteAutomaton(
            id=f"{id_prefix}{id_counter:04d}",
            name=f"{self.name}_Minimized",
            states=new_states,
            alphabet=self.alphabet,
            transitions=new_transitions,
            start_state=new_start_state,
            final_states=new_final_states
        )
        minimized.fa_type = "DFA"
        logging.info(f"Created minimized DFA {minimized.id} with {len(new_states)} states")
        return minimized

    def get_reachable_states(self):
        logging.info(f"Computing reachable states for FA {self.id}")
        reachable = {self.start_state}
        stack = [self.start_state]
        while stack:
            state = stack.pop()
            for symbol in self.alphabet:
                targets = self.transitions.get(state, {}).get(symbol, [])
                if isinstance(targets, str):
                    targets = [targets]
                for target in targets:
                    if target not in reachable:
                        reachable.add(target)
                        stack.append(target)
        logging.info(f"Reachable states for FA {self.id}: {reachable}")
        return reachable

    def partition_states(self, states):
        logging.info(f"Partitioning states for DFA {self.id}")
        non_final = states - set(self.final_states)
        final = set(self.final_states) & states
        partitions = [non_final, final]
        partitions = [p for p in partitions if p]
        while True:
            new_partitions = []
            changed = False
            for p in partitions:
                for symbol in self.alphabet:
                    groups = {}
                    for state in p:
                        target = self.transitions.get(state, {}).get(symbol, 'TRAP')
                        target_group = next((i for i, part in enumerate(partitions) if target in part), -1)
                        if target_group not in groups:
                            groups[target_group] = set()
                        groups[target_group].add(state)
                    if len(groups) > 1:
                        changed = True
                        new_partitions.extend(groups.values())
                    else:
                        new_partitions.append(p)
                    break
                if len(groups) <= 1:
                    new_partitions.append(p)
            partitions = [p for p in new_partitions if p]
            if not changed:
                break
        logging.info(f"Partitions for DFA {self.id}: {partitions}")
        return partitions
