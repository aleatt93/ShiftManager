# Shift Manager v2.1

Shift Manager is a user-friendly desktop application designed to simplify and automate the process of creating and managing monthly employee shift schedules. It provides a clean graphical interface to handle employee data, generate fair and balanced schedules, and export them to common formats.

This tool was created to help managers save time and reduce the complexity of manual scheduling, ensuring a fair distribution of shifts among all employees.

![Shift Manager Screenshot](placeholder.png)

---

## Features

-   **Employee Management:** Add, remove, and view a list of all employees and their cumulative shift counts.
-   **Automated Schedule Generation:** Generate a complete monthly shift schedule with a single click. The algorithm ensures a fair distribution of morning, afternoon, and special shifts.
-   **Days Off Management:** Easily account for employee vacations and off-duty days, which are automatically excluded from the schedule generation.
-   **Manual Shift Assignment:** Manually assign shifts or set days off directly from the schedule table using a dropdown menu. These assignments are respected during automated generation.
-   **Persistent Data:** All employee data and generated schedules are saved locally, so your work is always preserved.
-   **Multiple Views:** Switch seamlessly between the monthly schedule view and the employee management list.
-   **Data Export:** Export the generated monthly schedule to multiple formats for easy sharing and printing:
    -   Formatted Plain Text (`.txt`)
    -   CSV (`.csv`)
    -   Microsoft Excel (`.xlsx`)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

To run the application from the source code, you will need to have Python 3 installed on your system. You will also need the following Python libraries:

-   `openpyxl` (for Excel export)

You can install the required libraries using pip:

```bash
pip install openpyxl
```

### Installation & Running the Application

1.  **Clone the repository or download the source code.**
    If you have Git installed, you can use:
    ```bash
    git clone https://github.com/aleatt93/ShiftManager.git
    cd ShiftManager
    ```
    Otherwise, download the ZIP file and extract it.

2.  **Install dependencies.**
    Navigate to the project's root directory in your terminal and run the installation command from the prerequisites section.

3.  **Run the application.**
    Execute the `main.py` script to launch the GUI:
    ```bash
    python main.py
    ```

## How to Use

The application is designed to be intuitive and straightforward.

### First-Time Setup

When you run the application for the first time, it will automatically create a `config.json` file and a `Data` folder containing `employees.json` and `shift_storage.json`.

1.  Navigate to the **Impiegati** (Employees) view using the menu bar.
2.  Click the **"Aggiungi"** (Add) button to open the dialog and add your employees one by one.
3.  After adding all employees, click the **"Salva"** (Save) button to write the employee list to the disk.

### Generating a Schedule

1.  Navigate to the **Turni** (Shifts) view.
2.  Select the desired **Anno** (Year) and **Mese** (Month) from the dropdown menus.
3.  Click the **"Genera Turni"** (Generate Shifts) button. The table will be populated with the new schedule.
4.  Click the **"Salva"** (Save) button to save both the generated schedule and the updated employee shift counts to the disk.

### Manual Shift Assignment

You can manually assign shifts or set employees as "Off Duty" before or after generating a schedule:

1.  Click on any cell in the schedule table corresponding to an employee and a date.
2.  A dropdown menu will appear with the following options:
    -   **Shift Types (M, P, etc.):** Assigns the selected shift to the employee. This "locks" the assignment, ensuring the automated generator respects it.
    -   **X (Off Duty):** Marks the employee as unavailable for that day.
    -   **Empty:** Clears any manual assignment.
3.  The employee's shift counts will update immediately to reflect your changes.

### Viewing and Exporting

-   To view a previously saved schedule, select the year and month and click **"Visualizza"** (View).
-   To export the currently displayed schedule, use the **Esporta** (Export) menu and select your desired format. The application will prompt you to choose a location to save the file.

## Version History

### v2.1 (Current)

**Critical Bug Fixes:**
- Fixed manual shift assignments being lost visually after regenerating schedules
- Fixed shift counters updating immediately upon generation (now only update on save)
- Fixed multiple `AttributeError` issues on application startup

**New Features:**
- Added "Ferie" (Days Off) column to employee view to track off-duty days
- Manual shift assignments now have priority over generated shifts
- Improved temporary state management during schedule generation

**Technical Improvements:**
- Implemented shift counter decoupling logic
- Added `locked_shifts` persistence across regenerations
- Enhanced `schedule_populate_table` to check manual assignments first
- Added month tracking to prevent clearing manual assignments unnecessarily

**Known Issues:**
- Export function has minor bugs (to be fixed in v2.2)

### v2.0
- Initial release with core scheduling functionality
- Employee management system
- Automated schedule generation
- Manual shift assignment capabilities

## Built With

-   **Python 3** - The core programming language.
-   **Tkinter / ttk** - Python's standard library for the graphical user interface.
-   **PyInstaller** (for creating the executable) - A tool to bundle a Python application and all its dependencies into a single package.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

*   **Attura Alessio** - *Initial work & development*

## Acknowledgments

*   A special thanks to my partner, whose need for a better scheduling tool inspired this project.
*   To my mentor, for the guidance and patience throughout the development process.