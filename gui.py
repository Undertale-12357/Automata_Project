# gui.py  ── revamped “Create FA” for beginners
import tkinter as tk, re
import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox
from automaton_manager import manage_automaton


class AutomatonGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("🌀 Finite Automaton Designer")
        root.geometry("920x640")
        tb.Label(root, text="🧙‍♂️ Finite Automaton Visual Tool",
                 font=("Georgia", 20, "bold"), bootstyle="info").pack(pady=10)

        top = tb.Frame(root); top.pack()
        for txt, fn in [("🆕 Create FA", self.create_fa),
                        ("📂 Load FA", self.load_fa),
                        ("🧪 Simulate", self.sim_selected),
                        ("🔎 Check Type", self.check_type),
                        ("⚙ Convert", self.convert),
                        ("🔧 Minimize", self.minimize)]:
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
        self.out.insert("end", f"Accept: {', '.join(sorted(fa.accept_states))}\n\nTransitions:\n")
        for s in sorted(fa.transitions):
            for sym, dst in fa.transitions[s].items():
                dsttxt = dst if isinstance(dst, str) else ",".join(sorted(dst))
                self.out.insert("end", f"  δ({s}, {sym}) → {dsttxt}\n")
        self.out.config(state="disabled")

    # ──────────────────────────────────────────────────────────────────────────
    # Create FA
    def create_fa(self):
        dlg = tb.Toplevel(self.root); dlg.title("Create Finite Automaton")
        dlg.geometry("770x460"); dlg.grab_set()

        def add_row(lbl, row, widget):
            tb.Label(dlg, text=lbl, font=("Georgia", 12)).grid(row=row, column=0, sticky="e", padx=6, pady=3)
            widget.grid(row=row, column=1, sticky="w", padx=6, pady=3)

        name_e   = tb.Entry(dlg, width=28)
        states_e = tb.Entry(dlg, width=28)      # csv
        alpha_e  = tb.Entry(dlg, width=28)      # csv
        start_e  = tb.Entry(dlg, width=28)
        accept_e = tb.Entry(dlg, width=28)
        isdfa_v  = tk.BooleanVar(value=False)
        isdfa_cb = tb.Checkbutton(dlg, text="Deterministic ?", variable=isdfa_v, bootstyle="success")

        add_row("Name:",                0, name_e)
        add_row("States (csv):",        1, states_e)
        add_row("Alphabet (csv):",      2, alpha_e)
        add_row("Start state:",         3, start_e)
        add_row("Accept states (csv):", 4, accept_e)
        add_row("",                     5, isdfa_cb)

        # Transitions box with placeholder example
        tb.Label(dlg, text="Transitions (e.g. q0, a → q1,q2):",
                 font=("Georgia", 12)).grid(row=6, column=0, sticky="ne", padx=6, pady=3)
        trans_t = tk.Text(dlg, height=8, width=40, font=("Consolas", 10))
        trans_t.insert("1.0", "q0, a → q0\nq0, a → q1\nq1, b → q2\n")
        trans_t.grid(row=6, column=1, sticky="w")

        # Help pane
        help_txt = (
            "💡 Quick Primer\n"
            "• Format each line:\n"
            "    from_state, symbol → to_state[,to_state]\n"
            "• Multiple targets = NFA.\n"
            "• Use ‘ε’ for epsilon moves.\n"
            "• Separate states or symbols with commas.\n"
            "• Example above accepts strings ending in “ab”."
        )
        tb.Label(dlg, text=help_txt, justify="left", font=("Consolas", 9),
                 bootstyle="secondary").grid(row=0, column=2, rowspan=7, sticky="nsw", padx=10)

        # ── parsing helper
        def parse_transitions(txt, states, alpha, isdfa):
            transitions = {s: {} for s in states}
            line_re = re.compile(r"^\s*([^,]+)\s*,\s*([^→\-]+?)\s*[-­→]+\s*(.+?)\s*$")
            for ln_no, line in enumerate(filter(None, txt.splitlines()), 1):
                m = line_re.match(line)
                if not m:
                    raise ValueError(f"Line {ln_no}: bad format.")
                src, sym, dst_blob = m.groups()
                src, sym = src.strip(), sym.strip()
                dsts = [d.strip() for d in dst_blob.split(",") if d.strip()]
                if src not in states:
                    raise ValueError(f"Line {ln_no}: unknown state {src}.")
                if sym != "ε" and sym not in alpha:
                    raise ValueError(f"Line {ln_no}: symbol {sym} not in alphabet.")
                if not all(d in states for d in dsts):
                    raise ValueError(f"Line {ln_no}: unknown target state.")
                if isdfa and len(dsts) != 1:
                    raise ValueError(f"Line {ln_no}: DFA must have exactly 1 target.")
                transitions[src].setdefault(sym, [] if not isdfa else None)
                if isdfa:
                    transitions[src][sym] = dsts[0]
                else:
                    transitions[src][sym].extend(dsts)
            return transitions

        # ── submit
        def submit():
            name   = name_e.get().strip() or "Untitled"
            states = [s.strip() for s in states_e.get().split(",") if s.strip()]
            alpha  = [s.strip() for s in alpha_e.get().split(",") if s.strip()]
            start  = start_e.get().strip()
            accept = [s.strip() for s in accept_e.get().split(",") if s.strip()]
            isdfa  = isdfa_v.get()
            if not (states and alpha and start and accept):
                return Messagebox.show_error("All fields required.")
            if start not in states or not set(accept).issubset(states):
                return Messagebox.show_error("Start/Accept states invalid.")
            try:
                transitions = parse_transitions(trans_t.get("1.0", "end"),
                                                states, alpha, isdfa)
            except ValueError as e:
                return Messagebox.show_error(str(e))
            res = manage_automaton(action="create", name=name, states=states,
                                   alphabet=alpha, start_state=start,
                                   accept_states=accept, is_dfa=isdfa,
                                   transitions=transitions)
            if "error" in res:
                return Messagebox.show_error(res["error"])
            self.current = res["automaton"]; self.display(self.current)
            self.refresh(); dlg.destroy(); Messagebox.show_info("Automaton saved!")

        tb.Button(dlg, text="Save", bootstyle="success", command=submit)\
           .grid(row=7, column=1, sticky="e", pady=8, padx=5)
        tb.Button(dlg, text="Cancel", bootstyle="danger", command=dlg.destroy)\
           .grid(row=7, column=1, sticky="w", pady=8, padx=5)

    # ──────────────────────────────────────────────────────────────────────────
    # Other toolbar actions (short, unchanged)
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
