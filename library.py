import calendar
import datetime
import math
import random
from file_manager import JsonManager

WEEKDAYS = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]

class Employee:
    """Consente di gestire gli impiegati.
    Assegna un'identità all'impiegato e tiene il conteggio dei turni effettuati."""

    def __init__(self,
                 emp_id,
                 emp_surname,
                 emp_name,
                 emp_serial_number):
        self.id = emp_id
        self.surname = emp_surname
        self.name = emp_name
        self.serial_number = emp_serial_number
        self.days_off = []
        self.shift_count = {
            "mattina": 0,
            "mattina_rep": 0,
            "pomeriggio": 0,
            "weekend_rep": 0,
            "days_off": 0
        }


class EmployeesManager:
    """Consente la gestione del file di input degli employees."""

    def __init__(self, config_dict):
        self.emp_list = []
        self.employees_json = config_dict["files"]["employees_database_file"]
        self.file_loader = JsonManager()

        self._import_employees_from_json()

    def _calculate_id_and_starting_shift_count_for_added_employee(self):
        """Assegna un nuovo ID al new_employee e calcola una media dei turni svolti da tutti gli altri in modo da farlo
        partire al pari degli altri. Se partisse da zero la logica di funzionamento del software metterebbe sempre lui
        a oltranza.
        Restituisce: (max_id, average_mattina, average_mattina_rep, average_pomeriggio, average_weekend_rep)"""

        max_id = 0
        mattina_sum = 0
        mattina_rep_sum = 0
        pomeriggio_sum = 0
        weekend_rep_sum = 0

        # Rileva il massimo ID assegnato agli employees
        # Calcola il totale dei turni assegnati, in modo da poter eseguire la media
        for emp in self.emp_list:
            if emp.id > max_id:
                max_id = emp.id

            mattina_sum += emp.shift_count["mattina"]
            mattina_rep_sum += emp.shift_count["mattina_rep"]
            pomeriggio_sum += emp.shift_count["pomeriggio"]
            weekend_rep_sum += emp.shift_count["weekend_rep"]

        # Aggiunge 1 all'ID massimo rilevato, in modo da averne uno originale
        max_id += 1

        # Calcolo medie
        if len(self.emp_list) == 0:  # Previene crash nel caso in cui len(self.emp_list) = 0.
            average_mattina = 0
            average_mattina_rep = 0
            average_pomeriggio = 0
            average_weekend_rep = 0
        else:
            average_mattina = math.floor(mattina_sum / len(self.emp_list))
            average_mattina_rep = math.floor(mattina_rep_sum / len(self.emp_list))
            average_pomeriggio = math.floor(pomeriggio_sum / len(self.emp_list))
            average_weekend_rep = math.floor(weekend_rep_sum / len(self.emp_list))

        return max_id, average_mattina, average_mattina_rep, average_pomeriggio, average_weekend_rep

    def _import_employees_from_json(self):
        """
        # 1. Legge nome cognome dal file employees.json.
        # 2. Genera l'istanza dell'employee e gli assegna un numero id incrementale.
        # 3. Inserisce nell'array emp_list gli oggetti così creati.
        """
        imported_employees_from_file = self.file_loader.load_employees_file()  # Creazione/Import di employees.json
        # L'import si avvia solo se sono presenti impiegati nel file employees.json
        if len(imported_employees_from_file) > 0:
            for employee in imported_employees_from_file:
                temp_employee = Employee(
                    emp_id=employee["id"],
                    emp_surname=employee["surname"],
                    emp_name=employee["name"],
                    emp_serial_number=employee["serial_number"]
                )

                # Conversione days_off da stringhe a oggetti datetime.date
                temp_employee.days_off = [datetime.date.fromisoformat(d) for d in employee["days_off"]]
                temp_employee.shift_count["mattina"] = employee["shift_count"]["mattina"]
                temp_employee.shift_count["mattina_rep"] = employee["shift_count"]["mattina_rep"]
                temp_employee.shift_count["pomeriggio"] = employee["shift_count"]["pomeriggio"]
                temp_employee.shift_count["weekend_rep"] = employee["shift_count"]["weekend_rep"]
                self.emp_list.append(temp_employee)

        # print(self.emp_list) # DEBUG

    def add_employee(
            self,
            new_employee_surname,
            new_employee_name,
            new_employee_serial_number
    ):
        """Aggiunge un impiegato al file employees.json e ritorna l'impiegato aggiunto."""
        # Correzione della formattazione degli args surname e name
        new_employee_surname = new_employee_surname.lower().capitalize()
        new_employee_name = new_employee_name.lower().capitalize()
        new_employee_serial_number = new_employee_serial_number.upper()

        # Verifica se l'impiegato che si desidera inserire è già presente in employees.json
        for employee in self.emp_list:
            if (new_employee_surname == employee.surname and
                new_employee_name == employee.name and
                new_employee_serial_number == employee.serial_number):
                print("Impiegato già presente nella lista.")
                return False

        # +++ CREAZIONE NUOVO OGGETTO EMPLOYEE ED AGGIUNTA A EMP_LIST +++
        [
            new_employee_id,
            new_employee_mattina_count,
            new_employee_mattina_rep_count,
            new_employee_pomeriggio_count,
            new_employee_weekend_rep_count
        ] = self._calculate_id_and_starting_shift_count_for_added_employee()

        # Creazione nuovo object employee
        new_employee = Employee(emp_id=new_employee_id,
                                emp_surname=new_employee_surname,
                                emp_name=new_employee_name,
                                emp_serial_number = new_employee_serial_number
                                )

        new_employee.shift_count["mattina"] = new_employee_mattina_count
        new_employee.shift_count["mattina_rep"] = new_employee_mattina_rep_count
        new_employee.shift_count["pomeriggio"] = new_employee_pomeriggio_count
        new_employee.shift_count["weekend_rep"] = new_employee_weekend_rep_count

        # Aggiunta nuovo employee a emp_list
        self.emp_list.append(new_employee)

        # print(len(self.emp_list)) # DEBUG
        return new_employee

    def remove_employee(self, employee_to_remove_serial_number, employee_to_remove_surname, employee_to_remove_name):
        """Rimuove un impiegato dal file employees.json. Ritorna FALSE se non trovato, altrimenti TRUE"""
        # Correzione della formattazione degli args surname e name
        employee_to_remove_serial_number = employee_to_remove_serial_number.upper()
        employee_to_remove_surname = employee_to_remove_surname.lower().capitalize()
        employee_to_remove_name = employee_to_remove_name.lower().capitalize()

        # Verifica presenza dell'impiegato da rimuovere nella lista degli impiegati salvati
        employee_found = False
        for employee in self.emp_list:
            if (
                employee.serial_number == employee_to_remove_serial_number and
                employee.surname == employee_to_remove_surname and
                employee_to_remove_name == employee_to_remove_name
            ):
                employee_found = True
                self.emp_list.remove(employee) # Rimozione impiegato dal database del software
                print(f"Impiegato {employee.surname} {employee.name} rimosso.")
                break

        if not employee_found:
            # DEBUG
            # print(f"L'impiegato {employee_to_remove_surname} {employee_to_remove_name} che si desidera rimuovere "
            #       f"non è presente nella lista.")
            return False


        # print(len(self.emp_list))  # DEBUG
        return True

    def add_day_off(self, surname, name, off_duty_year, off_duty_month, off_duty_day):
        """Setta un giorno di ferie a un employee dato in input"""

        # Correzione della formattazione degli args surname e name
        surname = surname.lower().capitalize()
        name = name.lower().capitalize()

        # Genera l'oggetto datetime.data
        try:
            off_duty_date = datetime.date(off_duty_year, off_duty_month, off_duty_day)
        except ValueError:
            print("ERRORE! Verificare che la data immessa sia corretta.")
            return None

        # Ricerca employee nella lista e setta il giorno di ferie
        employee_found = False
        for employee in self.emp_list:
            if [surname, name] == [employee.surname, employee.name] and off_duty_date not in employee.days_off:
                employee_found = True
                employee.days_off.append(off_duty_date)
                print(f"{surname} {name} off-duty il giorno {WEEKDAYS[off_duty_date.weekday()]} {off_duty_date}")
            # Se l'impiegato è già in ferie quel giorno il software lo notifica
            elif [surname, name] == [employee.surname, employee.name] and off_duty_date in employee.days_off:
                print(f"{surname} {name} già in ferie il giorno {WEEKDAYS[off_duty_date.weekday()]} {off_duty_date}")

        if not employee_found:
            print("Impossibile trovare l'impiegato.")
            return None

        return True

    def remove_day_off(self, surname, name, off_duty_year, off_duty_month, off_duty_day):
        """Rimuove un giorno di ferie a un employee dato in input"""

        # Correzione della formattazione degli args surname e name
        surname = surname.lower().capitalize()
        name = name.lower().capitalize()

        # Genera l'oggetto datetime.data
        off_duty_date = datetime.date(off_duty_year, off_duty_month, off_duty_day)

        # Ricerca employee nella lista e setta il giorno di ferie
        employee_found = False
        for employee in self.emp_list:
            if [surname, name] == [employee.surname, employee.name]:
                employee_found = True
                try:
                    employee.days_off.remove(off_duty_date)
                    print(f"{surname} {name} reintegrato il {WEEKDAYS[off_duty_date.weekday()]} {off_duty_date}.")
                except ValueError:
                    print(f"Impiegato non in ferie il giorno {WEEKDAYS[off_duty_date.weekday()]} {off_duty_date}.")

        if not employee_found:
            print("Impossibile trovare l'impiegato.")
            return None

        return True

    def export_employees_list(self):
        """Esporta la lista impiegati"""
        return self.emp_list


class ShiftManager:
    def __init__(self, employees_file_manager: EmployeesManager):
        self.emp_list = employees_file_manager.emp_list
        self.file_loader = JsonManager()
        self.shift_schedule = {}

    @staticmethod
    def _calculate_daily_split(available_employees, config_dict):
        """Calcola quanti dipendenti sono assegnati al turno mattina e quanti al turno pomeriggio.
        È utile il calcolo giornaliero perché, in caso di ferie di 1+ dipendenti, la divisione sui turni cambia.
        Output: (dipendenti_assegnati_turno_mattina, dipendenti_assegnati_turno_pomeriggio)"""
        total_employees = len(available_employees)
        num_on_mattina = math.ceil(total_employees / 2)
        num_on_mattina_rep = config_dict["shift_settings"]["n_of_employees"]["mattina_rep"]
        num_on_pomeriggio = total_employees - num_on_mattina
        num_on_weekend_rep = config_dict["shift_settings"]["n_of_employees"]["weekend_rep"]

        return num_on_mattina, num_on_mattina_rep, num_on_pomeriggio, num_on_weekend_rep

    def shift_assignator(self, year, month, config_dict, locked_shifts=None, employees_list=None):
        """Assegna i turni ai dipendenti, durante la SETTIMANA, in base al mese e anno selezionati.
        Inserisce nel dictionary vuoto del shift_assignment_for_month_to_fill vuoto gli array dei dipendenti..

        Esempio: 01.01.2025: {'mattina':[emp_n, ..., emp_m], 'pomeriggio': [emp_x, ..., emp_y]}

        Ritorna la schedula creata."""
        
        if locked_shifts is None:
            locked_shifts = {}

        # Use the provided list if available, otherwise use the instance's list
        current_emp_list = employees_list if employees_list is not None else self.emp_list

        # Dictionary vuoto contenente il calendario e i turni possibili. Devono essere inseriti i turni
        shift_assignment_for_month = monthly_calendar_generator(year, month)

        # Se non sono presenti almeno due impiegati nella lista impedisce di generare i turni
        if len(current_emp_list) < 2:
            print("Non sono presenti abbastanza impiegati per la generazione dei turni.\n"
                  "Inserire ulteriori impiegati.")
            return False

        # +++ Inizio assegnazione turni giorno per giorno dato un certo mese e anno +++
        for day_date in shift_assignment_for_month:
            # print(f"\nAssigning shift for date {day_date}") # DEBUG

            # Copia della lista dei dipendenti per lavorare giorno per giorno
            employees_available_for_today = [emp for emp in current_emp_list if day_date not in emp.days_off]

            # Calcolo split impiegati
            (
                n_employees_on_mattina,
                n_employees_on_mattina_rep,
                n_employees_on_pomeriggio,
                n_employees_on_weekend_rep
            ) = self._calculate_daily_split(employees_available_for_today, config_dict)
            
            assigned_today = []  # Tiene conto delle persone assegnate per evitare doppi turni
            
            # +++ GESTIONE LOCKED SHIFTS +++
            # Assegna i turni bloccati manualmente e rimuove gli impiegati dalla disponibilità
            day_iso = day_date.isoformat()
            
            # Identifica i lock per oggi
            locks_today = []
            for (l_date, l_emp_id), l_shift in locked_shifts.items():
                if l_date == day_iso:
                    locks_today.append((l_emp_id, l_shift))
            
            for emp_id, shift_type in locks_today:
                # Trova l'oggetto employee
                emp_obj = next((e for e in current_emp_list if e.id == emp_id), None)
                if emp_obj:
                    if shift_type in shift_assignment_for_month[day_date]:
                         shift_assignment_for_month[day_date][shift_type].append(emp_obj)
                         assigned_today.append(emp_obj)
                         
                         # Incrementa contatore
                         if shift_type in emp_obj.shift_count:
                             emp_obj.shift_count[shift_type] += 1
                         
                         # Riduciamo il numero di posti disponibili per quel turno
                         if shift_type == "mattina":
                             n_employees_on_mattina -= 1
                         elif shift_type == "mattina_rep":
                             n_employees_on_mattina_rep -= 1
                         elif shift_type == "pomeriggio":
                             n_employees_on_pomeriggio -= 1
                         elif shift_type == "weekend_rep":
                             n_employees_on_weekend_rep -= 1
            
            # Rimuovi gli assegnati dalla lista dei disponibili
            employees_available_for_today = [e for e in employees_available_for_today if e not in assigned_today]

            # Assicuriamoci che non siano negativi
            n_employees_on_mattina = max(0, n_employees_on_mattina)
            n_employees_on_mattina_rep = max(0, n_employees_on_mattina_rep)
            n_employees_on_pomeriggio = max(0, n_employees_on_pomeriggio)
            n_employees_on_weekend_rep = max(0, n_employees_on_weekend_rep)

            random.shuffle(employees_available_for_today)  # Randomness in caso di stesso numero di turni
            

            # +++ ASSEGNAZIONU TURNI WEEKEND +++
            if day_date.weekday() in config_dict["shift_settings"]["weekend_days"]:
                # print(f"{day_date} - WEEKEND {day_date.weekday()}") # For DEBUG

                # Ordina la lista dei dipendenti in base ai weekend fatti
                employees_available_for_today.sort(key=lambda emp: emp.shift_count["weekend_rep"])

                for i in range(n_employees_on_weekend_rep):
                    if i < len(employees_available_for_today):
                        employee_to_assign = employees_available_for_today[i]
                        shift_assignment_for_month[day_date]["weekend_rep"].append(employee_to_assign)
                        employee_to_assign.shift_count["weekend_rep"] += 1
                        assigned_today.append(employee_to_assign)

            else:
                # print(f"{day_date} - WEEKDAY {day_date.weekday()}") # For DEBUG

                # +++ Assegnazione turni mattina +++
                # Ordina la lista dei dipendenti in base alle mattine fatte
                employees_available_for_today.sort(key=lambda emp: emp.shift_count["mattina"])

                for i in range(n_employees_on_mattina):
                    if i < len(employees_available_for_today):
                        employee_to_assign = employees_available_for_today[i]
                        shift_assignment_for_month[day_date]["mattina"].append(employee_to_assign)
                        employee_to_assign.shift_count["mattina"] += 1
                        assigned_today.append(employee_to_assign)
                
                # +++ Assegnazione mattina + rep +++
                # Recuperiamo TUTTI quelli che fanno mattina oggi
                all_mattina_today = shift_assignment_for_month[day_date]["mattina"]
                # Filtriamo quelli che non hanno già mattina_rep
                candidates_for_rep = [e for e in all_mattina_today if e not in shift_assignment_for_month[day_date]["mattina_rep"]]
                
                random.shuffle(candidates_for_rep)
                candidates_for_rep.sort(key=lambda emp: emp.shift_count["mattina_rep"])
                
                for i in range(n_employees_on_mattina_rep):
                    if i < len(candidates_for_rep):
                        employee_to_assign = candidates_for_rep[i]
                        shift_assignment_for_month[day_date]["mattina_rep"].append(employee_to_assign)
                        employee_to_assign.shift_count["mattina_rep"] += 1

                # +++ Assegnazione turni pomeriggio +++
                employees_available_for_pomeriggio = [
                    emp for emp in employees_available_for_today 
                    if emp not in assigned_today
                ]
                
                if n_employees_on_pomeriggio > 0:
                    random.shuffle(employees_available_for_pomeriggio)
                    employees_available_for_pomeriggio.sort(key=lambda emp: emp.shift_count["pomeriggio"])

                    for i in range(n_employees_on_pomeriggio):
                        if i < len(employees_available_for_pomeriggio):
                            employee_to_assign = employees_available_for_pomeriggio[i]
                            shift_assignment_for_month[day_date]["pomeriggio"].append(employee_to_assign)
                            employee_to_assign.shift_count["pomeriggio"] += 1

        self.shift_schedule = shift_assignment_for_month
        return True

    def export_schedule(self):
        """Esporta la programmazione generata per un certo mese.
        Il formato sarà:
        {
            datetime.date(yyyy, m, d): {
                "mattina": [],
                "mattina_rep": [],
                "pomeriggio": [],
                "weekened_rep": [],
            },
            datetime.date(yyyy, m, d+1): {...}
        } """
        return self.shift_schedule


class ShiftGeneratorTest:
    """Classe di testing."""
    def __init__(self, employees_file_manager: EmployeesManager):
        self.emp_list = employees_file_manager.emp_list
        self.input_file = "employees.txt"

    def show_list_of_employees(self):
        """Stampa la lista degli impiegati utilizzati dal software per eseguire le funzioni."""
        for emp in self.emp_list:
            print(emp.surname, emp.name)
            print(f"Days off: {emp.days_off}")
            print(f"Shift_count: {emp.shift_count}")
            print("-" * 10)

    @staticmethod
    def show_list_of_shifts(schedule):
        """+++ PER TEST +++
        Permette di visualizzare i nomi associato a ciascun giorno."""
        for day in schedule:
            print(day, " - ", WEEKDAYS[day.weekday()])

            print("MATTINA: ", end="")
            for employee in schedule[day]["mattina"]:
                print(f"{employee.name} {employee.surname},",  end=" ")
            print(f"({len(schedule[day]['mattina'])})")

            print("MATTINA + REP: ", end="")
            for employee in schedule[day]["mattina_rep"]:
                print(f"{employee.name} {employee.surname},",  end=" ")
            print(f"({len(schedule[day]['mattina_rep'])})")

            print("POMERIGGIO: ", end="")
            for employee in schedule[day]["pomeriggio"]:
                print(f"{employee.name} {employee.surname},",  end=" ")
            print(f"({len(schedule[day]['pomeriggio'])})")

            print("WEEKEND: ", end="")
            for employee in schedule[day]["weekend_rep"]:
                print(f"{employee.name} {employee.surname},",  end=" ")
            print(f"({len(schedule[day]['weekend_rep'])})\n")

    def show_shifts_count(self):
        """Permette di visualizzare quanti turni di ogni tipo sono assegnati a ciascun employee."""
        for employee in self.emp_list:
            print(f"{employee.surname}: {employee.shift_count}")
        print("\n")

    def test_shift_assignation(self, employees_file_manager_class, config_dict):
        """FAIRNESS TEST.
        Consente di assegnare turni su un lungo periodo e verificare quanti turni sono stati assegnati
        a ciascun employee."""
        n_of_run = int(input("Inserire il numero run da voler simulare: "))
        shift_calendar_for_test = ShiftManager(employees_file_manager_class)
        year = 2025
        month = 1
        for run in range(n_of_run):
            shift_calendar_for_test.shift_assignator(year, month, config_dict)
            month += 1
            if month == 13:
                year += 1
                month = 1

        for employee in self.emp_list:
            print(f"{employee.surname}: {employee.shift_count}")


def monthly_calendar_generator(selected_year: int, selected_month: int):
    """Dati in input un certo anno e un certo mese, genera un dictionary con tutti i giorni del mese.
    Associa, inoltre, a ogni giorno del mese i possibili turni.
    Es. 01-01-2025 = {'mattina': [],
                      'mattina_rep': [],
                      'pomeriggio': [],
                      'weekend_rep': []
                      }"""

    calendar_of_selected_month = {}
    # calendar.monthrange restituisce la tupla (primo_giorno_del_mese, numero_giorni_nel_mese)
    n_days_in_selected_month = calendar.monthrange(selected_year, selected_month)[1]

    for day in range(1, n_days_in_selected_month + 1):
        temp_date = datetime.date(selected_year, selected_month, day) # Data associata al giorno iterato (yyy-mm-dd)

        # Aggiunge valori al dictionary date_of_selected_month e inizializza la presenza dei turni
        calendar_of_selected_month[temp_date] = {"mattina": [],
                                                 "mattina_rep": [],
                                                 "pomeriggio": [],
                                                 "weekend_rep": []
                                                 }

    return calendar_of_selected_month