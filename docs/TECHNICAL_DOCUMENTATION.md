# Shift Manager - Technical Documentation

**Version:** 1.0
**Author:** Attura Alessio
**Date:** 10/08/2025

## 1. Overview

Shift Manager is a desktop application designed to automate the process of employee shift scheduling. It provides a graphical user interface (GUI) for managing employees, generating fair and balanced monthly shift schedules, and exporting the results to common file formats.

The application is built on a decoupled architecture, strictly separating the backend business logic (the "engine") from the frontend user interface (the "dashboard"). This design ensures the application is maintainable, testable, and scalable.

## 2. Project Structure

The project is organized into several key modules and directories:

```
Shift_Manager/
├── Data/                  # Contains all persistent data files.
│   ├── employees.json
│   └── shift_storage.json
├── Interface/             # Contains all GUI-related code.
│   ├── __init__.py
│   └── GUI.py
├── config.json            # Main configuration file for the application.
├── exporter.py            # Handles logic for exporting schedules to files.
├── file_manager.py        # Handles all file reading and writing operations.
├── library.py             # The core backend engine with all business logic.
└── main.py                # The main entry point that launches the application.
```

-   **`main.py`**: The launcher. Its sole responsibility is to initialize all the manager classes and start the GUI event loop.
-   **`library.py`**: The application's "brain." It contains the core data models (`Employee`) and business logic classes (`EmployeesManager`, `ShiftManager`). It is completely independent of the user interface.
-   **`file_manager.py`**: The persistence layer. The `JsonManager` class is the only part of the application that directly reads from or writes to the disk.
-   **`exporter.py`**: A utility module for converting schedule data into different report formats (TXT, CSV, XLSX).
-   **`Interface/GUI.py`**: The application's "dashboard." It contains all the code for the Tkinter windows, widgets, and event handling. It knows nothing about the scheduling algorithm; it only calls methods on the manager classes.
-   **`config.json`**: A user-configurable file to control application settings without changing the code.
-   **`Data/`**: The default directory for storing user data.

## 3. Core Components (Backend)

The backend is designed around the Single Responsibility Principle, where each class has one clear job.

### 3.1. `library.py` - The Engine

-   **`Employee` Class**: A simple data class that represents a single employee, holding their personal details, their list of off-duty days, and a dictionary of their accumulated shift counts.
-   **`EmployeesManager` Class**: Manages the collection of `Employee` objects in memory. It handles all business logic related to employees, such as adding a new employee, removing an employee, and calculating fair starting shift counts for new hires. It does not interact with files directly.
-   **`ShiftManager` Class**: The core scheduling engine. Its primary method, `shift_assignator`, implements the algorithm for generating a fair and balanced monthly schedule based on employee availability and historical shift counts. It now also accepts a `locked_shifts` parameter to respect manual assignments made by the user.

### 3.2. `file_manager.py` - The Persistence Layer

-   **`JsonManager` Class**: This class is responsible for all file I/O (Input/Output). It handles the loading, saving, and creation of the `config.json`, `employees.json`, and `shift_storage.json` files. It uses the **"Read -> Modify -> Write"** pattern for all updates to ensure data integrity. It also handles data transformation between Python objects (like `datetime.date`) and JSON-compatible formats (like ISO strings).

### 3.3. `exporter.py` - The Reporting Utility

-   **`Exporter` Class**: A utility class that takes a complete schedule and converts it into a universal data grid (a list of lists). It then provides methods to write this grid to various file formats (`.txt`, `.csv`, `.xlsx`), encapsulating the logic for each format.

## 4. User Interface (Frontend)

The GUI is built using Python's standard `tkinter` library with the modern `ttk` themed widgets. It is designed using a component-based architecture.

### 4.1. `Interface/GUI.py`

-   **`ShiftManagerGui(tk.Tk)` Class**: The main application class. It inherits from `tk.Tk` to become the root window.
    -   **View Management**: It manages two primary views (`frame_view_shifts` and `frame_view_employees`) and uses the `.tkraise()` method to switch between them, creating a multi-page user experience within a single window.
    -   **Event Handling**: It contains all the event handler methods (e.g., `_command_schedule_generate`, `_command_employees_add`) that connect user actions (button clicks) to the backend logic.
    -   **Dependency Injection**: It receives instances of the backend managers (`employees_manager`, `shift_manager`, `json_manager`) in its `__init__` method. This decouples the GUI from the creation of its dependencies, making the application more modular and testable.

-   **Component Classes (Nested within `ShiftManagerGui`)**:
    -   **`ScheduleTable(ttk.Frame)`**: A self-contained component that displays the monthly shift schedule. It manages its own `Treeview` widget, scrollbars, and the logic for populating itself with data. It also handles user interactions for manual shift assignment via cell clicks and dropdown menus (`_on_click`, `_on_shift_selected`).
    -   **`EmployeeTable(ttk.Frame)`**: A self-contained component for displaying the list of employees and their shift counts.
    -   **`AddEmployeeDialogWindow(tk.Toplevel)`**: A modal dialog window for adding new employees. It uses a **callback function** to communicate the new employee data back to the main GUI without being tightly coupled to it.
    -   **`Tooltip` and `AboutDialogWindow`**: Utility components for enhancing the user experience.

## 5. Data Flow and State Management

The application follows a clear data flow pattern for all major operations.

**Example: Generating a New Schedule**

1.  **User Action**: The user selects a year/month and clicks the "Genera Turni" button.
2.  **GUI Event Handler**: The `_command_schedule_generate` method is called.
3.  **Backend Call**: The handler calls `self.schedule_manager.shift_assignator()`.
4.  **In-Memory State Change**: The `shift_assignator` method runs its algorithm and updates the `shift_count` attributes of the `Employee` objects held in `self.employees_manager.emp_list`. The new schedule is stored in `self.schedule_manager.shift_schedule`.
5.  **GUI Update**: The handler retrieves the new schedule, converts it to a display-friendly format, and calls `self.schedule_table_manager.schedule_populate_table()` to refresh the view with the new data. The new schedule is also stored in `self.generated_schedule` to mark it as "unsaved."
6.  **User Action**: The user clicks the "Salva" button.
7.  **Persistence**: The `_command_schedule_save` handler calls `self.json_manager.save_shifts_file()` and `save_employees_file()`, passing the in-memory data. The `JsonManager` handles writing the updated state to the `.json` files on the disk.

**Example: Manual Shift Assignment**

1.  **User Action**: User clicks a cell in the schedule table.
2.  **GUI Event**: `ScheduleTable._on_click` is triggered, displaying a `ttk.Combobox`.
3.  **User Action**: User selects a shift (e.g., "M") or "X" (Off Duty).
4.  **GUI Event**: `ScheduleTable._on_shift_selected` is triggered.
5.  **State Update**:
    -   If "X" is selected, the date is added to `Employee.days_off`.
    -   If a shift is selected, it is added to `ShiftManagerGui.locked_shifts`.
    -   `Employee.shift_count` is updated immediately.
6.  **GUI Update**: The table cell is updated with the new value.
7.  **Subsequent Generation**: When `_command_schedule_generate` is called next, it passes `locked_shifts` to `shift_assignator`, ensuring these manual choices are preserved.

## 6. Configuration (`config.json`)

The application is configured via the `config.json` file, which allows for customization without code changes.

-   **`date`**: Controls default date settings and the range of years available in the GUI.
-   **`files`**: Defines the paths to the data files.
-   **`shift_settings`**:
    -   `shift_representation`: Maps internal shift names to the short codes displayed in the GUI and exports.
    -   `n_of_employees`: Defines the number of employees required for special shifts.
    -   `weekend_days`: Defines which days of the week are considered weekends.

## 7. Dependencies

To run this application from the source code, the following external libraries are required:

-   `openpyxl`: For exporting to Excel (.xlsx) format.
-   `reportlab`: (If PDF export is re-implemented).

These can be installed via pip:
```bash
pip install openpyxl
```