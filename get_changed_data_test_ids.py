import os
import re
import subprocess
from collections import defaultdict

# ANSI escape codes for colors and formatting
BOLD = '\033[1m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def color_print(text, color=RESET, bold=False):
    formatting = BOLD if bold else ''
    print(f"{formatting}{color}{text}{RESET}")

def get_current_branch():
    return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()

def normalize_id(id_value):
    return re.sub(r'[\s,]+', '', id_value)

def find_test_ids(directory):
    test_ids = defaultdict(lambda: defaultdict(list))
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.jsx', '.tsx')):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    data_test_id_pattern = r'data-test-id=(?:\"([^\"]*)\"|{`([^`]*)`}|{([^}]+)})'
                    data_testid_pattern = r'data-testid=(?:\"([^\"]*)\"|{`([^`]*)`}|{([^}]+)})'
                    
                    for pattern, id_type in [(data_test_id_pattern, 'data-test-id'), (data_testid_pattern, 'data-testid')]:
                        for match in re.finditer(pattern, content):
                            id_value = next(group for group in match.groups() if group is not None)
                            normalized_id = normalize_id(id_value)
                            test_ids[id_type][normalized_id].append((id_value, file_path))
    return test_ids

def checkout_branch(branch):
    subprocess.run(['git', 'checkout', branch], check=True)

def compare_test_ids(current_ids, master_ids):
    only_in_current = set(current_ids.keys()) - set(master_ids.keys())
    only_in_master = set(master_ids.keys()) - set(current_ids.keys())
    in_both_diff_count = {
        id: (len(current_ids[id]), len(master_ids[id]))
        for id in set(current_ids.keys()) & set(master_ids.keys())
        if len(current_ids[id]) != len(master_ids[id])
    }
    return only_in_current, only_in_master, in_both_diff_count

def main():
    current_branch = get_current_branch()
    color_print(f"Current branch: {current_branch}", BLUE, bold=True)

    color_print("Checking out master branch...", YELLOW)
    checkout_branch('master')
    
    color_print("Finding test IDs in master branch...", YELLOW)
    master_test_ids = find_test_ids('.')
    
    color_print(f"Checking out {current_branch} branch...", YELLOW)
    checkout_branch(current_branch)
    
    color_print(f"Finding test IDs in {current_branch} branch...", YELLOW)
    current_test_ids = find_test_ids('.')

    for id_type in ['data-test-id', 'data-testid']:
        color_print(f"\nComparing {id_type}:", BLUE, bold=True)
        only_in_current, only_in_master, in_both_diff_count = compare_test_ids(current_test_ids[id_type], master_test_ids[id_type])
        
        if only_in_current:
            color_print(f"IDs only in {current_branch}:", GREEN, bold=True)
            for normalized_id in only_in_current:
                instances = current_test_ids[id_type][normalized_id]
                print(f"  {normalized_id} (Count: {len(instances)})")
                for orig_id, file_path in instances:
                    print(f"    - {orig_id} in {file_path}")
        
        if only_in_master:
            color_print("IDs only in master:", RED, bold=True)
            for normalized_id in only_in_master:
                instances = master_test_ids[id_type][normalized_id]
                print(f"  {normalized_id} (Count: {len(instances)})")
                for orig_id, file_path in instances:
                    print(f"    - {orig_id} in {file_path}")
        
        if in_both_diff_count:
            color_print("IDs in both branches but with different counts:", YELLOW, bold=True)
            for normalized_id, (current_count, master_count) in in_both_diff_count.items():
                print(f"  {normalized_id} (Count in {current_branch}: {current_count}, Count in master: {master_count})")
                print(f"    In {current_branch}:")
                for orig_id, file_path in current_test_ids[id_type][normalized_id]:
                    print(f"      - {orig_id} in {file_path}")
                print("    In master:")
                for orig_id, file_path in master_test_ids[id_type][normalized_id]:
                    print(f"      - {orig_id} in {file_path}")
        
        color_print("\nSummary:", BLUE, bold=True)
        print(f"Total unique IDs in {current_branch}: {len(current_test_ids[id_type])}")
        print(f"Total unique IDs in master: {len(master_test_ids[id_type])}")
        print(f"Total instances in {current_branch}: {sum(len(instances) for instances in current_test_ids[id_type].values())}")
        print(f"Total instances in master: {sum(len(instances) for instances in master_test_ids[id_type].values())}")

if __name__ == "__main__":
    main()
