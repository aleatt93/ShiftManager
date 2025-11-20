import calendar
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import datetime
import library
import file_manager
from exporter import Exporter

FILE_VERSION = "1.0"

WEEKDAYS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
MONTHS = [0, "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto",
          "Settembre", "Ottobre", "Novembre", "Dicembre"]


class ShiftManagerGui(tk.Tk):
    class Tooltip:
        """Consente di generare label temporanee quando si porta il cursore su un certo widget."""

        def __init__(self, widget, text):
            self.widget = widget
            self.text = text
            self.tooltip_window = None

            self.widget.bind("<Enter>", self.show_tooltip)
            self.widget.bind("<Leave>", self.hide_tooltip)

        def show_tooltip(self, event):
            # If a tooltip already exists do nothing
            if self.tooltip_window:
                return

            # Storage delle coordinate del widget
            tooltip_coord_x = self.widget.winfo_rootx() + 20
            tooltip_coord_y = self.widget.winfo_rooty() - 20

            # Creazione di una finestra Toplevel, rimozione delle decorazioni e posizionamento della finestra su schermo
            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{tooltip_coord_x}+{tooltip_coord_y}")

            # Aggiunta della label all'oggetto Toplevel
            label = tk.Label(
                self.tooltip_window,
                text=self.text,
                background="#FFFFE0",
                relief="solid",
                borderwidth=1
            )
            label.pack()

        def hide_tooltip(self, event):
            if self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None  # Reset della variabile

    class ScheduleTable(ttk.Frame):
        """A custom widget that encapsulates a Treeview for displaying the shift schedule.
            It manages its own scrollbars, columns, and data population logic."""

        def __init__(self, parent_frame, employees_list, configuration):
            super().__init__(parent_frame)

            self.emp_list = employees_list
            self.configuration = configuration
            self.SHIFTS_CORRISPONDANCE = self.configuration["shift_settings"]["shift_representation"]

            # Style object
            style = ttk.Style(self)
            style.configure(
                "Treeview.Heading",
                font=(None, 10, "bold")
            )

            # Creazione oggetto Treeview
            self.schedule_table = ttk.Treeview(self, show="headings")

            # Inserimento widget nel frame tramite .grid()
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=1)
            self.schedule_table.grid(row=0, column=0, sticky="nsew")

            # Generazione scrollbar
            self._scrollbar_setting()

            # Bind click event
            self.schedule_table.bind("<Button-1>", self._on_click)

        def _on_click(self, event):
            """Gestisce il click sulla cella per assegnare manualmente un turno."""
            region = self.schedule_table.identify("region", event.x, event.y)
            if region != "cell":
                return

            # Identifica riga e colonna
            row_id = self.schedule_table.identify_row(event.y)
            column_id = self.schedule_table.identify_column(event.x)

            if not row_id or not column_id:
                return

            # Verifica che la colonna sia un giorno (es. "day_1", "day_2"...)
            # column_id è tipo "#1", "#2"... bisogna convertirlo in indice o nome colonna
            col_index = int(column_id.replace("#", "")) - 1 # 0-based index
            col_name = self.schedule_table["columns"][col_index]

            if not col_name.startswith("day_"):
                return

            # Recupera dati impiegato
            row_values = self.schedule_table.item(row_id, "values")
            serial_number = row_values[0]
            
            # Trova l'oggetto Employee
            employee = next((emp for emp in self.emp_list if emp.serial_number == serial_number), None)
            if not employee:
                return

            # Calcola la data
            day_number = int(col_name.split("_")[1])
            # Per ottenere anno e mese bisogna accedere al parent (ShiftManagerGui) o passarli
            # Qui accediamo tramite master.master... o meglio, salviamo year/month in populate
            if not hasattr(self, "current_year") or not hasattr(self, "current_month"):
                return
            
            current_date = datetime.date(self.current_year, self.current_month, day_number)
            
            # Coordinate cella per posizionare la Combobox
            x, y, width, height = self.schedule_table.bbox(row_id, column_id)
            
            # Valori possibili
            values = ["", "M", "P", "M+R", "R", "X"]
            
            # Creazione Combobox
            combobox = ttk.Combobox(self.schedule_table, values=values, state="readonly")
            combobox.place(x=x, y=y, width=width, height=height)
            
            # Setta valore corrente
            current_val = row_values[col_index]
            if current_val in values:
                combobox.set(current_val)
            
            def on_select(event):
                selected_val = combobox.get()
                combobox.destroy()
                self._on_shift_selected(employee, current_date, selected_val, row_id, col_index)

            combobox.bind("<<ComboboxSelected>>", on_select)
            combobox.bind("<FocusOut>", lambda e: combobox.destroy())
            combobox.focus_set()
            combobox.event_generate("<Button-1>") # Apre il menu a tendina

        def _on_shift_selected(self, employee, date_obj, new_val, row_id, col_index):
            """Callback quando viene selezionato un valore dalla Combobox."""
            
            # Aggiorna i dati nel backend (locked_shifts e days_off) e i contatori
            # Necessario riferimento alla GUI principale per locked_shifts
            main_gui = self.winfo_toplevel()
            
            # Chiave per locked_shifts
            lock_key = (date_obj.isoformat(), employee.id)
            
            # 1. Rimuovi stato precedente
            # Se era OFF DUTY
            if date_obj in employee.days_off:
                employee.days_off.remove(date_obj)
            
            # Se era LOCKED SHIFT (o turno generato, ma qui gestiamo manual overrides)
            # Se c'è un lock precedente, decrementiamo il contatore
            if lock_key in main_gui.locked_shifts:
                prev_shift = main_gui.locked_shifts[lock_key]
                # self._update_shift_count(employee, prev_shift, -1) # Removed to avoid double decrement (handled by visual val)
                del main_gui.locked_shifts[lock_key]
            
            # NOTA: Se stiamo modificando una cella che aveva un turno GENERATO (non lockato),
            # dovremmo decrementare il contatore?
            # Il piano dice: "Decrement employee shift counts to 'clean' the stats for this month" PRIMA di generare.
            # Ma qui stiamo modificando "live".
            # Se modifichiamo un turno generato, visivamente cambia. Il contatore dovrebbe aggiornarsi.
            # Ma se poi rigeneriamo, tutto viene ricalcolato.
            # Per coerenza visuale immediata:
            # Recuperiamo il valore visuale precedente dalla tabella
            current_row_values = list(self.schedule_table.item(row_id, "values"))
            prev_visual_val = current_row_values[col_index]
            
            # Mappa visuale -> chiave contatore
            # M -> mattina, P -> pomeriggio, M+R -> mattina_rep, R -> weekend_rep
            shift_map = {v: k for k, v in self.SHIFTS_CORRISPONDANCE.items()}
            
            if prev_visual_val in shift_map and prev_visual_val != "X":
                 # Se non era un lock (già gestito sopra), decrementiamo comunque per coerenza visuale
                 # Se era un lock, l'abbiamo già decrementato sopra?
                 # Attenzione ai doppi decrementi.
                 # Se era in locked_shifts, abbiamo decrementato.
                 # Se NON era in locked_shifts, ma era visualizzato, era un turno generato.
                 # Dobbiamo decrementare anche quello.
                 if lock_key not in main_gui.locked_shifts: # Se l'abbiamo appena tolto, era in locked.
                     # Se siamo qui, lock_key NON era in locked_shifts PRIMA (o l'abbiamo tolto).
                     # Ma aspetta, ho rimosso da locked_shifts poche righe sopra.
                     # Quindi devo sapere se era lockato PRIMA di rimuoverlo.
                     pass
            
            # Semplificazione: Usiamo il valore visuale per decrementare.
            # Se il valore visuale corrisponde a un turno, decrementiamo.
            if prev_visual_val == "X":
                pass # Già rimosso da days_off sopra se c'era
            elif prev_visual_val in shift_map:
                 shift_type = shift_map[prev_visual_val]
                 # Decrementiamo SOLO se non l'abbiamo già fatto rimuovendo il lock?
                 # No, il contatore è unico. Se era lockato o generato, il contatore è su.
                 # Quindi decrementiamo SEMPRE basandoci su cosa c'era.
                 # MA: se rimuoviamo da locked_shifts sopra, non dobbiamo decrementare due volte.
                 # Soluzione: Ignorare la logica sopra per i contatori e fare tutto basandosi sul visuale.
                 # L'unica cosa "logica" da fare sopra è pulire locked_shifts e days_off.
                 self._update_shift_count(employee, shift_type, -1)

            # 2. Applica nuovo stato
            if new_val == "X":
                if date_obj not in employee.days_off:
                    employee.days_off.append(date_obj)
            elif new_val in shift_map:
                shift_type = shift_map[new_val]
                main_gui.locked_shifts[lock_key] = shift_type
                self._update_shift_count(employee, shift_type, 1)
            
            # 3. Aggiorna UI
            current_row_values[col_index] = new_val
            self.schedule_table.item(row_id, values=current_row_values)
            
            # Aggiorna tabella impiegati
            if hasattr(main_gui, "employees_table_manager"):
                main_gui.employees_table_manager.employees_populate_table()

        def _update_shift_count(self, employee, shift_type, delta):
            if shift_type in employee.shift_count:
                employee.shift_count[shift_type] += delta
            elif shift_type == "off_duty":
                pass # Non c'è contatore per off_duty

        def _scrollbar_setting(self):
            """Genera e setta le scrollbar verticale e orizzontale della tabella shift schedule"""
            scrollbar_v = ttk.Scrollbar(
                self,
                orient="vertical",
                command=self.schedule_table.yview
            )
            scrollbar_h = ttk.Scrollbar(
                self,
                orient="horizontal",
                command=self.schedule_table.xview
            )
            self.schedule_table.configure(
                yscrollcommand=scrollbar_v.set,
                xscrollcommand=scrollbar_h.set
            )

            scrollbar_v.grid(row=0, column=1, sticky="ns")
            scrollbar_h.grid(row=1, column=0, sticky="ew")

        def clear(self):
            """Rimuove tutte le colonne e i dati da Treeview"""
            self.schedule_table.delete(*self.schedule_table.get_children())
            self.schedule_table["columns"] = ()

        def schedule_populate_table(self, schedule_data, year: int, month: int):
            """Clears the table and fills it with the schedule for a given month.
            :param schedule_data: The dictionary of shifts for the month (from shift_storage.json).
            :param year: anno di riferimento per la creazione della tabella
            :param month: mese di riferimento per la creazione della tabella"""

            self.clear()  # Cancella tutto per poi inserire i dati
            
            # Salva anno e mese correnti per gestione click
            self.current_year = year
            self.current_month = month

            # Definizione del numero di colonne necessarie in base al mese selezionato
            number_of_days = calendar.monthrange(year, month)[1]
            schedule_table_columns_headers = (
                    ["serial_number", "surname", "name"] + [f"day_{d}" for d in range(1, number_of_days + 1)]
            )
            self.schedule_table["columns"] = schedule_table_columns_headers

            # Configurazione proprietà delle colonne
            self.schedule_table.heading("serial_number", text="Matricola", anchor="center")
            self.schedule_table.heading("surname", text="Cognome", anchor="center")
            self.schedule_table.heading("name", text="Nome", anchor="center")
            self.schedule_table.column("serial_number", width=100, anchor="center", stretch=False)
            self.schedule_table.column("surname", width=100, anchor="center", stretch=False)
            self.schedule_table.column("name", width=100, anchor="center", stretch=False)

            for day in range(1, number_of_days + 1):
                col_id = f"day_{day}"
                day_name = WEEKDAYS[datetime.date(year, month, day).weekday()]
                self.schedule_table.heading(col_id, text=f"{day_name} {day}", anchor="n")
                self.schedule_table.column(col_id, width=60, anchor="center", stretch=False)

            for employee in self.emp_list:
                row_values = [employee.serial_number, employee.surname, employee.name]
                for day in range(1, number_of_days + 1):
                    current_date = datetime.date(year, month, day)
                    day_key_str_format = current_date.isoformat()
                    shift_text = ""  # Default to blank

                    # Check se employee è off-duty
                    if current_date in employee.days_off:
                        shift_text = self.SHIFTS_CORRISPONDANCE["off_duty"]

                    # Verifica in quale turno è inserito l'employee e inserisce la sigla del turno nell'array
                    # row_values
                    elif schedule_data and day_key_str_format in schedule_data:
                        daily_shifts = schedule_data[day_key_str_format]
                        # print(f"{day_key_str_format} - {daily_shifts.items()}")
                        if employee.id in daily_shifts["mattina_rep"]:
                            shift_text = self.SHIFTS_CORRISPONDANCE["mattina_rep"]
                        else:
                            for shift_type, emp_ids in daily_shifts.items():
                                # print(f"day: {day_key_str_format} - shift_type: {shift_type} - emp_ids {emp_ids}")
                                if employee.id in emp_ids:
                                    shift_text = self.SHIFTS_CORRISPONDANCE[shift_type]
                                    break  # Non è necessario ricercare ulteriormente una volta trovato l'employee

                    row_values.append(shift_text)

                self.schedule_table.insert("", "end", values=row_values)

    class EmployeeTable(ttk.Frame):
        """A custom widget that encapsulates a Treeview for displaying the employees list.
            It manages its own scrollbars, columns, and data population logic."""

        def __init__(self, frame, employees_list, configuration):
            super().__init__(frame)

            self.emp_list = employees_list
            self.configuration = configuration

            # Creazione oggetto Treeview
            self.employees_table = ttk.Treeview(self, show="headings")

            # Inserimento widget Treeview nel frame tramite .grid()
            self.columnconfigure(0, weight=1)  # Treeview si espande fino a riempire lo spazio disponibile
            self.rowconfigure(0, weight=1)
            self.employees_table.grid(row=0, column=0, sticky="nsew")

            # Generazione
            self._scrollbar_setting()
            self.employees_populate_table()

        def _scrollbar_setting(self):
            """Genera e setta le scrollbar verticale della tabella employees list"""

            scrollbar_v = ttk.Scrollbar(
                self,
                orient="vertical",
                command=self.employees_table.yview
            )
            self.employees_table.configure(yscrollcommand=scrollbar_v.set)
            scrollbar_v.grid(row=0, column=1, sticky="ns")

        def clear(self):
            """Rimuove tutte le colonne e i dati da Treeview"""
            self.employees_table.delete(*self.employees_table.get_children())
            self.employees_table["columns"] = ()

        def _columns_setting(self):
            """Configura le colonne della tabella"""

            # Definizione delle colonne
            employees_table_columns_headers = (
                "serial_number",
                "surname",
                "name",
                "mattina",
                "mattina_rep",
                "pomeriggio",
                "weekend_rep"
            )

            self.employees_table["columns"] = employees_table_columns_headers

            # Setting nome heading
            self.employees_table.heading("serial_number", text="Matricola")
            self.employees_table.heading("surname", text="Cognome")
            self.employees_table.heading("name", text="Nome")
            self.employees_table.heading("mattina", text="Mattina")
            self.employees_table.heading("mattina_rep", text="Mattina REP")
            self.employees_table.heading("pomeriggio", text="Pomeriggio")
            self.employees_table.heading("weekend_rep", text="Weekend REP")

            # Setting caratteristiche heading
            self.employees_table.column("serial_number", width=100, anchor="center", stretch=False)
            self.employees_table.column("surname", width=150, anchor="center", stretch=False)
            self.employees_table.column("name", width=150, anchor="center", stretch=False)
            self.employees_table.column("mattina", width=100, anchor="center", stretch=False)
            self.employees_table.column("mattina_rep", width=100, anchor="center", stretch=False)
            self.employees_table.column("pomeriggio", width=100, anchor="center", stretch=False)
            self.employees_table.column("weekend_rep", width=100, anchor="center", stretch=False)

        def employees_populate_table(self):
            """Clears and fills the table with the current employee list."""
            self.clear()  # Cancella tutto per poi inserire i dati

            self._columns_setting()  # Settaggio colonne

            # Genera valori da inserire nella riga di ciascun employee
            row_values = []
            for employee in self.emp_list:
                row_values = [
                    employee.serial_number,
                    employee.surname,
                    employee.name,
                    employee.shift_count["mattina"],
                    employee.shift_count["mattina_rep"],
                    employee.shift_count["pomeriggio"],
                    employee.shift_count["weekend_rep"]
                ]

                # Inserimento dei dati nella tabella
                self.employees_table.insert("", "end", values=row_values)

        def get_selected_employee_datas(self):
            """Returns datas (serial_number, surname, name) of the selected employee or None."""

            # IID è il numero identificativo che utilizza Treeview per identificare una certa riga di una tabella
            selected_employee_iid = self.employees_table.selection()  # -> selected_employee_iid = ["I001",]

            if not selected_employee_iid:
                return None

            selected_employee_iid = selected_employee_iid[0]  # -> selected_employee_iid = "I001"
            # print(f"selected_employee = {selected_employee}") # DEBUG

            selected_employee_serial_number, selected_employee_surname, selected_employee_name = [
                self.employees_table.item(selected_employee_iid, "values")[0],  # -> serial_number
                self.employees_table.item(selected_employee_iid, "values")[1],  # -> surname
                self.employees_table.item(selected_employee_iid, "values")[2]  # -> name
            ]

            # DEBUG
            # print(f"selected_employees_serial_number: {selected_employee_serial_number}\n"
            #       f"selected_employees_surname: {selected_employee_surname}\n"
            #       f"selected_employee_name: {selected_employee_name}")

            return selected_employee_serial_number, selected_employee_surname, selected_employee_name

    class AddEmployeeDialogWindow(tk.Toplevel):
        """Classe di gestione della finestra di dialogo per aggiungere impiegati"""

        # Callback è una funzione passata a una classe come parametro.
        # La funzione di un callback è quella di eseguire una funzione esterna alla classe
        def __init__(self, employees_list_frame, callback_add_employee):
            super().__init__(employees_list_frame)

            self.employees_list_frame = employees_list_frame  # Frame in cui è presente il frame della employees_table
            self.callback_add_employee = callback_add_employee

            self._root_setting()
            self._frame_setting()
            self._widget_setting()

            self.transient(self.employees_list_frame)  # Permette l'utilizzo della "X" per chiudere la finestra
            self.grab_set()  # Impedisce all'user di utilizzare la finestra sottostante

        def _root_setting(self):
            self._center_window()
            self.title("Aggiungi Impiegato")
            self.resizable(False, False)  # Impedisce all'user di ridimensionare la finestra

        def _center_window(self):
            """Centers the Toplevel window on the screen."""

            # This is needed to ensure that the window's dimensions are updated
            # before we try to get them.
            self.update_idletasks()

            # Storage delle dimensioni dello schermo
            screen_x = self.winfo_screenwidth()
            screen_y = self.winfo_screenheight()

            dialog_window_x = self.winfo_width()
            dialog_window_y = self.winfo_height()

            center_x = int((screen_x / 2) - (dialog_window_x / 2))
            center_y = int((screen_y / 2) - (dialog_window_y / 2))

            self.geometry(f"-{center_x}+{center_y}")

        def _frame_setting(self):
            self.frame_master = ttk.Frame(self)
            self.frame_master.pack(expand=True, fill="both")
            self.frame_master.columnconfigure((0, 1, 2), weight=1)

        def _widget_setting(self):
            # LABEL
            label_cognome = ttk.Label(self.frame_master, text="Cognome")
            label_nome = ttk.Label(self.frame_master, text="Nome")
            label_serial_number = ttk.Label(self.frame_master, text="Matricola")

            label_cognome.grid(row=0, column=0, sticky="e")
            label_nome.grid(row=1, column=0, sticky="e")
            label_serial_number.grid(row=2, column=0, sticky="e")

            # ENTRY
            self.entry_surname = ttk.Entry(self.frame_master)
            self.entry_name = ttk.Entry(self.frame_master)
            self.entry_serial_number = ttk.Entry(self.frame_master)

            self.entry_surname.grid(row=0, column=1, columnspan=2, sticky="ew", padx=10)
            self.entry_name.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10)
            self.entry_serial_number.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10)

            # BUTTON
            button_add_employee = ttk.Button(
                self.frame_master,
                text="Aggiungi",
                command=self._command_add_employee
            )
            button_clear = ttk.Button(
                self.frame_master,
                text="Cancella",
                command=self._command_clear_fields
            )
            button_close = ttk.Button(
                self.frame_master,
                text="Chiudi",
                command=self.destroy  # Chiude la finestra di dialogo
            )

            button_add_employee.grid(row=3, column=0, pady=10, padx=10)
            button_clear.grid(row=3, column=1, pady=10)
            button_close.grid(row=3, column=2, pady=10, padx=10)

        def _command_clear_fields(self):
            """Clear entry fields"""
            self.entry_surname.delete(0, "end")
            self.entry_name.delete(0, "end")
            self.entry_serial_number.delete(0, "end")
            self.entry_surname.focus_set()  # Imposta il cursore sul campo "Cognome"

        def _command_add_employee(self):
            """Validates input and closes the dialog, storing the result."""
            new_employee_surname = self.entry_surname.get().strip()
            new_employee_name = self.entry_name.get().strip()
            new_employee_serial_number = self.entry_serial_number.get().strip()

            # Input Validation
            if not (new_employee_surname and new_employee_name and new_employee_serial_number):
                messagebox.showerror("Errore", "Tutti i campi sono obbligatori", parent=self)
                return

            # Chiamata del callback -> Si invia il nuovo employee direttamente alla classe principale
            # La funzione di callback ritorna True/False per indicare GO/NOGO
            new_employee_added = self.callback_add_employee(
                new_employee_surname,
                new_employee_name,
                new_employee_serial_number
            )

            if new_employee_added:
                self._command_clear_fields()

    class InfoDialogWindow(tk.Toplevel):
        """Classe che consente di visualizare la finestra di info."""

        def __init__(self, frame_root):
            super().__init__(frame_root)

            self.frame_root = frame_root

            self._root_setting()
            self._frame_setting()
            self._widget_setting()

            self.transient(self.frame_root)  # Permette l'utilizzo della "X" per chiudere la finestra
            self.grab_set()  # Impedisce all'user di utilizzare la finestra sottostante

        def _root_setting(self):
            self._center_window()
            self.title("Info")
            # self.geometry("800x400")
            self.resizable(False, False)

        def _center_window(self):
            """Centers the Toplevel windows on the screen."""

            # This is needed to ensure that the window's dimensions are updated
            # before we try to get them.
            self.update_idletasks()

            # Storage delle dimensioni dello schermo
            screen_x = self.winfo_screenwidth()
            screen_y = self.winfo_screenheight()

            dialog_window_x = self.winfo_width()
            dialog_window_y = self.winfo_height()

            window_pos_x = int((screen_x / 2) - dialog_window_x)
            window_pos_y = int(screen_y * 0.25)

            self.geometry(f"-{window_pos_x}-{window_pos_y}")

        def _frame_setting(self):
            self.frame_info_master = ttk.Frame(self)
            self.frame_info_master.pack(expand=True, fill="both")
            self.frame_info_master.rowconfigure(2, weight=1)
            self.frame_info_master.columnconfigure(0, weight=1)

        def _widget_setting(self):
            text_header = f"Descrizione parametri in config.json"
            text_introduction = (
                "E' possibile modificare alcune informazioni tramite modifica del file config.json. "
                "Per modificare il file aprirlo con il blocco note.\n"
            )

            text_year_range = "year_range"
            text_year_range_description = (
                "Consente di modificare il range di anni visualizzati nella finestra 'Turni'.\n"
                )

            text_shift_representation = "shift_representation"
            text_shift_representation_description = (
                "Consente di modificare in che modo i turni vengono rappresentati nella tabella.\n"
            )

            text_n_of_employees = "n_of_employees"
            text_n_of_employees_description = (
                "Consente di indicare quanti impiegati assegnare in reperibilità la mattina\n"
                "ed il fine settimana. Il testo deve essere inserito tra virgolette ('" "').\n"
            )

            text_weekend_days = "weekend_days"
            text_weekend_days_description = (
                "Consente di indicare quali giorni sono da considerare come weekend.\n"
                "Il numero deve essere sempre seguito da una virgola, ad eccezione "
                " dell'ultimo numero.\n"
                "1: LUNEDI\n"
                "2: MARTEDI\n"
                "3: MERCOLEDI\n"
                "4: GIOVEDI\n"
                "5: VENERDI\n"
                "6: SABATO\n"
                "7: DOMENICA."
            )

            # Custom style setting for header
            style_header = ttk.Style(self)
            style_header.configure(
                style="Header.TLabel",
                font=("Helvetica", 12, "bold")
            )

            label_heading = ttk.Label(
                master=self.frame_info_master,
                text=text_header,
                style="Header.TLabel",
                anchor="center",
                padding=(0, 10)  # Applies 10 pixel of padding (Left-Right, Top-Bottom)
            )

            separator_top = ttk.Separator(
                master=self.frame_info_master,
                orient="horizontal"
            )

            label_text_introduction = ttk.Label(
                master=self.frame_info_master,
                text=text_introduction,
                anchor="center"
            )
            
            label_text_param_1 = ttk.Label(
                master=self.frame_info_master,
                text=text_year_range,
                anchor="ne"
            )
            
            label_text_param_1_description = ttk.Label(
                master=self.frame_info_master,
                text=text_year_range_description,
                anchor="nw"
            )

            label_text_param_2 = ttk.Label(
                master=self.frame_info_master,
                text=text_shift_representation,
                anchor="ne"
            )

            label_text_param_2_description = ttk.Label(
                master=self.frame_info_master,
                text=text_shift_representation_description,
                anchor="nw"
            )

            label_text_param_3 = ttk.Label(
                master=self.frame_info_master,
                text=text_n_of_employees,
                anchor="ne"
            )

            label_text_param_3_description = ttk.Label(
                master=self.frame_info_master,
                text=text_n_of_employees_description,
                anchor="nw"
            )

            label_text_param_4 = ttk.Label(
                master=self.frame_info_master,
                text=text_weekend_days,
                anchor="ne"
            )

            label_text_param_4_description = ttk.Label(
                master=self.frame_info_master,
                text=text_weekend_days_description,
                anchor="nw"
            )

            separator_bottom = ttk.Separator(
                master=self.frame_info_master,
                orient="horizontal"
            )

            button_exit = ttk.Button(
                master=self.frame_info_master,
                text="Chiudi",
                command=self.destroy
            )

            label_heading.grid(row=0, column=0, columnspan= 2, sticky="ew")
            separator_top.grid(row=1, column=0, columnspan= 2, sticky="ew", pady=5, padx=50)
            label_text_introduction.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5, padx=50)
            label_text_param_1.grid(row=3, column=0, sticky="nsew", pady=5, padx=50)
            label_text_param_1_description.grid(row=3, column=1, sticky="nsew", pady=5, padx=50)
            label_text_param_2.grid(row=4, column=0, sticky="nsew", pady=5, padx=50)
            label_text_param_2_description.grid(row=4, column=1, sticky="nsew", pady=5, padx=50)
            label_text_param_3.grid(row=5, column=0, sticky="nsew", pady=5, padx=50)
            label_text_param_3_description.grid(row=5, column=1, sticky="nsew", pady=5, padx=50)
            label_text_param_4.grid(row=6, column=0, sticky="nsew", pady=5, padx=50)
            label_text_param_4_description.grid(row=6, column=1, sticky="nsew", pady=5, padx=50)
            separator_bottom.grid(row=7, column=0, columnspan=2, sticky="ew", pady=5, padx=50)
            button_exit.grid(row=8, column=0, columnspan=2, pady=10)

    class AboutDialogWindow(tk.Toplevel):
        """Classe che consente di visualizare la finestra di about."""

        def __init__(self, frame_root):
            super().__init__(frame_root)

            self.frame_root = frame_root

            self._root_setting()
            self._frame_setting()
            self._widget_setting()

            self.transient(self.frame_root)  # Permette l'utilizzo della "X" per chiudere la finestra
            self.grab_set()  # Impedisce all'user di utilizzare la finestra sottostante

        def _root_setting(self):
            self._center_window()
            self.title("About")
            # self.geometry("400x600")
            self.resizable(False, False)

        def _center_window(self):
            """Centers the Toplevel windows on the screen."""

            # This is needed to ensure that the window's dimensions are updated
            # before we try to get them.
            self.update_idletasks()

            # Storage delle dimensioni dello schermo
            screen_x = self.winfo_screenwidth()
            screen_y = self.winfo_screenheight()

            dialog_window_x = self.winfo_width()
            dialog_window_y = self.winfo_height()

            window_pos_x = int((screen_x / 2) - dialog_window_x)
            window_pos_y = int(screen_y * 0.25)

            self.geometry(f"-{window_pos_x}-{window_pos_y}")

        def _frame_setting(self):
            self.frame_about_master = ttk.Frame(self)
            self.frame_about_master.pack(expand=True, fill="both")
            self.frame_about_master.rowconfigure(2, weight=1)
            self.frame_about_master.columnconfigure(0, weight=1)

        def _widget_setting(self):
            text_header = f"Shift Manager v{FILE_VERSION}"
            text_body = (
                "Shift Manager is a desktop application designed to simplify and automate\n "
                "the process of employee shift scheduling.\n\n"

                "This software was developed with passion by Attura Alessio.\n"
                "A special acknowledgment to Nicastro Sara,\n"
                "whose hard work and dedication inspired this project.\n\n"

                "--- NOTICE ---\n"
                "Copyright © 2024 Attura Alessio. All rights reserved.\n\n"

                "This software is the proprietary property of the author and is licensed for\n"
                "personal, non-commercial use only. You may not distribute, modify, or\n"
                "sell this software without the express written permission of the author.\n\n"

                "This software is provided 'AS IS', WITHOUT WARRANTY\n"
                "OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT\n"
                "LIMITED TO THE WARRANTIES OF MERCHANTABILITY\n"
                "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.\n"
                "IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE\n"
                "LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER\n"
                "IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
                "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR\n"
                "OTHER DEALINGS IN THE SOFTWARE"
            )

            # Custom style setting for header
            style_header = ttk.Style(self)
            style_header.configure(
                style="Header.TLabel",
                font=("Helvetica", 12, "bold")
            )

            label_heading = ttk.Label(
                master=self.frame_about_master,
                text=text_header,
                style="Header.TLabel",
                anchor="center",
                padding=(0, 10)  # Applies 10 pixel of padding (Left-Right, Top-Bottom)
            )

            separator_top = ttk.Separator(
                master=self.frame_about_master,
                orient="horizontal"
            )

            label_body = ttk.Label(
                master=self.frame_about_master,
                text=text_body,
                anchor="center",
                justify="center"
            )

            separator_bottom = ttk.Separator(
                master=self.frame_about_master,
                orient="horizontal"
            )

            button_exit = ttk.Button(
                master=self.frame_about_master,
                text="Chiudi",
                command=self.destroy
            )

            label_heading.grid(row=0, column=0, sticky="ew")
            separator_top.grid(row=1, column=0, sticky="ew", pady=5, padx=20)
            label_body.grid(row=2, column=0, sticky="nsew", pady=5, padx=20)
            separator_bottom.grid(row=3, column=0, sticky="ew", pady=5, padx=20)
            button_exit.grid(row=4, column=0, pady=10)

    def __init__(self,
                 employees_manager: library.EmployeesManager,
                 schedule_manager: library.ShiftManager,
                 json_manager: file_manager.JsonManager,
                 config_json_file):
        super().__init__()

        self.employees_manager = employees_manager
        self.schedule_manager = schedule_manager
        self.json_manager = json_manager
        self.configuration = config_json_file

        self.SHIFTS_CORRISPONDANCE = self.configuration["shift_settings"]["shift_representation"]
        self.current_year = datetime.date.today().year
        self.current_month = datetime.date.today().month
        self.generated_schedule = None  # Store generated schedule
        self.currently_displayed_schedule = None  # Store viewed schedule on shift_table
        self.locked_shifts = {} # Stores manual assignments {(date_iso, emp_id): shift_type}

        self._root_settings()

    def _root_settings(self):
        """Setta le proprietà fondamentali della UI"""
        self.title("Shift Manager")
        self.state("zoomed") # Full Screen

        self._frame_setting()  # Creazione dei frame

        # Popolazione dei frame
        self._build_view_shifts(self.frame_view_shifts)
        self._build_view_employees(self.frame_view_employees)

        self._menu_bar_settings()  # Setta la menubar

        self._show_view("shifts")  # Imposta la schermata iniziale (shift schedule)

    def _frame_setting(self):
        # Creazione master frame su root
        self.frame_master = ttk.Frame(self)
        self.frame_master.pack(expand=True, fill="both")
        self.frame_master.rowconfigure(0, weight=1)  # weight=1: le righe/colonne prendono tutto lo spazio
        self.frame_master.columnconfigure(0, weight=1)  # a disposizione

        # Creazione frame SOVRAPPOSTI per visualizzare shift_schedule table ed employees_list table
        # Sono sovrapposti in modo da poter passare da uno all'altro tramite menubar
        self.frame_view_shifts = ttk.Frame(self.frame_master)
        self.frame_view_employees = ttk.Frame(self.frame_master)
        self.frame_view_shifts.grid(row=0, column=0, sticky="nsew")
        self.frame_view_employees.grid(row=0, column=0, sticky="nsew")
        self.frame_view_employees.rowconfigure(0, weight=1)
        self.frame_view_employees.rowconfigure(1, weight=0)
        self.frame_view_employees.columnconfigure(0, weight=1)

        # +++ SHIFT SCHEDULE FRAME +++
        # Frame TOP: selezione anno e mese
        # Frame TABLE: visualizzazione shift_schedule table
        # Frame BOTTOM: "Visualizza", "Genera", "Salva" buttons
        self.frame_shift_schedule_top = ttk.Frame(self.frame_view_shifts)
        self.frame_shift_schedule_table = ttk.Frame(self.frame_view_shifts)
        self.frame_shift_schedule_bottom = ttk.Frame(self.frame_view_shifts, padding=15)
        self.frame_shift_schedule_top.pack(fill="x")
        self.frame_shift_schedule_table.pack(expand=True, fill="both")
        self.frame_shift_schedule_bottom.pack(side="bottom", fill="x")

        ## +++ TOP FRAME +++
        ## Impone una dimensione minima della colonna {index}, in modo da avere spazio tra i widget sulla stessa riga
        self.frame_shift_schedule_top.columnconfigure(2, minsize=20)
        self.frame_shift_schedule_top.columnconfigure(5, minsize=20)

        ## +++ BOTTOM FRAME +++
        # Impone alla colonna 0 di espandersi al massimo in modo da avere i pushbutton allineati a destra
        self.frame_shift_schedule_bottom.columnconfigure(0, weight=1)

        # +++ EMPLOYEES FRAME +++
        # Frame TABLE: contiene employees_list table
        # Frame BOTTOM: "Aggiungi", "Rimuovi", "Salva" pushbutton
        self.frame_employees_table = ttk.Frame(self.frame_view_employees)
        self.frame_employees_bottom = ttk.Frame(self.frame_view_employees, padding=5)
        self.frame_employees_table.pack(expand=True, fill="both")
        self.frame_employees_bottom.pack(side="bottom", fill="x", padx=12, pady=10)

        ## +++ BOTTOM FRAME +++
        self.frame_employees_bottom.columnconfigure(0, weight=1)

    def _menu_bar_settings(self):
        """Setta la menu bar con relative funzioni."""
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        menu_bar.add_command(label="Turni", command=lambda: self._show_view("shifts"))
        menu_bar.add_command(label="Impiegati", command=lambda: self._show_view("employees"))

        submenu_export = tk.Menu(menu_bar, tearoff=False)
        menu_bar.add_cascade(label="Esporta", menu=submenu_export)
        submenu_export.add_command(
            label="Testo",
            command=lambda: self._command_export("txt")
        )
        submenu_export.add_command(
            label="CSV",
            command=lambda: self._command_export("csv")
        )
        submenu_export.add_command(
            label="Excel (.xlsx)",
            command=lambda: self._command_export("xlsx")
        )

        submenu_other = tk.Menu(master=menu_bar, tearoff=False)
        menu_bar.add_cascade(label="Altro", menu=submenu_other)

        submenu_other.add_command(label="Info", command=self._command_show_info)
        submenu_other.add_command(label="About", command=self._command_show_about)


    @staticmethod
    def _convert_shift_schedule_to_text_format(shift_schedule):
        """
        Converts a schedule dictionary containing Employee objects into a
        dictionary containing employee IDs, suitable for the table view.
        """

        schedule = {}

        for date_obj, daily_shifts in shift_schedule.items():
            date_key_str = date_obj.isoformat()
            new_daily_shifts = {}
            for shift_type, list_of_emp_obj in daily_shifts.items():
                list_of_emp_ids = [emp.id for emp in list_of_emp_obj]
                new_daily_shifts[shift_type] = list_of_emp_ids
            schedule[date_key_str] = new_daily_shifts

        return schedule

    def _rehydrate_schedule_data(self, schedule_data_with_only_ids):
        """Converts a shift schedule with only employee IDs into a schedule with full employees details."""

        # In caso di assenza di schedule termina il metodo
        if not schedule_data_with_only_ids:
            return None

        employee_lookup = {emp.id: emp for emp in self.employees_manager.emp_list}

        rehydrated_schedule = {}
        for date_str, daily_shifts in schedule_data_with_only_ids.items():
            date_obj = datetime.date.fromisoformat(date_str)
            rehydrated_schedule[date_obj] = {}
            for shift_type, emp_ids in daily_shifts.items():
                # Replace the list of IDs with a list of Employee objects
                rehydrated_schedule[date_obj][shift_type] = [
                    employee_lookup.get(emp_id) for emp_id in emp_ids if employee_lookup.get(emp_id)
                ]

        return rehydrated_schedule

    def _new_employee_from_dialog_to_gui(self, emp_surname, emp_name, emp_serial_number):
        """Receives data from the add employee dialog window, calls the backend ed updates the UI
        (employees_list_view).
        Return True or False to indicate success or unsuccess.
        Ha funzione di callback."""

        # Chiamata al backend per aggiornamento emp_list.
        new_employee = self.employees_manager.add_employee(
            new_employee_surname=emp_surname,
            new_employee_name=emp_name,
            new_employee_serial_number=emp_serial_number
        )

        # print(new_employee) # DEBUG - Se già presente nella lista ritorna FALSE per if statement in metodo
        # print(f"len(emp_list): {len(self.employees_manager.emp_list)}") #DEBUG

        # If new employee exists refresh employee table
        if new_employee:
            self.employees_table_manager.employees_populate_table()
            return True
        else:
            messagebox.showerror("Errore", "Impiegato già presente nella lista.")
            return False

    def _command_schedule_view(self):
        """Event handler per il tasto 'Visualizza'"""

        # Setta reset di self.generated_schedule per evitare di salvare un mese mentre se ne visualizza un altro
        self.generated_schedule = None
        self.locked_shifts = {} # Reset manual locks when viewing a new schedule

        selected_year_str = self.box_year_selection.get()
        selected_month_str = self.box_month_selection.get()

        selected_year_int = int(selected_year_str)

        # Conversione mese da formato str a int
        selected_month_int = MONTHS.index(selected_month_str)

        schedule_database = self.json_manager.load_shifts_file()

        schedule_of_selected_month = schedule_database.get(selected_year_str, {}).get(str(selected_month_int))

        if not schedule_of_selected_month:
            error_message = messagebox.showwarning(
                "Dati non trovati",
                f"Nessuna turnazione trovata per {selected_month_str} {selected_year_str}."
            )
            self.schedule_table_manager.clear()
            if self.currently_displayed_schedule:
                self.currently_displayed_schedule.clear()
            self.generated_schedule = None
            return

        # Rehydrate to store full object schedule
        self.currently_displayed_schedule = self._rehydrate_schedule_data(schedule_of_selected_month)
        self.generated_schedule = None  # To be sure that var is empty (with this button schedule is not generate)

        self.schedule_table_manager.schedule_populate_table(
            schedule_data=schedule_of_selected_month,
            year=selected_year_int,
            month=selected_month_int
        )

    def _command_schedule_generate(self):
        """Generates a new schedule, asking for confirmation if one already exists."""

        selected_year_str = self.box_year_selection.get()
        selected_month_str = self.box_month_selection.get()

        selected_year_int = int(selected_year_str)

        # Conversione mese da formato str a int
        selected_month_int = MONTHS.index(selected_month_str)

        # Caricamento dello storico di tutte le schedule da shift_storage.json
        schedule_database = self.json_manager.load_shifts_file()

        # Verifica l'esistenza di un turno generato nello stesso periodo
        # Se presente ne richiede la sovrascrizione
        # str(selected_month_int) perché nel database.json il mese è salvato come numero, ma in formato str
        schedule_already_exists = False
        if selected_year_str in schedule_database and str(selected_month_int) in schedule_database[selected_year_str]:
            schedule_already_exists = True

        # Se il turno è stato già generato chiede la conferma della sovrascrizione
        if schedule_already_exists:
            overwrite = messagebox.askyesno(
                title="Programmazione Presente",
                message=f"Esiste già una programmazione per "
                        f"{selected_month_str} {selected_year_str}.\n"
                        f"Vuoi sovrascrivere?"
            )
            if not overwrite:
                return None

        # Chiamata backend ShiftManager class
        print(f"Generazione turni per {selected_month_str} {selected_year_int}")  # DEBUG
        
        # PRIMA di generare, dobbiamo "pulire" i contatori dai turni di QUESTO mese
        # perché il generatore ripartirà da zero per questo mese (sommando ai mesi precedenti).
        # Se non lo facciamo, i turni generati si sommeranno a quelli già presenti in memoria per questo mese.
        # TUTTAVIA, i locked_shifts devono essere contati.
        # Il metodo più sicuro è:
        # 1. Caricare i dipendenti (hanno i contatori "storici" + "correnti" se non abbiamo ricaricato da file).
        #    In realtà, emp_list è in memoria. Se abbiamo generato/modificato, i contatori sono "sporchi".
        #    L'ideale sarebbe ricalcolare i contatori da zero basandosi sullo storico (file) ESCLUSO il mese corrente.
        #    Ma non abbiamo una funzione facile per farlo.
        #    Alternativa: Iterare sulla schedule ATTUALE (se esiste) e decrementare.
        
        if self.currently_displayed_schedule:
             shift_map = {v: k for k, v in self.SHIFTS_CORRISPONDANCE.items()}
             for date_obj, daily_shifts in self.currently_displayed_schedule.items():
                 # Verifica che sia del mese che stiamo rigenerando (dovrebbe esserlo se visualizzato)
                 if date_obj.year == selected_year_int and date_obj.month == selected_month_int:
                     for shift_type, employees in daily_shifts.items():
                         for emp in employees:
                             if shift_type in emp.shift_count:
                                 emp.shift_count[shift_type] -= 1
        
        # Ora i contatori dovrebbero essere "puliti" (come se il mese non fosse mai esistito).
        # Il generatore (shift_assignator) ri-assegnerà i turni.
        # Se passiamo locked_shifts, il generatore dovrà:
        # 1. Assegnare i locked shifts.
        # 2. Incrementare i contatori per i locked shifts.
        # 3. Assegnare il resto.
        
        is_generated = self.schedule_manager.shift_assignator(
            selected_year_int,
            selected_month_int,
            self.configuration,
            locked_shifts=self.locked_shifts
        )

        if not is_generated:
            messagebox.showwarning(
                title="Attenzione",
                message="Dipendenti non sufficienti per la creazione della programmazione.\n"
                        "Aggiungere dipendenti prima di procedere.",
                parent=self
            )
            return None

        # Storage dei turni appena generati
        new_schedule = self.schedule_manager.export_schedule()
        self.generated_schedule = new_schedule
        self.currently_displayed_schedule = new_schedule
        # print(self.generated_schedule) # DEBUG

        # Ripopola la tabella per mostrare la nuova schedula
        generated_schedule_display_format = self._convert_shift_schedule_to_text_format(self.generated_schedule)
        self.schedule_table_manager.schedule_populate_table(
            schedule_data=generated_schedule_display_format,
            year=selected_year_int,
            month=selected_month_int
        )

        messagebox.showinfo("Turni Generati",
                            f"Nuova programmazione per {selected_month_str} "
                            f"{selected_year_str} generata con successo.")
        return None

    def _command_schedule_save(self):
        if not self.generated_schedule:
            messagebox.showerror(
                title="Programmazione Assente",
                message="Generare una programmazione prima di tentare il salvataggio",
                parent=self
            )
            return
        else:
            self.json_manager.save_shifts_file(self.generated_schedule)
            self.json_manager.save_employees_file(self.employees_manager.export_employees_list())

        messagebox.showinfo(
            title="Salvataggio Eseguito",
            message="Programmazione salvata correttamente.",
            parent=self)

    def _command_employees_add(self):
        """Opens the Add Employee dialog."""
        # Creazione oggetto finestra di dialogo
        dialog_window_add_employee = ShiftManagerGui.AddEmployeeDialogWindow(
            self,
            self._new_employee_from_dialog_to_gui
        )

    def _command_employees_remove(self):
        """Gestisce la logica di rimozione di un impiegato."""
        # Verifica che sia stato selezionato un employee, altrimenti blocca il codice per evitare crash
        if self.employees_table_manager.get_selected_employee_datas() is None:
            messagebox.showinfo(
                title="Rimuovere Impiegato",
                message="Per rimuovere un impiegato selezionarne uno dall'elenco e premere su 'Rimuovi'",
                parent=self
            )
            return None

        # Salvataggio di serial_number, cognome e nome dell'employee selezionato nella tabella
        (
            selected_employee_serial_number,
            selected_employee_surname,
            selected_employee_name
        ) = self.employees_table_manager.get_selected_employee_datas()

        # Verifica che un employee sia stato effettivamente selezionato
        employee_to_remove = None
        for employee in self.employees_manager.emp_list:
            # DEBUG
            # print(f"selected_employee_serial_number == employee.serial_number: {selected_employee_serial_number} == "
            #       f"{employee.serial_number}\n"
            #       f"selected_employee_surname == employee.surname: {selected_employee_surname} == {employee.surname}\n"
            #       f"selected_employee_name == employee.name: {selected_employee_name} == {employee.name}"
            # )
            # print(f"len(emp_list) = {len(self.employees_manager.emp_list)}")
            if (
                    selected_employee_serial_number == employee.serial_number and
                    selected_employee_surname == employee.surname and
                    selected_employee_name == employee.name
            ):
                employee_to_remove = employee
                # print(employee_to_remove.surname) # DEBUG
                break

        # DEBUG
        if not employee_to_remove:
            print("Impossibile trovare i dati dell'impiegato selezionato.")
            return None

        # Richiede la conferma di eliminazione
        check_delete = messagebox.askyesno(
            title="Conferma Eliminazione",
            message=f"Vuoi davvero eliminare l'impiegato {employee_to_remove.surname} {employee_to_remove.name}?",
            parent=self
        )

        if not check_delete:
            return None

        # In caso di conferma richiama il metodo di backend
        employee_found = self.employees_manager.remove_employee(
            employee_to_remove_serial_number=selected_employee_serial_number,
            employee_to_remove_surname=selected_employee_surname,
            employee_to_remove_name=selected_employee_name
        )

        if not employee_found:
            print("Impiegato non trovato")
            return None

        # Esegue un refresh della lista degli impiegati
        self.employees_table_manager.employees_populate_table()

        return None

    def _command_employees_save(self):
        """Salva la lista degli employee in employees.json."""

        check_save = messagebox.askyesno(
            title="Eseguire Salvataggio?",
            message="Vuoi salvare la lista degli impiegati?",
        )
        if check_save:
            self.json_manager.save_employees_file(self.employees_manager.export_employees_list())
            messagebox.showinfo("Salvato", "Salvataggio Eseguito.")
        else:
            return

    def _command_export(self, export_format):
        """Gestisce i comandi di esportazione (CSV, XLSX)."""

        # Verifica della presenza di una schedula da esportare
        if not self.currently_displayed_schedule:
            messagebox.showwarning(
                title="Impossibile Esportare",
                message="Programmazione non presente.\n"
                        "Genera o visualizza una programmazione prima di esportarla.",
                parent=self
            )
            return None

        # Utilizza mese e anno di riferimento per generare un filename di default
        selected_year_str = self.box_year_selection.get()
        selected_month_str = self.box_month_selection.get()

        # Conversione year and month in int per utilizzo in altri metodi
        selected_year_int = int(selected_year_str)
        selected_month_int = MONTHS.index(selected_month_str)

        # Open "Save As..." dialog box
        file_types = {
            "txt": [("Text file", "*.txt")],
            "csv": [("CSV file", "*.csv")],
            "xlsx": [("Excel file", "*.xlsx")]
        }

        filepath = filedialog.asksaveasfilename(
            title=f"Esporta come {export_format.upper()}",
            initialfile=f"{selected_month_str}_{selected_year_str}_schedule.{export_format}",
            filetypes=file_types[export_format],
            defaultextension=f".{export_format}"
        )

        # If user cancel the dialog, filepath will be empty
        if not filepath:
            return None

        # Creazione istanza Exporter e chiamata del metodo corretto
        try:
            exporter = Exporter(
                schedule_data=self.currently_displayed_schedule,
                employees_list=self.employees_manager.export_employees_list(),
                year=selected_year_int,
                month=selected_month_int,
                config=self.configuration
            )

            export_done = False
            if export_format == "txt":
                exporter.export_to_txt(filepath)
                export_done = True
            elif export_format == "csv":
                exporter.export_to_csv(filepath)
                export_done = True
            elif export_format == "xlsx":
                exporter.export_to_xlsx(filepath)
                export_done = True

            if export_done:
                messagebox.showinfo(
                    title="Esportazione Riuscita",
                    message=f"File esportato con successo in\n{filepath}.",
                    parent=self
                )
        except Exception as e:
            messagebox.showerror(
                title="Esportazione Non Riuscita",
                message=f"Si è verificato un errore:\n{e}",
                parent=self
            )

    def _command_show_info(self):
        """Opens the Info dialog window"""
        info_dialog_window = ShiftManagerGui.InfoDialogWindow(self.frame_master)

    def _command_show_about(self):
        """Opens the Aboud dialog window"""
        about_dialog_window = ShiftManagerGui.AboutDialogWindow(self.frame_master)

    def _show_view(self, view):
        """Mostra in primo piano la vista passata come argomento.
        'shifts': shift_schedule table
        'employees' employees_list table"""

        if view == "shifts":
            self.frame_view_shifts.tkraise()
        elif view == "employees":
            if hasattr(self, "employees_table_manager"):
                self.employees_table_manager.employees_populate_table()
            self.frame_view_employees.tkraise()

    def _build_view_shifts(self, frame):
        """Genera l'interfaccia della finestra che mostra la turnazione."""

        # Determina il range di anni da visualizzare. Valore preso da config.json -> date -> year_range
        year_range_for_selection = self.configuration["date"]["year_range"]
        years_range_for_year_selection = [
            str(year) for year in range(self.current_year - year_range_for_selection,
                                        self.current_year + year_range_for_selection + 1)
        ]

        # Selezione mese/anno
        label_shift_schedule_top_year = ttk.Label(self.frame_shift_schedule_top, text="Anno")
        label_shift_schedule_top_month = ttk.Label(self.frame_shift_schedule_top, text="Mese")
        self.box_year_selection = ttk.Combobox(self.frame_shift_schedule_top,
                                               values=years_range_for_year_selection,
                                               state="readonly",
                                               justify="center",
                                               width=5)
        self.box_year_selection.set(str(self.current_year))  # .set() Setta il valore di default da visualizzare
        self.box_month_selection = ttk.Combobox(self.frame_shift_schedule_top,
                                                values=MONTHS,
                                                state="readonly",
                                                justify="left",
                                                width=10)
        self.box_month_selection.set(MONTHS[self.current_month])

        label_shift_schedule_top_year.grid(row=0, column=0, pady=5)
        self.box_year_selection.grid(row=0, column=1, pady=5)
        label_shift_schedule_top_month.grid(row=0, column=3, pady=5)
        self.box_month_selection.grid(row=0, column=4, pady=5)

        # Creazione shift_schedule table
        self.schedule_table_manager = ShiftManagerGui.ScheduleTable(
            parent_frame=self.frame_shift_schedule_table,
            employees_list=self.employees_manager.emp_list,
            configuration=self.configuration
        )
        self.schedule_table_manager.pack(expand=True, fill="both")

        # Creazione e posizionamento pushbutton
        button_view_shifts = ttk.Button(
            self.frame_shift_schedule_bottom,
            text="Visualizza",
            command=self._command_schedule_view
        )

        button_generate_shifts = ttk.Button(
            self.frame_shift_schedule_bottom,
            text="Genera Turni",
            command=self._command_schedule_generate
        )

        button_save_shifts = ttk.Button(
            self.frame_shift_schedule_bottom,
            text="Salva",
            command=self._command_schedule_save
        )

        button_exit = ttk.Button(
            self.frame_shift_schedule_bottom,
            text="Esci",
            command=self.destroy
        )

        # Colonna iniziale è column=1 perché la colonna 0 utilizzata per l'allineamento a Sud-Est
        # self.frame_shift_schedule_bottom.columnconfigure(0, weight=1)
        button_view_shifts.grid(row=0, column=1, sticky="e")
        button_generate_shifts.grid(row=0, column=2, sticky="e")
        button_save_shifts.grid(row=0, column=3, sticky="e")
        button_exit.grid(row=0, column=4, sticky="e")

    def _build_view_employees(self, frame):
        """Genera l'interfaccia della finestra che mostra la gli impiegati."""

        # Creazione e posizionamento employees_table
        self.employees_table_manager = ShiftManagerGui.EmployeeTable(
            self.frame_employees_table,
            self.employees_manager.emp_list,
            self.configuration
        )
        self.employees_table_manager.pack(expand=True, fill="both")

        # Creazione e posizionamento pushbutton
        button_add_employee = ttk.Button(
            self.frame_employees_bottom,
            text="Aggiungi",
            command=self._command_employees_add
        )
        button_remove_employee = ttk.Button(
            self.frame_employees_bottom,
            text="Rimuovi",
            command=self._command_employees_remove
        )
        button_save_employee = ttk.Button(
            self.frame_employees_bottom,
            text="Salva",
            command=self._command_employees_save
        )
        button_exit_employee = ttk.Button(
            self.frame_employees_bottom,
            text="Esci",
            command=self.destroy
        )

        # Colonna iniziale è column=1 perché la colonna 0 utilizzata per l'allineamento a Sud-Est
        # self.frame_employees_bottom.columnconfigure(0, weight=1)
        button_add_employee.grid(row=0, column=1, sticky="se")
        button_remove_employee.grid(row=0, column=2, sticky="se")
        button_save_employee.grid(row=0, column=3, sticky="se")
        button_exit_employee.grid(row=0, column=4, sticky="se")
