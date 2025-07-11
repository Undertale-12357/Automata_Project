# Finite Automaton Project with Visual Editor and Full Feature Set

import json
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk, Canvas
from collections import deque

class FiniteAutomaton:
    def __init__(self, id, name, states, alphabet, transitions, start_state, accept_states, is_dfa=True):
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

    def simulate(self, input_string):
        if self.is_dfa:
            state = self.start_state
            for sym in input_string:
                if sym in self.transitions[state]:
                    state = self.transitions[state][sym]
                else:
                    return False
            return state in self.accept_states
        else:
            current_states = {self.start_state}
            for sym in input_string:
                next_states = set()
                for st in current_states:
                    next_states.update(self.transitions.get(st, {}).get(sym, []))
                current_states = next_states
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
                dest_name = ','.join(sorted(dest))
                new_trans[curr_name][sym] = dest_name
                if dest and dest_name not in visited:
                    queue.append(frozenset(dest))

        new_accepts = {s for s in new_states if set(s.split(',')) & self.accept_states}
        return FiniteAutomaton(
            id=self.id + "_dfa",
            name=self.name + " (DFA)",
            states=new_states,
            alphabet=self.alphabet,
            transitions=new_trans,
            start_state=','.join(sorted(start)),
            accept_states=new_accepts,
            is_dfa=True
        )

    def minimize(self):
        assert self.is_dfa
        return self  # Placeholder

fa_store = {}

def save_fa_to_json(fa, path):
    with open(path, 'w') as f:
        json.dump(fa.to_dict(), f, indent=2)

def load_fa_from_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    fa = FiniteAutomaton(**data)
    fa_store[fa.id] = fa
    return fa

def create_fa():
    new_id = simpledialog.askstring("New FA", "Enter FA ID:")
    if not new_id or new_id in fa_store:
        messagebox.showerror("Error", "Invalid or duplicate ID.")
        return
    name = simpledialog.askstring("FA Name", "Enter FA Name:") or new_id
    try:
        num_states = int(simpledialog.askstring("States", "How many states?"))
        num_symbols = int(simpledialog.askstring("Alphabet", "How many input symbols?"))
    except:
        messagebox.showerror("Error", "Invalid number format.")
        return

    states = [f"q{i}" for i in range(num_states)]
    alphabet = [simpledialog.askstring("Alphabet", f"Symbol {i+1}:") for i in range(num_symbols)]
    start_state = simpledialog.askstring("Start State", f"Choose start state from {states}:")
    accept_states_input = simpledialog.askstring("Accept States", f"Enter accept states separated by commas from {states}:")
    accept_states = [s.strip() for s in accept_states_input.split(",") if s.strip() in states]

    transitions = {}
    is_dfa = messagebox.askyesno("DFA or NFA", "Is this a DFA?")

    for state in states:
        transitions[state] = {}
        for sym in alphabet:
            prompt = f"δ({state}, {sym}) = "
            target = simpledialog.askstring("Transition", prompt)
            if is_dfa:
                transitions[state][sym] = target
            else:
                transitions[state][sym] = [s.strip() for s in target.split(',') if s.strip() in states]

    fa = FiniteAutomaton(
        id=new_id,
        name=name,
        states=states,
        alphabet=alphabet,
        transitions=transitions,
        start_state=start_state,
        accept_states=accept_states,
        is_dfa=is_dfa
    )
    fa_store[new_id] = fa
    path = filedialog.asksaveasfilename(defaultextension=".json")
    if path:
        save_fa_to_json(fa, path)


def show_visual_editor():
    win = tk.Toplevel()
    win.title("Visual FA Designer")
    canvas = Canvas(win, width=800, height=600, bg="white")
    canvas.pack()

    fid = simpledialog.askstring("Visualize FA", "Enter FA ID:")
    if not fid or fid not in fa_store:
        messagebox.showerror("Error", "Invalid FA ID")
        return

    fa = fa_store[fid]
    positions = {}
    state_list = list(fa.states)
    for i, s in enumerate(state_list):
        x, y = 150 + (i % 4) * 150, 100 + (i // 4) * 150
        positions[s] = (x, y)
        r = 30
        canvas.create_oval(x-r, y-r, x+r, y+r, fill="lightblue")
        canvas.create_text(x, y, text=s)
        if s in fa.accept_states:
            canvas.create_oval(x-r+5, y-r+5, x+r-5, y+r-5)

    for src in fa.transitions:
        for sym, dsts in fa.transitions[src].items():
            if isinstance(dsts, str): dsts = [dsts]
            for dst in dsts:
                x1, y1 = positions[src]
                x2, y2 = positions[dst]
                canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST)
                canvas.create_text((x1+x2)//2, (y1+y2)//2 - 10, text=sym)


def run_gui():
    def list_fas():
        table.delete(*table.get_children())
        for fa in fa_store.values():
            table.insert('', 'end', values=(fa.id, fa.name, len(fa.states), len(fa.alphabet), sum(len(v) for v in fa.transitions.values())))

    def simulate_selected():
        fid = simpledialog.askstring("FA ID", "Enter FA ID to simulate on:")
        if fid in fa_store:
            inp = simpledialog.askstring("Input String", "Enter input string:")
            result = fa_store[fid].simulate(inp)
            messagebox.showinfo("Result", f"String is {'ACCEPTED' if result else 'REJECTED'}.")

    def check_type():
        fid = simpledialog.askstring("FA ID", "Enter FA ID to check:")
        if fid in fa_store:
            messagebox.showinfo("FA Type", "DFA" if fa_store[fid].is_dfa_check() else "NFA")

    def convert_nfa():
        fid = simpledialog.askstring("FA ID", "Enter NFA ID to convert:")
        if fid in fa_store and not fa_store[fid].is_dfa:
            dfa = fa_store[fid].convert_to_dfa()
            fa_store[dfa.id] = dfa
            messagebox.showinfo("Converted", f"Converted NFA to DFA as ID {dfa.id}")
            list_fas()

    def minimize_dfa():
        fid = simpledialog.askstring("FA ID", "Enter DFA ID to minimize:")
        if fid in fa_store and fa_store[fid].is_dfa:
            minimized = fa_store[fid].minimize()
            fa_store[minimized.id + "_min"] = minimized
            messagebox.showinfo("Minimized", "Minimized DFA added to list.")
            list_fas()

    root = tk.Tk()
    root.title("Finite Automaton Tool")

    tk.Button(root, text="Create New FA", command=create_fa).pack(pady=2)
    tk.Button(root, text="Load FA", command=lambda: [load_fa_from_json(filedialog.askopenfilename()), list_fas()]).pack(pady=2)
    tk.Button(root, text="Save FA", command=lambda: save_fa_to_json(fa_store[simpledialog.askstring("Save", "Enter FA ID")], filedialog.asksaveasfilename())).pack(pady=2)
    tk.Button(root, text="Simulate Input", command=simulate_selected).pack(pady=2)
    tk.Button(root, text="Check FA Type", command=check_type).pack(pady=2)
    tk.Button(root, text="Convert NFA to DFA", command=convert_nfa).pack(pady=2)
    tk.Button(root, text="Minimize DFA", command=minimize_dfa).pack(pady=2)
    tk.Button(root, text="Visual Editor", command=show_visual_editor).pack(pady=2)

    table = ttk.Treeview(root, columns=("ID", "Name", "States", "Symbols", "Transitions"), show="headings")
    for col in ("ID", "Name", "States", "Symbols", "Transitions"):
        table.heading(col, text=col)
    table.pack()

    list_fas()
    root.mainloop()

if __name__ == '__main__':
    run_gui()
