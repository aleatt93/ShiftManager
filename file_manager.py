import datetime
import json
import os
import sys


class JsonManager:
    def __init__(self):
        self.directories = ["data"]
        self.file_path_config = "config.json"
        self.file_path_employees = os.path.join(self.directories[0], "employees.json") #./Data/.json
        self.file_path_shifts_storage = os.path.join(self.directories[0], "shift_storage.json") #./Data/.json

        self._directories_check()

    def _directories_check(self):
        """Checks if a directory exists at the given path, and creates it if not."""
        # Creazione directories
        for directory in self.directories:
            os.makedirs(directory,exist_ok=True)

    @staticmethod
    def _load_file(file_to_load, default_file):
        """Verifica l'esistenza e l'integrità del file da aprire.
            - json_to_load: file che si desidera caricare.
            - default_file: contenuto default da caricare se il file desiderato non esiste."""
        if not os.path.exists(file_to_load):
            try:
                with open(file_to_load, "w") as f:
                    json.dump(default_file, f, indent=4)
                    return default_file
            except IOError:
                print(f"Impossibile creare {file_to_load}")
                return None
        else:
            try:
                # Lettura json per verifica integrità. Se corrotto ne propone il reset
                with open(file_to_load, "r") as f:
                    loaded_file = json.load(f)
                    # print(loaded_file) #DEBUG
                    return loaded_file
            except (ValueError, IOError):
                print(f"{file_to_load} corrupted or unreadable! Try to reset {file_to_load} or correct it manually.")
                return None

    def load_config_file(self):
        """Verifica l'esistenza del file config.json.
        Se il file non esiste lo crea inserendovi impostazioni di default e ritornando quelle impostazioni."""

        current_date = datetime.date.today()
        default_configuration = {
            "date": {
                "year": current_date.year,
                "month": current_date.month,
                "year_range": 5
            },
            "files": {
                "employees_database_file": self.file_path_employees,
                "shift_storage_database_file": self.file_path_shifts_storage
            },
            "shift_settings": {
                "shift_representation": {
                    "mattina": "M",
                    "mattina_rep": "M+R",
                    "pomeriggio": "P",
                    "weekend_rep": "R",
                    "off_duty": "X"
                },
                "n_of_employees":{
                    "mattina_rep": 1,
                    "weekend_rep": 1
                },
                "weekend_days": [5, 6]
            },
            "employees_view": {
                "matricola": "Matricola",
                "cognome": "Cognome",
                "nome": "Nome",
                "mattina": "Mattina",
                "mattina_rep": "Mattina REP",
                "pomeriggio": "Pomeriggio",
                "weekend_rep": "Weekend REP",
                "off_duty": "Ferie"
            }
        }

        return self._load_file(self.file_path_config, default_configuration)

    def load_employees_file(self):
        """Verifica l'esistenza del file employees.json.
        employees.json sarà un array (in modo da poter contarne gli elementi), i cui elementi sono dictionary:

        employees.json = [{'id': ..., 'surname': ..., 'name': ..., 'serial_number': ...'shift_count': {'mattina': ...,
        mattina_rep': ..., 'pomeriggio': ..., 'weekend_rep': ...}, {...}]

        Se il file non esiste lo crea inserendovi un array vuoto."""

        default_employees_json = []

        return self._load_file(self.file_path_employees, default_employees_json)

    def load_shifts_file(self):
        """Verifica l'esistenza del file shits_storage.json.
        Se non esiste crea un dictionary vuoto.
        Il file avrà una struttura del tipo:
        {
        "2024": {
            "5": {
                "2024-05-01": { "mattina": [/* employee data */], "pomeriggio": [/* ... */] },
                "2024-05-02": { "mattina": [/* employee data */], "pomeriggio": [/* ... */] },
                "...": "..."
            },
            "6": {
                "2024-06-01": { "mattina": [/* employee data */], "pomeriggio": [/* ... */] },
                "...": "..."
            }
        },
        "2025": {
            "1": {
                "...": "..."
            }
        }"""

        default_shifts_storage = {}

        return self._load_file(self.file_path_shifts_storage, default_shifts_storage)

    @staticmethod
    def reset_file(file_to_reset, default_file):
        print(f"Ripristino {file_to_reset} in corso...")
        with open(file_to_reset, "w") as f:
            json.dump(default_file, f, indent=4)
            return default_file

    def save_employees_file(self, exported_employees_list):
        """Salva gli impiegati e i loro attributi (dati in input) nel file employees.json"""
        file_to_save = []

        for employee in exported_employees_list:
            employee_dictionary = {
                "id": employee.id,
                "surname": employee.surname,
                "name": employee.name,
                "serial_number": employee.serial_number,
                # JSON non gestisce gli oggetti. Conversione da oggetto datetime.date a stringa
                "days_off": [d.isoformat() for d in employee.days_off],
                "shift_count": employee.shift_count
            }
            file_to_save.append(employee_dictionary)

        with open(self.file_path_employees, "w") as f:
            json.dump(file_to_save, f, indent=4)
            print("SALVATAGGIO IMPIEGATI COMPLETATO")

    def save_shifts_file(self, exported_shifts_list):
        """Salva i turni nel file shifts_storage.json
        Trasforma gli oggetti datetime.date in stringhe e associa alle date gli IDs degli employees."""
        # Il dictionary da salvare in shift_storage.json deriva direttamente da quello caricato.
        # Si interpreti come:
        ## Loaded_file = self.load_shifts_file()
        ## schedule_to_save = loaded_file
        schedule_to_save = self.load_shifts_file()

        if not exported_shifts_list:
            print("Nessuna programmazione da salvare.")
            return None

        # Prende il primo item della lista in modo da estrapolarne la data.
        # next(iter(...)) è un for loop in range(1)
        # La funzione iter() inserisce un iteratore nel suo argomento che punta a prima dell'elemento [0]
        # La funzione next() fa spostare il puntatore di una posizione, portandolo su [0]
        # Un successivo next() fa spostare il puntatore su [1]
        first_date = next(iter(exported_shifts_list))

        # Ricava anno e mese da first_date e ritorna le stringhe
        year_key = str(first_date.year)
        month_key = str(first_date.month)

        # Temporary storage for converted data convertibile in .json
        month_schedule_json = {}

        # date_objects -> datetime.date(yyyy-m-d)
        # daily_shifts_dicts -> {"mattina": [...], "mattina_rep": [...], ...}
        for date_objects, daily_shifts_dicts in exported_shifts_list.items():
            date_to_string = date_objects.isoformat()

            # Temporary storage for shifts convertibile in .json
            daily_shifts_schedule_json = {}

            # shift_type -> "mattina", "mattina_rep", ecc...
            # list_of_employees -> [mattina_emp_1, mattina_emp_2, ...], [mattina_rep_emp_1, ...], ecc...
            for shift_type, list_of_employees in daily_shifts_dicts.items():
                list_of_employees_id = [emp.id for emp in list_of_employees]

                daily_shifts_schedule_json[shift_type] = list_of_employees_id
            # print(daily_shifts_schedule_json) # DEBUG

            # Aggiunge il dictionary json friendly al mensile json friendly
            month_schedule_json[date_to_string] = daily_shifts_schedule_json
        # print(month_schedule_json) # DEBUG

        # Check dell'esistenza della key dell'anno di riferimento. Se non esiste la crea
        if year_key not in schedule_to_save:
            schedule_to_save[year_key] = {}

        # Aggiunta del json-friendly dict generato al loaded
        schedule_to_save[year_key][month_key] = month_schedule_json

        # Scrittura della schedula mensile generata su shifts_storage.json
        try:
            with open(self.file_path_shifts_storage, "w") as f:
                json.dump(schedule_to_save, f, indent=4)
                print("SALVATAGGIO TURNI COMPLETATO")
        except (IOError, ValueError):
            print(f"Errore durante il salvataggio di {self.file_path_shifts_storage}.")

        return None

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)