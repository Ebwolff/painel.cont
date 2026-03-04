import os
import sys

def search_for_status_erro(start_dir):
    print(f"Searching for 'status' and 'erro' in {start_dir}...")
    for root, dirs, files in os.walk(start_dir):
        if 'node_modules' in dirs: dirs.remove('node_modules')
        if '.git' in dirs: dirs.remove('.git')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        
        for file in files:
            if file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.sql')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if 'status' in line.lower() and 'erro' in line.lower():
                                print(f"{path}:{i+1} -> {line.strip()}")
                except Exception as e:
                    pass

if __name__ == '__main__':
    search_for_status_erro(os.path.dirname(os.path.dirname(__file__)))
