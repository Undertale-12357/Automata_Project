from typing import Set, Dict, List
from collections import defaultdict, deque

class FiniteAutomaton:
    def __init__(self, id: str, name: str, states: Set[str], alphabet: Set[str], transitions: Dict[str, Dict[str, str | List[str]]], start_state: str, accept_states: Set[str], is_dfa: bool = True):
        self.id = id
        self.name = name
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = set(accept_states)
        self.is_dfa = is_dfa

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "states": list(self.states),
            "alphabet": list(self.alphabet),
            "transitions": self.transitions,
            "start_state": self.start_state,
            "accept_states": list(self.accept_states),
            "is_dfa": self.is_dfa
        }

    def is_dfa_check(self):
        for state in self.transitions:
            for symbol in self.transitions[state]:
                if not isinstance(self.transitions[state][symbol], str):
                    return False
        return True

    def simulate(self, input_string: str) -> bool:
        if self.is_dfa:
            state = self.start_state
            for sym in input_string:
                if sym in self.transitions.get(state, {}):
                    state = self.transitions[state][sym]
                else:
                    return False
            return state in self.accept_states
        else:
            current_states = {self.start_state}
            for sym in input_string:
                next_states = set()
                for state in current_states:
                    next_states.update(self.transitions.get(state, {}).get(sym, []))
                current_states = next_states
                if not current_states:
                    return False
            return bool(current_states & self.accept_states)

    def convert_to_dfa(self):
        if self.is_dfa:
            return self
        new_states = set()
        new_trans = {}
        queue = deque()
        start = frozenset([self.start_state])
        queue.append(start)
        visited = set()

        while queue:
            curr = queue.popleft()
            curr_name = ','.join(sorted(curr))
            if curr_name in visited:
                continue
            visited.add(curr_name)
            new_states.add(curr_name)
            new_trans[curr_name] = {}
            for sym in self.alphabet:
                dest = set()
                for sub in curr:
                    dest.update(self.transitions.get(sub, {}).get(sym, []))
                if dest:
                    dest_name = ','.join(sorted(dest))
                    new_trans[curr_name][sym] = dest_name
                    if dest_name not in visited:
                        queue.append(frozenset(dest))
            if not new_trans[curr_name]:
                new_trans.pop(curr_name)

        new_accepts = {s for s in new_states if set(s.split(',')) & self.accept_states}
        return FiniteAutomaton(
            id=f"{self.id}_dfa",
            name=f"{self.name}_DFA",
            states=new_states,
            alphabet=self.alphabet,
            transitions=new_trans,
            start_state=','.join(sorted(start)),
            accept_states=new_accepts,
            is_dfa=True
        )

    def minimize(self):
        if not self.is_dfa:
            raise ValueError("Minimization requires a DFA.")
        
        # Step 1: Remove unreachable states
        reachable = {self.start_state}
        queue = deque([self.start_state])
        while queue:
            state = queue.popleft()
            for symbol in self.alphabet:
                next_state = self.transitions.get(state, {}).get(symbol)
                if next_state and next_state not in reachable:
                    reachable.add(next_state)
                    queue.append(next_state)
        states = reachable
        transitions = {s: {a: t for a, t in self.transitions[s].items() if t in reachable} for s in states if s in self.transitions}
        accept_states = self.accept_states & states

        # Step 2: Partition states into accepting and non-accepting
        partitions = [accept_states, states - accept_states]
        partitions = [p for p in partitions if p]
        new_partitions = []

        # Step 3: Refine partitions
        while True:
            for partition in partitions:
                split = defaultdict(set)
                for state in partition:
                    key = tuple(
                        sorted([
                            next(iter([p for p in partitions if self.transitions.get(state, {}).get(symbol, "trap") in p]), ["trap"])[0]
                            for symbol in self.alphabet
                        ])
                    )
                    split[key].add(state)
                new_partitions.extend(split.values())
            if len(new_partitions) == len(partitions):
                break
            partitions = new_partitions
            new_partitions = []

        # Step 4: Build minimized DFA
        state_map = {frozenset(p): f"q{i}" for i, p in enumerate(partitions)}
        new_states = set(state_map.values())
        new_transitions = {}
        new_accept_states = set()
        new_start_state = None

        for partition in partitions:
            rep_state = next(iter(partition))
            new_state = state_map[frozenset(partition)]
            if rep_state == self.start_state:
                new_start_state = new_state
            if rep_state in self.accept_states:
                new_accept_states.add(new_state)
            new_transitions[new_state] = {}
            for symbol in self.alphabet:
                next_state = self.transitions.get(rep_state, {}).get(symbol)
                if next_state:
                    for p in partitions:
                        if next_state in p:
                            new_transitions[new_state][symbol] = state_map[frozenset(p)]
                            break

        return FiniteAutomaton(
            id=f"{self.id}_min",
            name=f"{self.name}_Minimized",
            states=new_states,
            alphabet=self.alphabet,
            transitions=new_transitions,
            start_state=new_start_state,
            accept_states=new_accept_states,
            is_dfa=True
        )