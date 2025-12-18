import py_compile
import sys
import os

files_to_check = [
    "c:\\Users\\USER\\Desktop\\EDU_PARTY_FINAL\\pygame_client_v2\\game_controller.py",
    "c:\\Users\\USER\\Desktop\\EDU_PARTY_FINAL\\pygame_client_v2\\profile_view.py",
    "c:\\Users\\USER\\Desktop\\EDU_PARTY_FINAL\\pygame_client_v2\\views\\base_view.py",
    "c:\\Users\\USER\\Desktop\\EDU_PARTY_FINAL\\pygame_client_v2\\views\\lobby_list_view.py",
    "c:\\Users\\USER\\Desktop\\EDU_PARTY_FINAL\\pygame_client_v2\\views\\lobby_settings_view.py",
    "c:\\Users\\USER\\Desktop\\EDU_PARTY_FINAL\\pygame_client_v2\\views\\in_lobby_view.py",
    "c:\\Users\\USER\\Desktop\\EDU_PARTY_FINAL\\pygame_client_v2\\network_manager.py",
    "c:\\Users\\USER\\Desktop\\EDU_PARTY_FINAL\\pygame_client_v2\\student.py"
]

print("Verifying syntax...")
for f in files_to_check:
    try:
        py_compile.compile(f, doraise=True)
        print(f"[OK] {os.path.basename(f)}")
    except py_compile.PyCompileError as e:
        print(f"[ERROR] {os.path.basename(f)}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] {os.path.basename(f)}: {e}")
        sys.exit(1)

print("\nAll files compiled successfully.")
