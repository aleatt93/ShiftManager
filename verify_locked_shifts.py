import tkinter as tk
from tkinter import ttk
import datetime
import copy
from unittest.mock import MagicMock

# Mock library classes
class Employee:
    def __init__(self, emp_id, surname, name, serial):
        self.id = emp_id
        self.surname = surname
        self.name = name
        self.serial_number = serial
        self.days_off = []
        self.shift_count = {"mattina": 0, "mattina_rep": 0, "pomeriggio": 0, "weekend_rep": 0, "days_off": 0}

class EmployeesManager:
    def __init__(self):
        self.emp_list = [
            Employee(1, "A", "A", "S1"),
            Employee(2, "B", "B", "S2"),
            Employee(3, "C", "C", "S3")
        ]
    def export_employees_list(self):
        return []

class ShiftManager:
    def __init__(self, emp_manager):
        self.emp_manager = emp_manager
    
    def shift_assignator(self, year, month, config, locked_shifts=None, employees_list=None):
        print(f"shift_assignator called with {len(locked_shifts) if locked_shifts else 0} locked shifts")
        return True
    
    def export_schedule(self):
        # Return a complete dummy schedule
        return {
            datetime.date(2025, 1, d): {
                "mattina": [],
                "mattina_rep": [],
                "pomeriggio": [],
                "weekend_rep": []
            } for d in range(1, 32)
        }

class JsonManager:
    def load_shifts_file(self):
        return {}
    def save_shifts_file(self, data):
        pass
    def save_employees_file(self, data):
        pass

# Import GUI to test it
import sys
import os
sys.path.append(os.getcwd())
from interface import GUI

# Mock messagebox
GUI.messagebox = MagicMock()
GUI.messagebox.askyesno.return_value = True

def verify_locked_shifts_persistence():
    root = tk.Tk()
    
    emp_manager = EmployeesManager()
    shift_manager = ShiftManager(emp_manager)
    json_manager = JsonManager()
    config = {
        "date": {"year_range": 1},
        "shift_settings": {
            "shift_representation": {"mattina": "M", "pomeriggio": "P", "mattina_rep": "MR", "weekend_rep": "WR", "off_duty": "X"},
            "n_of_employees": {"mattina_rep": 1, "weekend_rep": 1},
            "weekend_days": [5, 6]
        },
        "employees_view": {
             "matricola": "Matricola", "cognome": "Cognome", "nome": "Nome",
             "mattina": "Mattina", "mattina_rep": "Mattina REP",
             "pomeriggio": "Pomeriggio", "weekend_rep": "Weekend REP", "off_duty": "Ferie"
        }
    }
    
    app = GUI.ShiftManagerGui(emp_manager, shift_manager, json_manager, config)
    
    # Setup state
    app.box_year_selection.set("2025")
    app.box_month_selection.set("Gennaio")
    
    print("=== Test 1: Generate schedule ===")
    app._command_schedule_generate()
    print(f"locked_shifts after generation: {len(app.locked_shifts)}")
    
    print("\n=== Test 2: Add manual assignment ===")
    # Simulate manual assignment
    date_key = datetime.date(2025, 1, 15)
    emp = emp_manager.emp_list[0]
    app.locked_shifts[(date_key.isoformat(), emp.id)] = "off_duty"
    print(f"locked_shifts after manual assignment: {len(app.locked_shifts)}")
    print(f"Manual assignment: {list(app.locked_shifts.keys())}")
    
    print("\n=== Test 3: Regenerate SAME month ===")
    app._command_schedule_generate()
    print(f"locked_shifts after regeneration: {len(app.locked_shifts)}")
    if len(app.locked_shifts) > 0:
        print("SUCCESS: locked_shifts preserved during regeneration!")
        print(f"Preserved assignment: {list(app.locked_shifts.keys())}")
    else:
        print("FAILURE: locked_shifts were cleared during regeneration!")
    
    print("\n=== Test 4: View DIFFERENT month ===")
    app.box_month_selection.set("Febbraio")
    # Mock the load to return empty
    app._command_schedule_view()
    print(f"locked_shifts after viewing different month: {len(app.locked_shifts)}")
    if len(app.locked_shifts) == 0:
        print("SUCCESS: locked_shifts cleared when viewing different month!")
    else:
        print("FAILURE: locked_shifts should be cleared when viewing different month!")

    root.destroy()

if __name__ == "__main__":
    verify_locked_shifts_persistence()
