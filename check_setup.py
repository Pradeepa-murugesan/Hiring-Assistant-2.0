import os
import sys

print("--- STARTING SETUP CHECK ---")

# --- 1. Check Current Location ---
current_working_directory = os.getcwd()
print(f"\n[INFO] You are running this script from: {current_working_directory}")

# --- 2. Check Project Root ---
project_root = os.path.dirname(os.path.abspath(__file__))
print(f"[INFO] The script believes the project root is: {project_root}")

if project_root != current_working_directory:
    print("\n[WARNING] You are not running the script from the same directory it is in. This can cause issues.")
    print(f"Please 'cd' into this directory: {project_root}")

# --- 3. Check Python's Search Path ---
print("\n[INFO] Python is currently looking for modules in these places (sys.path):")
for path in sys.path:
    print(f"  - {path}")

# --- 4. Check for 'src' Directory ---
src_path = os.path.join(project_root, 'src')
print(f"\n[INFO] Checking for 'src' directory at: {src_path}")
if os.path.isdir(src_path):
    print("[SUCCESS] 'src' directory found.")
    
    # --- 5. Check contents of 'src' ---
    try:
        src_contents = os.listdir(src_path)
        print(f"[INFO] Contents of 'src': {src_contents}")
        if '__init__.py' not in src_contents:
            print("[ERROR] CRITICAL: 'src/__init__.py' is MISSING.")
        else:
            print("[SUCCESS] 'src/__init__.py' found.")
            
        # --- 6. Check for 'src/utils' and its contents ---
        utils_path = os.path.join(src_path, 'utils')
        if 'utils' in src_contents and os.path.isdir(utils_path):
            print("\n[SUCCESS] 'src/utils' directory found.")
            utils_contents = os.listdir(utils_path)
            print(f"[INFO] Contents of 'src/utils': {utils_contents}")
            
            if '__init__.py' not in utils_contents:
                print("[ERROR] CRITICAL: 'src/utils/__init__.py' is MISSING.")
            else:
                print("[SUCCESS] 'src/utils/__init__.py' found.")
                
            if 'pdf_parser.py' not in utils_contents:
                 print("[ERROR] CRITICAL: 'src/utils/pdf_parser.py' is MISSING.")
            else:
                 print("[SUCCESS] 'src/utils/pdf_parser.py' found.")
        else:
            print("[ERROR] CRITICAL: 'src/utils' directory is MISSING.")
            
    except Exception as e:
        print(f"[ERROR] Could not read contents of 'src' directory: {e}")

else:
    print("[ERROR] CRITICAL: The 'src' directory was NOT FOUND where expected.")


print("\n--- CHECK COMPLETE ---")