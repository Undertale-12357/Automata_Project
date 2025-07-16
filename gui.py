# gui.py  ── "Create FA" without "Copy ε" button
import tkinter as tk, re
import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.tableview import Tableview
from automaton_manager import manage_automaton


class AutomatonGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("🌀 Finite Automaton Designer")
        root.geometry("920x640")
        tb.Label(root, text="🧙‍♂️ Finite Automaton Visual Tool",
                 font=("Georgia", 20, "bold"), bootstyle="info").pack(pady=10)

        top = tb.Frame(root); top.pack()
        for txt, fn in [("🆕 Create FA", self.create_fa),
                        ("📂 Load FA", self.load_fa),
                        ("🧪 Simulate", self.sim_selected),
                        ("🔎 Check Type", self.check_type),
                        ("⚙ Convert", self.convert),
                        ("🔧 Minimize", self.minimize)]:
            tb.Button(top, text=txt, command=fn, bootstyle="info").pack(side="left", padx=5)

        cols = ("DB‑ID", "Public‑ID", "Name", "#States", "#Σ", "#δ")
        self.table = tb.Treeview(root, columns=cols, show="headings", height=10, bootstyle="dark")
        for c in cols:
            self.table.heading(c, text=c); self.table.column(c, anchor="center")
        self.table.pack(fill="both", expand=True, padx=10, pady=8)

        self.out = tk.Text(root, height=12, font=("Consolas", 10), bg="#1e1e2f", fg="white")
        self.out.pack(fill="x", padx=10, pady=5)
        self.out.config(state="disabled")

        self.current = None
        self.refresh()

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    def refresh(self):
        self.table.delete(*self.table.get_children())
        res = manage_automaton(action="list").get("automata", [])
        for fa in res:
            tc = sum(len(v) if isinstance(v, (set, list)) else 1
                     for mp in fa.transitions.values() for v in mp.values())
            self.table.insert("", "end", values=(
                getattr(fa, "db_id", ""), fa.id, fa.name,
                len(fa.states), len(fa.alphabet), tc))

    def display(self, fa):
        self.out.config(state="normal"); self.out.delete("1.0", "end")
        self.out.insert("end", f"Name: {fa.name}   ({'DFA' if fa.is_dfa else 'NFA'})\n")
        self.out.insert("end", f"Public‑ID: {fa.id}\n")
        self.out.insert("end", f"States: {', '.join(sorted(fa.states))}\n")
        self.out.insert("end", f"Alphabet: {', '.join(sorted(fa.alphabet))}\n")
        self.out.insert("end", f"Start: {fa.start_state}\n")
        self.out.insert("end", f"Final: {', '.join(sorted(fa.accept_states))}\n\nTransitions:\n")
        for s in sorted(fa.transitions):
            for sym, dst in fa.transitions[s].items():
                dsttxt = dst if isinstance(dst, str) else ",".join(sorted(dst))
                self.out.insert("end", f"  δ({s}, {sym}) → {dsttxt}\n")
        self.out.config(state="disabled")

    # ──────────────────────────────────────────────────────────────────────────
    # Create FA
    def create_fa(self):
        dlg = tb.Toplevel(self.root); dlg.title("Create Finite Automaton")
        dlg.geometry("900x600"); dlg.grab_set()

        def add_row(lbl, row, widget, example=None):
            tb.Label(dlg, text=lbl, font=("Georgia", 12)).grid(row=row, column=0, sticky="e", padx=6, pady=3)
            widget.grid(row=row, column=1, sticky="w", padx=6, pady=3)
            if example:
                tb.Label(dlg, text=f"e.g., {example}", font=("Georgia", 10), bootstyle="secondary").grid(row=row, column=2, sticky="w", padx=6, pady=3)

        name_e   = tb.Entry(dlg, width=28)
        states_e = tb.Entry(dlg, width=28)      # space-separated
        alpha_e  = tb.Entry(dlg, width=28)      # space-separated
        start_e  = tb.Entry(dlg, width=28)
        final_e  = tb.Entry(dlg, width=28)      # space-separated
        isdfa_v  = tk.BooleanVar(value=False)
        isdfa_cb = tb.Checkbutton(dlg, text="Deterministic ?", variable=isdfa_v, bootstyle="success")

        add_row("Name:",                0, name_e,   "MyAutomaton")
        add_row("States (space-separated):", 1, states_e, "A B C")
        add_row("Alphabet (space-separated):", 2, alpha_e,  "a c")
        add_row("Start state:",         3, start_e,  "A")
        add_row("Final states (space-separated):", 4, final_e, "C")
        add_row("",                     5, isdfa_cb)

        # Transitions frame with dynamic grid
        trans_frame = tb.Frame(dlg)
        trans_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
        trans_label = tb.Label(trans_frame, text="Transitions (e.g., a: B,C or - for none):", font=("Georgia", 12))
        trans_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        trans_status = tb.Label(trans_frame, text="Enter states and alphabet to define transitions.", font=("Consolas", 10), bootstyle="warning")
        trans_status.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        # Dictionary to store transition entries
        trans_entries = {}
        trans_labels = []

        def update_trans_grid(*args):
            # Clear existing widgets except label and status
            for widget in trans_frame.grid_slaves():
                if widget not in (trans_label, trans_status):
                    widget.destroy()
            trans_entries.clear()
            trans_labels.clear()

            states = [s.strip() for s in states_e.get().split() if s.strip()]
            alpha = [s.strip() for s in alpha_e.get().split() if s.strip()]
            if not (states and alpha):
                trans_status.config(text="Enter states and alphabet to define transitions.")
                return

            trans_status.config(text="Define transitions (e.g., a: B,C; ε: B for epsilon):")
            row_idx = 2  # Start after label and status
            for state in states:
                lbl = tb.Label(trans_frame, text=f"State {state}:", font=("Consolas", 10, "bold"))
                lbl.grid(row=row_idx, column=0, sticky="e", padx=10, pady=5)
                trans_labels.append(lbl)
                row_idx += 1
                for sym in alpha + (["ε"] if not isdfa_v.get() else []):
                    lbl = tb.Label(trans_frame, text=f"{sym}:", font=("Consolas", 10))
                    lbl.grid(row=row_idx, column=0, sticky="e", padx=20, pady=2)
                    entry = tb.Entry(trans_frame, width=20)
                    entry.grid(row=row_idx, column=1, sticky="w", padx=10, pady=2)
                    entry.focus_set()  # Ensure entries can gain focus
                    trans_entries[(state, sym)] = entry
                    trans_labels.append(lbl)
                    # Example values for first state
                    if state == states[0] and sym == alpha[0]:
                        entry.insert(0, "B,C")
                    elif state == states[0] and sym == "ε":
                        entry.insert(0, "-")
                    row_idx += 1

        # Bind updates to state, alphabet, and DFA checkbox changes
        states_e.bind("<KeyRelease>", update_trans_grid)
        alpha_e.bind("<KeyRelease>", update_trans_grid)
        isdfa_v.trace("w", update_trans_grid)
        update_trans_grid()  # Initial grid setup

        # Help pane
        help_txt = (
            "💡 Quick Primer\n"
            "• States: Separate with spaces (e.g., A B C)\n"
            "• Alphabet: Separate with spaces (e.g., a c). Do not include ε\n"
            "• Transitions: For each state and symbol, enter target state(s)\n"
            "  - Use commas for multiple targets (e.g., B,C)\n"
            "  - Use '-' for no transition\n"
            "  - For ε fields (NFA only), enter target states (e.g., B or B,C)\n"
            "• Example: State A, a: B,C; ε: B (epsilon to B)\n"
            "• Example above accepts strings with 'a' or ε to B"
        )
        tb.Label(dlg, text=help_txt, justify="left", font=("Consolas", 9),
                 bootstyle="secondary").grid(row=0, column=3, rowspan=7, sticky="nsw", padx=10)

        # ── parsing helper
        def parse_transitions(entries, states, alpha, isdfa):
            transitions = {s: {} for s in states}
            for state in states:
                for sym in alpha + (["ε"] if not isdfa else []):
                    val = entries.get((state, sym), tb.Entry(dlg)).get().strip()
                    print(f"Parsing transition for {state}, {sym}: {val}")  # Debug
                    if not val or val == "-":
                        continue
                    if val == "ε":
                        raise ValueError(f"Invalid input for {state}, {sym}: 'ε' is not a valid target state. Enter a state (e.g., B or B,C).")
                    dsts = [d.strip() for d in val.split(",") if d.strip()]
                    if not all(d in states for d in dsts):
                        raise ValueError(f"Invalid target state for {state}, {sym}: {val}. Targets must be in {states}.")
                    if sym != "ε" and sym not in alpha:
                        raise ValueError(f"Symbol {sym} not in alphabet for {state}")
                    if isdfa and len(dsts) > 1:
                        raise ValueError(f"DFA cannot have multiple targets for {state}, {sym}")
                    transitions[state][sym] = dsts[0] if isdfa else dsts
            return transitions

        # ── submit
        def submit():
            name = name_e.get().strip() or "Untitled"
            states = [s.strip() for s in states_e.get().split() if s.strip()]
            alpha = [s.strip() for s in alpha_e.get().split() if s.strip()]
            start = start_e.get().strip()
            final = [s.strip() for s in final_e.get().split() if s.strip()]
            isdfa = isdfa_v.get()
            if not (states and alpha and start and final):
                return Messagebox.show_error("All fields required.")
            if start not in states or not set(final).issubset(states):
                return Messagebox.show_error("Start/Final states invalid.")
            try:
                transitions = parse_transitions(trans_entries, states, alpha, isdfa)
            except ValueError as e:
                return Messagebox.show_error(str(e))
            res = manage_automaton(action="create", name=name, states=states,
                                   alphabet=alpha, start_state=start,
                                   accept_states=final, is_dfa=isdfa,
                                   transitions=transitions)
            if "error" in res:
                return Messagebox.show_error(res["error"])
            self.current = res["automaton"]
            self.display(self.current)
            self.refresh()

            # Show confirmation and transition table
            confirm_dlg = tb.Toplevel(self.root)
            confirm_dlg.title("Automaton Created")
            confirm_dlg.geometry("600x400")
            tb.Label(confirm_dlg, text="Automaton saved successfully!", font=("Georgia", 12), bootstyle="success").pack(pady=10)

            # Transition table
            cols = ["State"] + alpha + (["ε"] if not isdfa else [])
            rows = []
            for state in sorted(states):
                row = [state]
                for sym in alpha + (["ε"] if not isdfa else []):
                    dst = transitions.get(state, {}).get(sym, "-")
                    row.append(dst if isinstance(dst, str) else ",".join(sorted(dst)) if dst else "-")
                rows.append(row)
            table = Tableview(confirm_dlg, coldata=cols, rowdata=rows, bootstyle="dark", autofit=True)
            table.pack(fill="both", expand=True, padx=10, pady=10)
            tb.Button(confirm_dlg, text="Close", bootstyle="danger", command=confirm_dlg.destroy).pack(pady=5)

            dlg.destroy()

        tb.Button(dlg, text="Save", bootstyle="success", command=submit)\
           .grid(row=7, column=1, sticky="e", pady=8, padx=5)
        tb.Button(dlg, text="Cancel", bootstyle="danger", command=dlg.destroy)\
           .grid(row=7, column=1, sticky="w", pady=8, padx=5)

    # ──────────────────────────────────────────────────────────────────────────
    # Other toolbar actions (unchanged)
    def load_fa(self):
        sel = self.table.selection()
        pid = self.table.item(sel[0])["values"][1] if sel else None
        if not pid:
            return Messagebox.show_error("Select an FA row first.")
        res = manage_automaton(action="load", id=pid)
        if "error" in res: return Messagebox.show_error(res["error"])
        self.current = res["automaton"]; self.display(self.current)

    def sim_selected(self):
        if not self.current: return Messagebox.show_error("Load an FA first.")
        s = tb.ask_string("Input String", "Enter input:")
        if s is None: return
        ok = manage_automaton(action="simulate", automaton=self.current,
                              input_string=s)["result"]
        Messagebox.show_info("ACCEPTED" if ok else "REJECTED")

    def check_type(self):
        if not self.current: return Messagebox.show_error("Load an FA first.")
        isdfa = manage_automaton(action="check_type", automaton=self.current)["type"]
        Messagebox.show_info("DFA" if isdfa else "NFA")

    def convert(self):
        if not self.current: return Messagebox.show_error("Load an FA first.")
        res = manage_automaton(action="convert", automaton=self.current)
        if "error" in res: return Messagebox.show_error(res["error"])
        self.current = res["automaton"]; self.display(self.current); self.refresh()

    def minimize(self):
        if not self.current: return Messagebox.show_error("Load an FA first.")
        res = manage_automaton(action="minimize", automaton=self.current)
        if "error" in res: return Messagebox.show_error(res["error"])
        self.current = res["automaton"]; self.display(self.current); self.refresh()


if __name__ == "__main__":
    root = tb.Window(themename="superhero")
    AutomatonGUI(root)
    root.mainloop()