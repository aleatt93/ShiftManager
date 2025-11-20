import library
from interface import GUI

if __name__ == "__main__":
    # Caricamento gestori
    file_manager = library.JsonManager()
    configuration = file_manager.load_config_file()
    employees_manager = library.EmployeesManager(configuration)
    shift_manager = library.ShiftManager(employees_manager)
    gui = GUI.ShiftManagerGui(employees_manager,
                              shift_manager,
                              file_manager,
                              configuration)

    gui.mainloop()

    # +++ TESTING +++
    # test_machine = library.ShiftGeneratorTest(employees_manager)
