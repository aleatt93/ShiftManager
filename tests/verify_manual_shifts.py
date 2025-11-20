
import sys
import os
import datetime
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import library
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import library

class MockJsonManager:
    def __init__(self):
        pass

    def load_employees_file(self):
        # Return a list of dummy employees
        return [
            {
                "id": 1, "surname": "Rossi", "name": "Mario", "serial_number": "001",
                "days_off": [],
                "shift_count": {"mattina": 0, "mattina_rep": 0, "pomeriggio": 0, "weekend_rep": 0}
            },
            {
                "id": 2, "surname": "Bianchi", "name": "Luigi", "serial_number": "002",
                "days_off": [],
                "shift_count": {"mattina": 0, "mattina_rep": 0, "pomeriggio": 0, "weekend_rep": 0}
            },
            {
                "id": 3, "surname": "Verdi", "name": "Anna", "serial_number": "003",
                "days_off": [],
                "shift_count": {"mattina": 0, "mattina_rep": 0, "pomeriggio": 0, "weekend_rep": 0}
            },
            {
                "id": 4, "surname": "Neri", "name": "Paolo", "serial_number": "004",
                "days_off": [],
                "shift_count": {"mattina": 0, "mattina_rep": 0, "pomeriggio": 0, "weekend_rep": 0}
            },
            {
                "id": 5, "surname": "Gialli", "name": "Luca", "serial_number": "005",
                "days_off": [],
                "shift_count": {"mattina": 0, "mattina_rep": 0, "pomeriggio": 0, "weekend_rep": 0}
            }
        ]

class TestManualShifts(unittest.TestCase):
    def setUp(self):
        # Mock JsonManager in library
        self.original_json_manager = library.JsonManager
        library.JsonManager = MockJsonManager
        
        # Setup config dict
        self.config = {
            "files": {"employees_database_file": "dummy"},
            "shift_settings": {
                "n_of_employees": {"mattina_rep": 1, "weekend_rep": 1},
                "weekend_days": [5, 6]
            }
        }
        
        # Initialize managers
        self.emp_manager = library.EmployeesManager(self.config)
        self.shift_manager = library.ShiftManager(self.emp_manager)

    def tearDown(self):
        library.JsonManager = self.original_json_manager

    def test_locked_shifts(self):
        year = 2025
        month = 1 # January
        
        # Define locks
        # Day 1 is Wednesday (Weekday)
        # Lock Rossi (1) to Mattina
        # Lock Bianchi (2) to Off Duty (X) -> This is handled by days_off in the GUI, 
        # but let's see how we simulate it here.
        # In the GUI, selecting "X" adds to days_off. So we should add to days_off manually here for the test.
        
        # Lock Verdi (3) to Pomeriggio
        
        date_str = "2025-01-01"
        date_obj = datetime.date(2025, 1, 1)
        
        # Simulate "X" selection for Bianchi
        bianchi = next(e for e in self.emp_manager.emp_list if e.id == 2)
        bianchi.days_off.append(date_obj)
        
        # Locked shifts dictionary
        locked_shifts = {
            (date_str, 1): "mattina",
            (date_str, 3): "pomeriggio"
        }
        
        # Run assignment
        success = self.shift_manager.shift_assignator(year, month, self.config, locked_shifts=locked_shifts)
        self.assertTrue(success)
        
        schedule = self.shift_manager.shift_schedule
        day_schedule = schedule[date_obj]
        
        # Verify Rossi is in Mattina
        mattina_ids = [e.id for e in day_schedule["mattina"]]
        self.assertIn(1, mattina_ids, "Rossi should be in Mattina")
        
        # Verify Verdi is in Pomeriggio
        pomeriggio_ids = [e.id for e in day_schedule["pomeriggio"]]
        self.assertIn(3, pomeriggio_ids, "Verdi should be in Pomeriggio")
        
        # Verify Bianchi is NOT in any shift for that day
        all_ids_today = []
        for shift_type in day_schedule:
            all_ids_today.extend([e.id for e in day_schedule[shift_type]])
        self.assertNotIn(2, all_ids_today, "Bianchi should not be assigned any shift")
        
        # Verify counts (at least 1 since they were assigned manually, could be more if assigned automatically on other days)
        rossi = next(e for e in self.emp_manager.emp_list if e.id == 1)
        self.assertGreaterEqual(rossi.shift_count["mattina"], 1, "Rossi morning count should be at least 1")
        
        verdi = next(e for e in self.emp_manager.emp_list if e.id == 3)
        self.assertGreaterEqual(verdi.shift_count["pomeriggio"], 1, "Verdi afternoon count should be at least 1")

if __name__ == '__main__':
    unittest.main()
