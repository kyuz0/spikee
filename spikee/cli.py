# spikee/cli.py

import argparse
import sys
import os
import shutil
import time
from dotenv import load_dotenv
from pathlib import Path

from .generator import generate_dataset
from .tester import test_dataset
from .results import analyze_results, convert_results_to_excel
from .list import list_seeds, list_datasets, list_targets, list_plugins

import importlib.resources  

banner = r'''
   _____ _____ _____ _  ________ ______ 
  / ____|  __ \_   _| |/ /  ____|  ____|
 | (___ | |__) || | | ' /| |__  | |__   
  \___ \|  ___/ | | |  < |  __| |  __|  
  ____) | |    _| |_| . \| |____| |____ 
 |_____/|_|   |_____|_|\_\______|______|
'''

# Explicitly load the .env file
env_loaded = load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

def main():
    print(banner)
    print("SPIKEE - Simple Prompt Injection Kit for Evaluation and Exploitation")
    print("Author: WithSecure Consulting\n")

    parser = argparse.ArgumentParser(
        description="SPIKEE - Simple Prompt Injection Kit for Evaluation and Exploitation"
    )

    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')

    # === [INIT] Sub-command (NEW) ==============================================
    parser_init = subparsers.add_parser('init', help='Initialize a local SPIKEE workspace')
    parser_init.add_argument('--force', action='store_true', 
                             help='Overwrite existing directories if they exist.')

    # === [GENERATE] Sub-command ===============================================
    parser_generate = subparsers.add_parser('generate', help='Generate a dataset')
    parser_generate.add_argument('--seed-folder', default='seeds-mini-test',
                                 help='Name of seed folder in local "datasets/" or built-in package data')
    parser_generate.add_argument('--positions', nargs='+', default=['end'],
                                 help='Positions to insert jailbreaks (start, middle, end)')
    parser_generate.add_argument('--injection-delimiters', default='\nINJECTION_PAYLOAD\n',
                                 help='Comma-separated list of patterns to use when injecting payloads')
    parser_generate.add_argument('--plugins', nargs='*', default=[],
                                 help='List of plugin names to modify the jailbreak+instruction text')
    parser_generate.add_argument('--standalone_attacks', default=None,
                                 help='Path to standalone_attacks.jsonl')
    parser_generate.add_argument('--format', choices=['full-prompt', 'document', 'burp'], 
                                 default='full-prompt', 
                                 help='Output format: full-prompt (default), document, or burp')
    parser_generate.add_argument('--spotlighting-data-markers', default='\nDOCUMENT\n',
                                 help='Comma-separated list of data markers (placeholder: "DOCUMENT")')
    parser_generate.add_argument('--languages', default=None,
                                 help='Comma-separated list of languages to filter jailbreaks and instructions')
    parser_generate.add_argument('--match-languages', action='store_true',
                                 help='Only combine jailbreaks and instructions with matching languages')
    parser_generate.add_argument('--instruction-filter', default=None,
                                 help='Comma-separated list of instruction types to include')
    parser_generate.add_argument('--jailbreak-filter', default=None,
                                 help='Comma-separated list of jailbreak types to include')
    parser_generate.add_argument('--include-suffixes', action='store_true',
                                 help='Include advanced suffixes in the dataset generation')
    parser_generate.add_argument('--include-system-message', action='store_true',
                                 help='Include system message based on system_messages.toml')

    # === [TEST] Sub-command ===================================================
    parser_test = subparsers.add_parser('test', help='Test the dataset against a target')
    parser_test.add_argument('--dataset', type=str, required=True,
                             help='Path to the dataset file (local workspace)')
    parser_test.add_argument('--target', type=str, required=True,
                             help='Name of the target to test (in local or built-in targets/ dir)')
    parser_test.add_argument('--threads', type=int, default=4, 
                             help='Number of threads for parallel processing')
    parser_test.add_argument('--attempts', type=int, default=1,
                             help='Number of attempts per payload (default: 1)')
    parser_test.add_argument('--success-criteria', default='canary', choices=['canary', 'boolean'],
                             help='Criteria to determine success (default: canary)')
    parser_test.add_argument('--resume-file', type=str, default=None,
                             help='Path to a results JSONL file to resume from')
    parser_test.add_argument('--throttle', type=float, default=0,
                             help='Time in seconds to wait between requests per thread')

    # === [RESULTS] Sub-command ================================================
    parser_results = subparsers.add_parser('results', help='Analyze or convert results')
    subparsers_results = parser_results.add_subparsers(dest='results_command',
                                                       help='Results sub-commands')

    # --- analyze
    parser_analyze = subparsers_results.add_parser('analyze', help='Analyze the results JSONL file')
    parser_analyze.add_argument('--result-file', type=str, required=True,
                                help='Path to the results JSONL file')
    parser_analyze.add_argument('--output-format', choices=['console', 'html'], default='console',
                                help='Output format: console (default) or html')

    # --- convert-to-excel
    parser_convert_to_excel = subparsers_results.add_parser('convert-to-excel',
                                                            help='Convert results JSONL file to Excel')
    parser_convert_to_excel.add_argument('--result-file', type=str, required=True,
                                         help='Path to the results JSONL file')

    # === [LIST] Sub-command ================================================
    parser_list = subparsers.add_parser('list', help='List seeds, datasets, targets, or plugins')
    list_subparsers = parser_list.add_subparsers(dest='list_command', help='What to list')

    parser_list_seeds = list_subparsers.add_parser('seeds', help='List available seed folders')
    parser_list_datasets = list_subparsers.add_parser('datasets', help='List available dataset .jsonl files')
    parser_list_targets = list_subparsers.add_parser('targets', help='List available targets')
    parser_list_plugins = list_subparsers.add_parser('plugins', help='List available plugins')


    args = parser.parse_args()

    if args.command == 'init':
        init_workspace(force=args.force)  

    elif args.command == 'generate':
        generate_dataset(args)  
    elif args.command == 'test':
        test_dataset(args)      
    elif args.command == 'results':
        if args.results_command == 'analyze':
            analyze_results(args)
        elif args.results_command == 'convert-to-excel':
            convert_results_to_excel(args)
        else:
            parser_results.print_help()
    elif args.command == 'list':
        if args.list_command == 'seeds':
            list_seeds(args)
        elif args.list_command == 'datasets':
            list_datasets(args)
        elif args.list_command == 'targets':
            list_targets(args)
        elif args.list_command == 'plugins':
            list_plugins(args)
        else:
            parser_list.print_help()
    else:
        parser.print_help()
        sys.exit(1)

def init_workspace(force=False):
    """
    Copy the entire 'data/workspace' directory from the installed package
    into the user's current working directory. This sets up the local spikee workspace
    (datasets, plugins, targets, env-example, etc.).
    """
    cwd = Path(os.getcwd())
    workspace_dest = cwd  

    src_folder = Path(__file__).parent / "data" / "workspace"

    # If not forcing, ensure we don't overwrite any existing files/folders
    # We'll do this by manually copying sub-items, skipping if they exist.
    for item in src_folder.iterdir():
        destination = workspace_dest / item.name

        if destination.exists() and not force:
            print(f"[init] '{destination}' already exists. Use --force to overwrite.")
            continue

        # If force and destination is a directory, remove it first
        if destination.exists() and force:
            if destination.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()

        try:
            if item.is_dir():
                shutil.copytree(item, destination)
            else:
                shutil.copy2(item, destination)
            print(f"[init] Copied {item.name} --> {destination}")
        except Exception as e:
            print(f"[init] Could not copy {item.name} to {destination}: {e}")

    print("[init] Local spikee workspace has been initialized.")
