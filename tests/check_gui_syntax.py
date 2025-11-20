
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import interface.GUI
    print("GUI imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    # Tkinter might fail to initialize without a display, but we want to catch SyntaxErrors
    print(f"Exception during import (expected if no display): {e}")
