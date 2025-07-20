import tkinter as tk
from tkinter import ttk, messagebox
from database import FADatabase
from fa import FiniteAutomaton
import logging
import sqlite3  # Added for exception handling

# Set up logging
logging.basicConfig(filename='fa_tool.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class FAApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Finite Automaton Visual Tool")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f8f9fa")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_styles()

        logging.info("Initializing FADatabase")
        self.db = FADatabase()
        logging.info("Verifying database schema")
        self.db.verify_schema()
        logging.info("Loading all FAs")
        self.fas = self.db.load_all_fas()

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky='nsew')

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.grid(row=0, column=0, sticky='nsew')
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        self.title = ttk.Label(self.content_frame, text="Finite Automaton Visual Tool", font=("Helvetica", 24, 'bold'),
                               background="#f8f9fa", foreground="#212529")
        self.title.grid(row=0, column=0, pady=20, sticky='ew')

        self.create_category_buttons()
        self.create_dynamic_area()

    def _configure_styles(self):
        self.style.configure('TButton', font=('Helvetica', 14, 'bold'), padding=10)
        self.style.map('TButton', foreground=[('active', 'white')], background=[('active', '#0d6efd')])
        self.style.configure('Category.TButton', background='#0d6efd', foreground='white', font=('Helvetica', 14, 'bold'), padding=12)
        self.style.map('Category.TButton', background=[('active', '#084298')])
        self.style.configure('Danger.TButton', background='#dc3545', foreground='white', font=('Helvetica', 14, 'bold'), padding=12)
        self.style.map('Danger.TButton', background=[('active', '#a71d2a')])
        self.style.configure('Success.TButton', background='#198754', foreground='white', font=('Helvetica', 14, 'bold'), padding=12)
        self.style.map('Success.TButton', background=[('active', '#146c43')])

    def create_dynamic_area(self):
        container = ttk.Frame(self.content_frame)
        container.grid(row=2, column=0, sticky='nsew')
        canvas = tk.Canvas(container, borderwidth=0, background="#e8e6e1", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        self.dynamic_frame = ttk.Frame(canvas)
        self.dynamic_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.dynamic_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        self._bind_mousewheel(canvas)

    def _bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def create_category_buttons(self):
        button_frame = ttk.Frame(self.content_frame)
        button_frame.grid(row=1, column=0, pady=10, sticky='ew')
        self.content_frame.columnconfigure(0, weight=1)
        ttk.Button(button_frame, text="Design FA", command=self.show_design_options, style='Category.TButton').grid(row=0, column=0, padx=5, pady=6, sticky="ew")
        ttk.Button(button_frame, text="Simulate / Analyze", command=self.show_simulate_options, style='Success.TButton').grid(row=0, column=1, padx=5, pady=6, sticky="ew")
        ttk.Button(button_frame, text="Optimize FA", command=self.show_conversion_options, style='Danger.TButton').grid(row=0, column=2, padx=5, pady=6, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

    def clear_dynamic_frame(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

    def show_design_options(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Design Finite Automata", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        self.dynamic_frame.columnconfigure(0, weight=1)
        button_frame = ttk.Frame(self.dynamic_frame)
        button_frame.grid(row=1, column=0, pady=10)
        ttk.Button(button_frame, text="Create FA", command=self.create_fa_ui, style='Category.TButton').pack(side=tk.LEFT, padx=5, pady=8)
        ttk.Button(button_frame, text="Edit FA", command=self.edit_fa_ui, style='Success.TButton').pack(side=tk.LEFT, padx=5, pady=8)
        ttk.Button(button_frame, text="Delete FA", command=self.delete_fa_ui, style='Danger.TButton').pack(side=tk.LEFT, padx=5, pady=8)
        ttk.Button(button_frame, text="Show FA Structure", command=self.show_fa_ui, style='Category.TButton').pack(side=tk.LEFT, padx=5, pady=8)

    def create_fa_ui(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Create New Finite Automaton", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)

        ttk.Label(self.dynamic_frame, text="Name:").grid(row=1, column=0, sticky='w', padx=5, pady=4)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(self.dynamic_frame, textvariable=name_var, font=("Helvetica", 14))
        name_entry.grid(row=1, column=1, sticky='ew', pady=4, padx=5)

        ttk.Label(self.dynamic_frame, text="States (comma separated):").grid(row=2, column=0, sticky='w', padx=5, pady=4)
        states_var = tk.StringVar()
        states_entry = ttk.Entry(self.dynamic_frame, textvariable=states_var, font=("Helvetica", 14))
        states_entry.grid(row=2, column=1, sticky='ew', pady=4, padx=5)

        ttk.Label(self.dynamic_frame, text="Alphabet (comma separated):").grid(row=3, column=0, sticky='w', padx=5, pady=4)
        alphabet_var = tk.StringVar()
        alphabet_entry = ttk.Entry(self.dynamic_frame, textvariable=alphabet_var, font=("Helvetica", 14))
        alphabet_entry.grid(row=3, column=1, sticky='ew', pady=4, padx=5)

        ttk.Label(self.dynamic_frame, text="Start State:").grid(row=4, column=0, sticky='w', padx=5, pady=4)
        start_var = tk.StringVar()
        start_entry = ttk.Entry(self.dynamic_frame, textvariable=start_var, font=("Helvetica", 14))
        start_entry.grid(row=4, column=1, sticky='ew', pady=4, padx=5)

        ttk.Label(self.dynamic_frame, text="Final (Accept) States (comma separated):").grid(row=5, column=0, sticky='w', padx=5, pady=4)
        final_var = tk.StringVar()
        final_entry = ttk.Entry(self.dynamic_frame, textvariable=final_var, font=("Helvetica", 14))
        final_entry.grid(row=5, column=1, sticky='ew', pady=4, padx=5)

        transitions_container = ttk.Frame(self.dynamic_frame)
        transitions_container.grid(row=6, column=0, columnspan=2, sticky='nsew', pady=10)
        self.dynamic_frame.rowconfigure(6, weight=1)
        transitions_container.columnconfigure(0, weight=1)

        transitions_canvas = tk.Canvas(transitions_container, background="#f8f9fa")
        transitions_scrollbar_y = ttk.Scrollbar(transitions_container, orient="vertical", command=transitions_canvas.yview)
        transitions_scrollbar_x = ttk.Scrollbar(transitions_container, orient="horizontal", command=transitions_canvas.xview)
        transitions_inner = ttk.Frame(transitions_canvas)

        transitions_canvas.create_window((0, 0), window=transitions_inner, anchor="nw")
        transitions_canvas.configure(yscrollcommand=transitions_scrollbar_y.set, xscrollcommand=transitions_scrollbar_x.set)
        transitions_container.columnconfigure(0, weight=1)
        transitions_container.rowconfigure(0, weight=1)
        transitions_canvas.grid(row=0, column=0, sticky='nsew')
        transitions_scrollbar_y.grid(row=0, column=1, sticky='ns')
        transitions_scrollbar_x.grid(row=1, column=0, sticky='ew')

        transitions_status_label = ttk.Label(transitions_inner, text="Enter states and alphabet to define transitions", font=("Helvetica", 12), foreground="gray")
        transitions_status_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
        transitions_inputs = {}

        def build_transitions_grid(*args):
            logging.info("Building transitions grid")
            for widget in transitions_inner.winfo_children():
                widget.destroy()
            states = [s.strip() for s in states_var.get().split(",") if s.strip()]
            alphabet = [a.strip() for a in alphabet_var.get().split(",") if a.strip()]
            if 'ε' not in alphabet:
                alphabet.append('ε')
            if not states or not alphabet:
                transitions_status_label = ttk.Label(transitions_inner, text="Enter states and alphabet to define transitions", font=("Helvetica", 12), foreground="gray")
                transitions_status_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
                logging.info("No states or alphabet entered, showing placeholder")
                transitions_canvas.configure(scrollregion=transitions_canvas.bbox("all"))
                return
            logging.info(f"States: {states}, Alphabet: {alphabet}")
            ttk.Label(transitions_inner, text="Transitions (enter target state(s), comma-separated):").grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
            for col_idx, sym in enumerate(alphabet):
                ttk.Label(transitions_inner, text=sym, font=("Helvetica", 12, "bold")).grid(row=1, column=col_idx + 1, padx=5, pady=5)
            for row_idx, st in enumerate(states):
                ttk.Label(transitions_inner, text=st, font=("Helvetica", 12, "bold")).grid(row=row_idx + 2, column=0, padx=5, pady=5)
                for col_idx, sym in enumerate(alphabet):
                    e = ttk.Entry(transitions_inner, width=15, font=("Helvetica", 12))
                    e.grid(row=row_idx + 2, column=col_idx + 1, padx=5, pady=3, sticky='ew')
                    transitions_inputs[(st, sym)] = e
            transitions_inner.columnconfigure(1, weight=1)
            transitions_canvas.update_idletasks()
            transitions_canvas.configure(scrollregion=transitions_canvas.bbox("all"))
            logging.info("Transitions grid built successfully")

        states_var.trace_add("write", build_transitions_grid)
        alphabet_var.trace_add("write", build_transitions_grid)
        build_transitions_grid()  # Initial call to set up placeholder

        def save_new_fa():
            try:
                name = name_var.get().strip()
                states = [s.strip() for s in states_var.get().split(",") if s.strip()]
                alphabet = [a.strip() for a in alphabet_var.get().split(",") if a.strip()]
                start_state = start_var.get().strip()
                final_states = [s.strip() for s in final_var.get().split(",") if s.strip()]

                logging.info(f"Saving FA: Name={name}, States={states}, Alphabet={alphabet}, Start={start_state}, Final={final_states}")

                if not name:
                    messagebox.showerror("Error", "Name cannot be empty")
                    logging.error("Name is empty")
                    return
                if not states:
                    messagebox.showerror("Error", "States cannot be empty")
                    logging.error("States are empty")
                    return
                if not alphabet:
                    messagebox.showerror("Error", "Alphabet cannot be empty")
                    logging.error("Alphabet is empty")
                    return
                if start_state not in states:
                    messagebox.showerror("Error", f"Start state '{start_state}' must be in states")
                    logging.error(f"Invalid start state: {start_state}")
                    return
                if not set(final_states).issubset(states):
                    messagebox.showerror("Error", "Final states must be subset of states")
                    logging.error(f"Invalid final states: {final_states}")
                    return

                transitions = {}
                for st in states:
                    transitions[st] = {}
                    for sym in alphabet:
                        val = transitions_inputs.get((st, sym))
                        tgt = val.get().strip() if val else ''
                        if tgt:
                            targets = [t.strip() for t in tgt.split(",") if t.strip()]
                            if not all(t in states for t in targets):
                                messagebox.showerror("Error", f"Invalid transition target(s) '{tgt}' for state '{st}' and symbol '{sym}'")
                                logging.error(f"Invalid transition targets: {tgt} for state {st}, symbol {sym}")
                                return
                            transitions[st][sym] = targets

                new_id = self.db.generate_next_fa_id()
                fa = FiniteAutomaton(new_id, name, states, alphabet, transitions, start_state, final_states)
                logging.info(f"Saving new FA with ID {new_id}")
                self.db.save_fa(fa)
                logging.info(f"Loading FAs after saving {new_id}")
                self.fas = self.db.load_all_fas()
                fa_type = "DFA" if fa.is_dfa() else "NFA"
                messagebox.showinfo("Success", f"FA '{name}' created with ID {new_id} (Type: {fa_type})")
                logging.info(f"FA {new_id} created successfully: Type={fa_type}")
                self.show_design_options()

            except Exception as e:
                logging.error(f"Error saving new FA: {str(e)}")
                messagebox.showerror("Error", f"Failed to create FA: {str(e)}")

        ttk.Button(self.dynamic_frame, text="Save FA", command=save_new_fa, style='Category.TButton').grid(row=7, column=0, columnspan=2, pady=10, padx=5)

    def edit_fa_ui(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Edit Existing Finite Automaton", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)

        ttk.Label(self.dynamic_frame, text="Select FA by ID and Name:").grid(row=1, column=0, sticky='w', padx=5, pady=4)
        fa_ids_names = [f"{fa.id} - {fa.name}" for fa in self.fas]
        fa_id_map = {f"{fa.id} - {fa.name}": fa.id for fa in self.fas}
        if not fa_ids_names:
            ttk.Label(self.dynamic_frame, text="No FAs available. Create one first.", foreground="red").grid(row=1, column=1, sticky='w', padx=5, pady=4)
            return

        selected_id_var = tk.StringVar()
        selected_id_combo = ttk.Combobox(self.dynamic_frame, values=fa_ids_names, textvariable=selected_id_var, state="readonly", font=("Helvetica", 14))
        selected_id_combo.grid(row=1, column=1, sticky='ew', pady=4, padx=5)

        container = ttk.Frame(self.dynamic_frame)
        container.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=10)
        self.dynamic_frame.rowconfigure(2, weight=1)

        def load_selected_fa():
            for widget in container.winfo_children():
                widget.destroy()
            selected_id_name = selected_id_var.get()
            if not selected_id_name:
                messagebox.showerror("Error", "Please select an FA to edit")
                logging.error("No FA selected for editing")
                return
            selected_id = fa_id_map.get(selected_id_name)
            if not selected_id:
                messagebox.showerror("Error", "Selected FA not found")
                logging.error(f"FA with ID {selected_id_name} not found")
                return
            fa = next((f for f in self.fas if f.id == selected_id), None)
            if not fa:
                messagebox.showerror("Error", "Selected FA not found")
                logging.error(f"FA with ID {selected_id} not found")
                return

            ttk.Label(container, text="Name:").grid(row=0, column=0, sticky='w', padx=5, pady=4)
            name_var = tk.StringVar(value=fa.name)
            name_entry = ttk.Entry(container, textvariable=name_var, font=("Helvetica", 14))
            name_entry.grid(row=0, column=1, sticky='ew', pady=4, padx=5)

            ttk.Label(container, text="States (comma separated):").grid(row=1, column=0, sticky='w', padx=5, pady=4)
            states_var = tk.StringVar(value=", ".join(fa.states))
            states_entry = ttk.Entry(container, textvariable=states_var, font=("Helvetica", 14))
            states_entry.grid(row=1, column=1, sticky='ew', pady=4, padx=5)

            ttk.Label(container, text="Alphabet (comma separated):").grid(row=2, column=0, sticky='w', padx=5, pady=4)
            alphabet_var = tk.StringVar(value=", ".join(fa.alphabet))
            alphabet_entry = ttk.Entry(container, textvariable=alphabet_var, font=("Helvetica", 14))
            alphabet_entry.grid(row=2, column=1, sticky='ew', pady=4, padx=5)

            ttk.Label(container, text="Start State:").grid(row=3, column=0, sticky='w', padx=5, pady=4)
            start_var = tk.StringVar(value=fa.start_state)
            start_entry = ttk.Entry(container, textvariable=start_var, font=("Helvetica", 14))
            start_entry.grid(row=3, column=1, sticky='ew', pady=4, padx=5)

            ttk.Label(container, text="Final (Accept) States (comma separated):").grid(row=4, column=0, sticky='w', padx=5, pady=4)
            final_var = tk.StringVar(value=", ".join(fa.final_states))
            final_entry = ttk.Entry(container, textvariable=final_var, font=("Helvetica", 14))
            final_entry.grid(row=4, column=1, sticky='ew', pady=4, padx=5)

            transitions_frame = ttk.Frame(container)
            transitions_frame.grid(row=5, column=0, columnspan=2, sticky='nsew', pady=10)
            container.rowconfigure(5, weight=1)
            ttk.Label(transitions_frame, text="Transitions (enter target state(s), comma-separated):").grid(row=0, column=0, sticky='w', columnspan=2)

            transitions_inputs = {}

            def build_transitions_grid(*args):
                for widget in transitions_frame.winfo_children():
                    if int(widget.grid_info().get("row", 0)) > 0:
                        widget.destroy()
                states = [s.strip() for s in states_var.get().split(",") if s.strip()]
                alphabet = [a.strip() for a in alphabet_var.get().split(",") if a.strip()]
                if 'ε' not in alphabet:
                    alphabet.append('ε')
                if not states or not alphabet:
                    return
                for col_idx, sym in enumerate(alphabet):
                    ttk.Label(transitions_frame, text=sym, font=("Helvetica", 12, "bold")).grid(row=1, column=col_idx + 1, padx=5, pady=5)
                for row_idx, st in enumerate(states):
                    ttk.Label(transitions_frame, text=st, font=("Helvetica", 12, "bold")).grid(row=row_idx + 2, column=0, padx=5, pady=5)
                    for col_idx, sym in enumerate(alphabet):
                        e = ttk.Entry(transitions_frame, width=15, font=("Helvetica", 12))
                        e.grid(row=row_idx + 2, column=col_idx + 1, padx=5, pady=3, sticky='ew')
                        val = fa.transitions.get(st, {}).get(sym, [])
                        e.insert(0, ", ".join(val) if isinstance(val, list) else val)
                        transitions_inputs[(st, sym)] = e
                transitions_frame.columnconfigure(1, weight=1)

            states_var.trace_add("write", build_transitions_grid)
            alphabet_var.trace_add("write", build_transitions_grid)
            build_transitions_grid()

            def save_edited_fa():
                try:
                    name = name_var.get().strip()
                    states = [s.strip() for s in states_var.get().split(",") if s.strip()]
                    alphabet = [a.strip() for a in alphabet_var.get().split(",") if a.strip()]
                    start_state = start_var.get().strip()
                    final_states = [s.strip() for s in final_var.get().split(",") if s.strip()]

                    logging.info(f"Updating FA: ID={selected_id}, Name={name}, States={states}, Alphabet={alphabet}, Start={start_state}, Final={final_states}")

                    if not name:
                        messagebox.showerror("Error", "Name cannot be empty")
                        logging.error("Name is empty")
                        return
                    if not states:
                        messagebox.showerror("Error", "States cannot be empty")
                        logging.error("States are empty")
                        return
                    if not alphabet:
                        messagebox.showerror("Error", "Alphabet cannot be empty")
                        logging.error("Alphabet is empty")
                        return
                    if start_state not in states:
                        messagebox.showerror("Error", f"Start state '{start_state}' must be in states")
                        logging.error(f"Invalid start state: {start_state}")
                        return
                    if not set(final_states).issubset(states):
                        messagebox.showerror("Error", "Final states must be subset of states")
                        logging.error(f"Invalid final states: {final_states}")
                        return

                    transitions = {}
                    for st in states:
                        transitions[st] = {}
                        for sym in alphabet:
                            val = transitions_inputs.get((st, sym))
                            tgt = val.get().strip() if val else ''
                            if tgt:
                                targets = [t.strip() for t in tgt.split(",") if t.strip()]
                                if not all(t in states for t in targets):
                                    messagebox.showerror("Error", f"Invalid transition target(s) '{tgt}' for state '{st}' and symbol '{sym}'")
                                    logging.error(f"Invalid transition targets: {tgt} for state {st}, symbol {sym}")
                                    return
                                transitions[st][sym] = targets

                    fa.name = name
                    fa.states = states
                    fa.alphabet = alphabet
                    fa.start_state = start_state
                    fa.final_states = final_states
                    fa.transitions = transitions

                    logging.info(f"Updating FA with ID {fa.id}")
                    self.db.update_fa(fa)
                    logging.info(f"Loading FAs after updating {fa.id}")
                    self.fas = self.db.load_all_fas()
                    fa_type = "DFA" if fa.is_dfa() else "NFA"
                    messagebox.showinfo("Success", f"FA '{name}' updated (Type: {fa_type})")
                    logging.info(f"FA {fa.id} updated successfully: Type={fa_type}")
                    self.show_design_options()

                except Exception as e:
                    logging.error(f"Error updating FA {selected_id}: {str(e)}")
                    messagebox.showerror("Error", f"Failed to update FA: {str(e)}")

            ttk.Button(container, text="Save Changes", command=save_edited_fa, style='Success.TButton').grid(row=6, column=0, columnspan=2, pady=10, padx=5)

        ttk.Button(self.dynamic_frame, text="Load FA", command=load_selected_fa, style='Category.TButton').grid(row=3, column=0, columnspan=2, pady=8, padx=5)

    def delete_fa_ui(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Delete Finite Automaton", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        fa_ids_names = [f"{fa.id} - {fa.name}" for fa in self.fas]
        fa_id_map = {f"{fa.id} - {fa.name}": fa.id for fa in self.fas}
        if not fa_ids_names:
            ttk.Label(self.dynamic_frame, text="No FAs available to delete.", foreground="red").grid(row=1, column=0, sticky='w', padx=5, pady=4)
            return
        ttk.Label(self.dynamic_frame, text="Select FA by ID and Name:").grid(row=1, column=0, sticky='w', padx=5, pady=4)
        selected_id_var = tk.StringVar()
        selected_id_combo = ttk.Combobox(self.dynamic_frame, values=fa_ids_names, textvariable=selected_id_var, state="readonly", font=("Helvetica", 14))
        selected_id_combo.grid(row=1, column=1, sticky='ew', pady=4, padx=5)

        def delete_selected_fa():
            selected_id_name = selected_id_var.get()
            if not selected_id_name:
                messagebox.showerror("Error", "Please select an FA to delete")
                logging.error("No FA selected for deletion")
                return
            selected_id = fa_id_map.get(selected_id_name)
            if not selected_id:
                messagebox.showerror("Error", "Selected FA not found")
                logging.error(f"FA with ID {selected_id_name} not found for deletion")
                return
            fa = next((f for f in self.fas if f.id == selected_id), None)
            if not fa:
                messagebox.showerror("Error", "Selected FA not found")
                logging.error(f"FA with ID {selected_id} not found for deletion")
                return
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete FA '{fa.name}' (ID: {fa.id})?")
            if confirm:
                try:
                    logging.info(f"Deleting FA with ID {selected_id}")
                    self.db.delete_fa(selected_id)
                    logging.info(f"Loading FAs after deleting {selected_id}")
                    self.fas = self.db.load_all_fas()
                    messagebox.showinfo("Success", f"FA '{fa.name}' (ID: {fa.id}) deleted")
                    logging.info(f"FA {selected_id} deleted successfully")
                    self.delete_fa_ui()  # Refresh UI to update combobox
                except sqlite3.Error as e:
                    logging.error(f"Database error deleting FA {selected_id}: {str(e)}")
                    messagebox.showerror("Error", f"Failed to delete FA: {str(e)}")
                except Exception as e:
                    logging.error(f"Error deleting FA {selected_id}: {str(e)}")
                    messagebox.showerror("Error", f"Failed to delete FA: {str(e)}")

        ttk.Button(self.dynamic_frame, text="Delete FA", command=delete_selected_fa, style='Danger.TButton').grid(row=2, column=0, columnspan=2, pady=8, padx=5)

    def show_fa_ui(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Show Finite Automaton Structure", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        fa_ids_names = [f"{fa.id} - {fa.name}" for fa in self.fas]
        fa_id_map = {f"{fa.id} - {fa.name}": fa.id for fa in self.fas}
        if not fa_ids_names:
            ttk.Label(self.dynamic_frame, text="No FAs available.", foreground="red").grid(row=1, column=0, sticky='w', padx=5, pady=4)
            return
        ttk.Label(self.dynamic_frame, text="Select FA by ID and Name:").grid(row=1, column=0, sticky='w', padx=5, pady=4)
        selected_id_var = tk.StringVar()
        selected_id_combo = ttk.Combobox(self.dynamic_frame, values=fa_ids_names, textvariable=selected_id_var, state="readonly", font=("Helvetica", 14))
        selected_id_combo.grid(row=1, column=1, sticky='ew', pady=4, padx=5)
        output_text = tk.Text(self.dynamic_frame, height=20, font=("Consolas", 12))
        output_text.grid(row=2, column=0, columnspan=2, pady=10, sticky='nsew')

        def display_fa():
            selected_id_name = selected_id_var.get()
            if not selected_id_name:
                messagebox.showerror("Error", "Please select an FA to show")
                logging.error("No FA selected for display")
                return
            selected_id = fa_id_map.get(selected_id_name)
            if not selected_id:
                messagebox.showerror("Error", "Selected FA not found")
                logging.error(f"FA with ID {selected_id_name} not found for display")
                return
            fa = next((f for f in self.fas if f.id == selected_id), None)
            if not fa:
                messagebox.showerror("Error", "Selected FA not found")
                logging.error(f"FA with ID {selected_id} not found for display")
                return
            logging.info(f"Displaying FA with ID {selected_id}")
            output_text.delete(1.0, tk.END)
            output_text.insert(tk.END, f"ID: {fa.id}\n")
            output_text.insert(tk.END, f"Name: {fa.name}\n")
            output_text.insert(tk.END, f"Type: {fa.fa_type}\n")
            output_text.insert(tk.END, f"States: {fa.states}\n")
            output_text.insert(tk.END, f"Alphabet: {fa.alphabet}\n")
            output_text.insert(tk.END, f"Start State: {fa.start_state}\n")
            output_text.insert(tk.END, f"Final States: {fa.final_states}\n")
            output_text.insert(tk.END, "Transitions:\n")
            for state, trans in fa.transitions.items():
                output_text.insert(tk.END, f"  {state}:\n")
                for sym, tgt in trans.items():
                    output_text.insert(tk.END, f"    {sym} -> {', '.join(tgt) if isinstance(tgt, list) else tgt}\n")

        ttk.Button(self.dynamic_frame, text="Show FA", command=display_fa, style='Category.TButton').grid(row=3, column=0, columnspan=2, pady=8, padx=5)
        self.dynamic_frame.rowconfigure(2, weight=1)

    def show_simulate_options(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Simulate and Analyze FA", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        self.dynamic_frame.columnconfigure(0, weight=1)
        button_frame = ttk.Frame(self.dynamic_frame)
        button_frame.grid(row=1, column=0, pady=10)
        ttk.Button(button_frame, text="Test Input String", command=self.simulate_ui, style='Category.TButton').pack(side=tk.LEFT, padx=5, pady=8)
        ttk.Button(button_frame, text="Check FA Type (DFA/NFA)", command=self.check_type_ui, style='Success.TButton').pack(side=tk.LEFT, padx=5, pady=8)

    def simulate_ui(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Test Input String on FA", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        fa_ids_names = [f"{fa.id} - {fa.name}" for fa in self.fas]
        fa_id_map = {f"{fa.id} - {fa.name}": fa.id for fa in self.fas}
        if not fa_ids_names:
            ttk.Label(self.dynamic_frame, text="No FAs available.", foreground="red").grid(row=1, column=0, sticky='w', padx=5, pady=4)
            return
        ttk.Label(self.dynamic_frame, text="Select FA by ID and Name:").grid(row=1, column=0, sticky='w', padx=5, pady=4)
        selected_id_var = tk.StringVar()
        selected_id_combo = ttk.Combobox(self.dynamic_frame, values=fa_ids_names, textvariable=selected_id_var, state="readonly", font=("Helvetica", 14))
        selected_id_combo.grid(row=1, column=1, sticky='ew', pady=4, padx=5)
        ttk.Label(self.dynamic_frame, text="Input String:").grid(row=2, column=0, sticky='w', padx=5, pady=4)
        input_str_var = tk.StringVar()
        input_str_entry = ttk.Entry(self.dynamic_frame, textvariable=input_str_var, font=("Helvetica", 14))
        input_str_entry.grid(row=2, column=1, sticky='ew', pady=4, padx=5)
        output_label = ttk.Label(self.dynamic_frame, text="", font=("Helvetica", 14))
        output_label.grid(row=3, column=0, columnspan=2, pady=10, sticky='ew')

        def run_simulation():
            selected_id_name = selected_id_var.get()
            if not selected_id_name:
                messagebox.showerror("Error", "Please select an FA")
                logging.error("No FA selected for simulation")
                return
            fa_id = fa_id_map.get(selected_id_name)
            if not fa_id:
                messagebox.showerror("Error", "Selected FA not found")
                logging.error(f"FA with ID {selected_id_name} not found for simulation")
                return
            input_str = input_str_var.get()
            fa = next((f for f in self.fas if f.id == fa_id), None)
            if not fa:
                messagebox.showerror("Error", "FA not found")
                logging.error(f"FA with ID {fa_id} not found for simulation")
                return
            try:
                logging.info(f"Simulating input '{input_str}' on FA {fa_id}")
                accepted = fa.simulate(input_str)
                result = "ACCEPTED" if accepted else "REJECTED"
                output_label.config(text=f"Result: {result}")
                self.db.save_input_test(fa_id, input_str, accepted)
                logging.info(f"Simulation result for {fa_id}: {result}")
            except Exception as e:
                logging.error(f"Simulation error for {fa_id}: {str(e)}")
                messagebox.showerror("Error", f"Simulation error: {str(e)}")

        ttk.Button(self.dynamic_frame, text="Simulate", command=run_simulation, style='Category.TButton').grid(row=4, column=0, columnspan=2, pady=8, padx=5)

    def check_type_ui(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Check if FA is DFA or NFA", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        fa_ids_names = [f"{fa.id} - {fa.name}" for fa in self.fas]
        fa_id_map = {f"{fa.id} - {fa.name}": fa.id for fa in self.fas}
        if not fa_ids_names:
            ttk.Label(self.dynamic_frame, text="No FAs available.", foreground="red").grid(row=1, column=0, sticky='w', padx=5, pady=4)
            return
        ttk.Label(self.dynamic_frame, text="Select FA by ID and Name:").grid(row=1, column=0, sticky='w', padx=5, pady=4)
        selected_id_var = tk.StringVar()
        selected_id_combo = ttk.Combobox(self.dynamic_frame, values=fa_ids_names, textvariable=selected_id_var, state="readonly", font=("Helvetica", 14))
        selected_id_combo.grid(row=1, column=1, sticky='ew', pady=4, padx=5)
        output_label = ttk.Label(self.dynamic_frame, text="", font=("Helvetica", 14))
        output_label.grid(row=2, column=0, columnspan=2, pady=10, sticky='ew')

        def check_type():
            selected_id_name = selected_id_var.get()
            if not selected_id_name:
                messagebox.showerror("Error", "Please select an FA")
                logging.error("No FA selected for type check")
                return
            fa_id = fa_id_map.get(selected_id_name)
            if not fa_id:
                messagebox.showerror("Error", "Selected FA not found")
                logging.error(f"FA with ID {selected_id_name} not found for type check")
                return
            fa = next((f for f in self.fas if f.id == fa_id), None)
            if not fa:
                messagebox.showerror("Error", "FA not found")
                logging.error(f"FA with ID {fa_id} not found for type check")
                return
            try:
                logging.info(f"Checking type for FA {fa_id}")
                is_dfa = fa.is_dfa()
                output_label.config(text="This FA is a DFA." if is_dfa else "This FA is an NFA.")
                logging.info(f"FA {fa_id} is {'DFA' if is_dfa else 'NFA'}")
            except Exception as e:
                logging.error(f"Error checking type for {fa_id}: {str(e)}")
                messagebox.showerror("Error", f"Error checking FA type: {str(e)}")

        ttk.Button(self.dynamic_frame, text="Check Type", command=check_type, style='Category.TButton').grid(row=3, column=0, columnspan=2, pady=8, padx=5)

    def show_conversion_options(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Optimize Finite Automata", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        self.dynamic_frame.columnconfigure(0, weight=1)
        button_frame = ttk.Frame(self.dynamic_frame)
        button_frame.grid(row=1, column=0, pady=10)
        ttk.Button(button_frame, text="Convert NFA to DFA", command=self.convert_ui, style='Category.TButton').pack(side=tk.LEFT, padx=5, pady=8)
        ttk.Button(button_frame, text="Minimize DFA", command=self.minimize_ui, style='Success.TButton').pack(side=tk.LEFT, padx=5, pady=8)

    def convert_ui(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Convert NFA to DFA", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        fa_ids_names = [f"{fa.id} - {fa.name}" for fa in self.fas if not fa.is_dfa()]
        fa_id_map = {f"{fa.id} - {fa.name}": fa.id for fa in self.fas if not fa.is_dfa()}
        if not fa_ids_names:
            ttk.Label(self.dynamic_frame, text="No NFAs available for conversion.", foreground="red").grid(row=1, column=0, sticky='w', padx=5, pady=4)
            return
        ttk.Label(self.dynamic_frame, text="Select NFA by ID and Name:").grid(row=1, column=0, sticky='w', padx=5, pady=4)
        selected_id_var = tk.StringVar()
        selected_id_combo = ttk.Combobox(self.dynamic_frame, values=fa_ids_names, textvariable=selected_id_var, state="readonly", font=("Helvetica", 14))
        selected_id_combo.grid(row=1, column=1, sticky='ew', pady=4, padx=5)
        output_text = tk.Text(self.dynamic_frame, height=20, font=("Consolas", 12))
        output_text.grid(row=2, column=0, columnspan=2, pady=10, sticky='nsew')

        def convert_nfa():
            selected_id_name = selected_id_var.get()
            if not selected_id_name:
                messagebox.showerror("Error", "Please select an NFA")
                logging.error("No NFA selected for conversion")
                return
            fa_id = fa_id_map.get(selected_id_name)
            if not fa_id:
                messagebox.showerror("Error", "Selected NFA not found")
                logging.error(f"NFA with ID {selected_id_name} not found for conversion")
                return
            fa = next((f for f in self.fas if f.id == fa_id), None)
            if not fa:
                messagebox.showerror("Error", "NFA not found")
                logging.error(f"NFA with ID {fa_id} not found for conversion")
                return
            if fa.is_dfa():
                messagebox.showerror("Error", f"FA '{fa.name}' (ID: {fa_id}) is already a DFA")
                logging.error(f"FA {fa_id} is already a DFA")
                return
            if not fa.states or not fa.start_state:
                messagebox.showerror("Error", f"NFA '{fa.name}' (ID: {fa_id}) is invalid (missing states or start state)")
                logging.error(f"Invalid NFA {fa_id}: No states or start state")
                return
            try:
                logging.info(f"Starting NFA to DFA conversion for {fa_id}")
                new_id = self.db.generate_next_fa_id()
                logging.info(f"Generated new ID {new_id} for DFA")
                # Extract numeric part of ID for id_counter
                id_counter = int(new_id.replace("FA", "") if new_id.startswith("FA") else new_id)
                dfa = fa.to_dfa(id_prefix="FA", id_counter=id_counter, db=self.db)
                if not dfa.states or not dfa.start_state:
                    raise ValueError("Conversion produced an invalid DFA (empty states or start state)")
                logging.info(f"Saving DFA with ID {dfa.id}")
                self.db.save_fa(dfa)
                logging.info(f"Saving conversion record: source={fa_id}, result={dfa.id}")
                self.db.save_conversion(fa_id, dfa.id, "NFA_TO_DFA")
                logging.info(f"Loading FAs after conversion")
                self.fas = self.db.load_all_fas()
                output_text.delete(1.0, tk.END)
                output_text.insert(tk.END, f"Converted DFA:\n")
                output_text.insert(tk.END, f"ID: {dfa.id}\n")
                output_text.insert(tk.END, f"Name: {dfa.name}\n")
                output_text.insert(tk.END, f"Type: {dfa.fa_type}\n")
                output_text.insert(tk.END, f"States: {dfa.states}\n")
                output_text.insert(tk.END, f"Alphabet: {dfa.alphabet}\n")
                output_text.insert(tk.END, f"Start State: {dfa.start_state}\n")
                output_text.insert(tk.END, f"Final States: {dfa.final_states}\n")
                output_text.insert(tk.END, "Transitions:\n")
                for state, trans in dfa.transitions.items():
                    output_text.insert(tk.END, f"  {state}:\n")
                    for sym, tgt in trans.items():
                        output_text.insert(tk.END, f"    {sym} -> {', '.join(tgt) if isinstance(tgt, list) else tgt}\n")
                messagebox.showinfo("Success", f"Converted DFA saved with ID {dfa.id}")
                logging.info(f"Conversion successful: DFA {dfa.id} created")
            except sqlite3.Error as e:
                logging.error(f"Database error during conversion for {fa_id}: {str(e)}")
                messagebox.showerror("Error", f"Database error during conversion: {str(e)}")
            except Exception as e:
                logging.error(f"Conversion error for {fa_id}: {str(e)}")
                messagebox.showerror("Error", f"Conversion error: {str(e)}")

        ttk.Button(self.dynamic_frame, text="Convert to DFA", command=convert_nfa, style='Category.TButton').grid(row=3, column=0, columnspan=2, pady=8, padx=5)
        self.dynamic_frame.rowconfigure(2, weight=1)

    def minimize_ui(self):
        self.clear_dynamic_frame()
        ttk.Label(self.dynamic_frame, text="Minimize DFA", font=("Helvetica", 18, 'bold')).grid(row=0, column=0, pady=10)
        fa_ids_names = [f"{fa.id} - {fa.name}" for fa in self.fas if fa.is_dfa()]
        fa_id_map = {f"{fa.id} - {fa.name}": fa.id for fa in self.fas if fa.is_dfa()}
        if not fa_ids_names:
            ttk.Label(self.dynamic_frame, text="No DFAs available for minimization.", foreground="red").grid(row=1, column=0, sticky='w', padx=5, pady=4)
            return
        ttk.Label(self.dynamic_frame, text="Select DFA by ID and Name:").grid(row=1, column=0, sticky='w', padx=5, pady=4)
        selected_id_var = tk.StringVar()
        selected_id_combo = ttk.Combobox(self.dynamic_frame, values=fa_ids_names, textvariable=selected_id_var, state="readonly", font=("Helvetica", 14))
        selected_id_combo.grid(row=1, column=1, sticky='ew', pady=4, padx=5)
        output_text = tk.Text(self.dynamic_frame, height=20, font=("Consolas", 12))
        output_text.grid(row=2, column=0, columnspan=2, pady=10, sticky='nsew')

        def minimize_dfa():
            selected_id_name = selected_id_var.get()
            if not selected_id_name:
                messagebox.showerror("Error", "Please select a DFA")
                logging.error("No DFA selected for minimization")
                return
            fa_id = fa_id_map.get(selected_id_name)
            if not fa_id:
                messagebox.showerror("Error", "Selected DFA not found")
                logging.error(f"DFA with ID {selected_id_name} not found for minimization")
                return
            fa = next((f for f in self.fas if f.id == fa_id), None)
            if not fa:
                messagebox.showerror("Error", "DFA not found")
                logging.error(f"DFA with ID {fa_id} not found for minimization")
                return
            try:
                logging.info(f"Starting DFA minimization for {fa_id}")
                new_id = self.db.generate_next_fa_id()
                logging.info(f"Generated new ID {new_id} for minimized DFA")
                # Extract numeric part of ID for id_counter
                id_counter = int(new_id.replace("FA", "") if new_id.startswith("FA") else new_id)
                minimized = fa.minimize(id_prefix="FA", id_counter=id_counter, db=self.db)
                logging.info(f"Saving minimized DFA with ID {minimized.id}")
                self.db.save_fa(minimized)
                logging.info(f"Saving conversion record: source={fa_id}, result={minimized.id}")
                self.db.save_conversion(fa_id, minimized.id, "DFA_MINIMIZATION")
                logging.info(f"Loading FAs after minimization")
                self.fas = self.db.load_all_fas()
                output_text.delete(1.0, tk.END)
                output_text.insert(tk.END, f"Minimized DFA:\n")
                output_text.insert(tk.END, f"ID: {minimized.id}\n")
                output_text.insert(tk.END, f"Name: {minimized.name}\n")
                output_text.insert(tk.END, f"Type: {minimized.fa_type}\n")
                output_text.insert(tk.END, f"States: {minimized.states}\n")
                output_text.insert(tk.END, f"Alphabet: {minimized.alphabet}\n")
                output_text.insert(tk.END, f"Start State: {minimized.start_state}\n")
                output_text.insert(tk.END, f"Final States: {minimized.final_states}\n")
                output_text.insert(tk.END, "Transitions:\n")
                for state, trans in minimized.transitions.items():
                    output_text.insert(tk.END, f"  {state}:\n")
                    for sym, tgt in trans.items():
                        output_text.insert(tk.END, f"    {sym} -> {', '.join(tgt) if isinstance(tgt, list) else tgt}\n")
                messagebox.showinfo("Success", f"Minimized DFA saved with ID {minimized.id}")
                logging.info(f"Minimization successful: DFA {minimized.id} created")
            except sqlite3.Error as e:
                logging.error(f"Database error during minimization for {fa_id}: {str(e)}")
                messagebox.showerror("Error", f"Database error during minimization: {str(e)}")
            except Exception as e:
                logging.error(f"Minimization error for {fa_id}: {str(e)}")
                messagebox.showerror("Error", f"Minimization error: {str(e)}")

        ttk.Button(self.dynamic_frame, text="Minimize DFA", command=minimize_dfa, style='Category.TButton').grid(row=3, column=0, columnspan=2, pady=8, padx=5)
        self.dynamic_frame.rowconfigure(2, weight=1)

if __name__ == '__main__':
    root = tk.Tk()
    app = FAApp(root)
    root.mainloop()
