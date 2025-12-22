import os
import mmap
import re
import multiprocessing
import argparse
import csv
from datetime import datetime
import time

# Default path for the documents (override with SSN_DOCUMENT_PATH env var or --path)
DOCUMENT_PATH = os.environ.get('SSN_DOCUMENT_PATH', './data')

def format_ssn(ssn):
    # Normalize SSN by removing non-digit chars and preserving leading zeros
    digits = re.sub(r"\D", "", ssn or "")
    if len(digits) == 9:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    # If not a 9-digit number, return the cleaned version (or original) for visibility
    return digits if digits else ssn

def format_phone(phone):
    if len(phone) == 10:
        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
    return phone

def search_chunk(args):
    file_path, pattern_str, max_results, ssn_index, debug = args
    results = []

    try:
        with open(file_path, 'rb') as f:
            try:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            except ValueError:
                # Empty file
                return results

            search_regex = re.compile(pattern_str)
            csv_reader = csv.reader
            for line in iter(mm.readline, b''):
                if len(results) >= max_results:
                    break
                raw_line = line.decode('utf-8', errors='ignore')
                if search_regex.search(raw_line):
                    try:
                        fields = next(csv_reader([raw_line]))
                    except Exception:
                        # Fallback to naive split if csv parsing fails
                        fields = raw_line.strip().split(',')

                    # Allow short lines; we'll format what we can
                    if len(fields) >= 2:  # minimal requirement for a name/search match
                        formatted_fields = []

                        # Format name (fields 1-4) — guard against missing indices
                        name_parts = []
                        for part in fields[1:5]:
                            if part and part.strip():
                                name_parts.append(part.strip())
                        name = " ".join(name_parts).upper() if name_parts else ""
                        if name:
                            formatted_fields.append(name)

                        # Format DOB (field 5) if present
                        if len(fields) > 5 and fields[5].strip():
                            try:
                                dob = datetime.strptime(fields[5].strip(), "%Y%m%d")
                                formatted_fields.append(f"DOB: {dob.strftime('%m/%d/%Y')}")
                            except ValueError:
                                formatted_fields.append(f"DOB: {fields[5].strip()}")

                        # Format address (fields 6-10) with safety checks
                        if len(fields) > 6 and fields[6].strip():
                            formatted_fields.append(fields[6].strip())  # Street address
                        city = fields[7].strip() if len(fields) > 7 else ''
                        state = fields[9].strip() if len(fields) > 9 else ''
                        zipc = fields[10].strip() if len(fields) > 10 else ''
                        if city or state or zipc:
                            formatted_fields.append(f"{city}, {state} {zipc}".strip(', '))
                        if len(fields) > 8 and fields[8].strip():  # county
                            formatted_fields.append(fields[8].strip().upper())

                        # Add phone (field 11)
                        if len(fields) > 11 and fields[11].strip():
                            formatted_fields.append(f"Phone: {format_phone(fields[11].strip())}")

                        # Add alternate DOBs (fields 16-18)
                        for i, alt_dob in enumerate(fields[16:19], 1):
                            if alt_dob.strip():
                                try:
                                    dob = datetime.strptime(alt_dob.strip(), "%Y%m%d")
                                    formatted_fields.append(f"Alt DOB {i}: {dob.strftime('%m/%d/%Y')}")
                                except ValueError:
                                    formatted_fields.append(f"Alt DOB {i}: {alt_dob.strip()}")

                        # Extract SSN safely using configurable index
                        ssn_raw = fields[ssn_index].strip() if len(fields) > ssn_index else ''
                        # If debug mode is enabled, show raw fields and SSN extract
                        if debug:
                            formatted_fields.insert(0, f"RAW_FIELDS: {fields}")
                            formatted_fields.insert(1, f"SSN raw at index {ssn_index}: {ssn_raw}")

                        if ssn_raw:
                            formatted_fields.append(f"SSN: {format_ssn(ssn_raw)}")

                        # Only add non-empty formatted results
                        if formatted_fields:
                            results.append("\n".join(formatted_fields))
            mm.close()
    except (OSError, IOError):
        # Could not open or mmap the file; skip it
        return results

    return results

def optimized_search(search_terms, max_results=100, document_path=DOCUMENT_PATH, ssn_index=19, debug=False):
    try:
        all_files = [os.path.join(document_path, f) for f in os.listdir(document_path) if f.startswith('part_')]
    except FileNotFoundError:
        raise FileNotFoundError(f"Document path '{document_path}' does not exist or is not accessible. Provide a valid path with --path or set SSN_DOCUMENT_PATH.")

    # Sort files to ensure consistent ordering
    all_files.sort()

    # Create a regex pattern string for efficient searching (compiled in worker)
    pattern_str = r'(?i)' + r'.*'.join(re.escape(term) for term in search_terms)

    results = []
    if not all_files:
        return results

    # Create a pool of worker processes
    with multiprocessing.Pool() as pool:
        args_iterable = [(file, pattern_str, max_results, ssn_index, debug) for file in all_files]
        for chunk_results in pool.imap_unordered(search_chunk, args_iterable):
            results.extend(chunk_results)
            if len(results) >= max_results:
                pool.close()
                pool.join()
                break

    return results[:max_results]

def main():
    parser = argparse.ArgumentParser(description='Search SSN files for given terms.')
    parser.add_argument('terms', nargs='*', help='Search terms separated by pipes (|) or as separate args')
    parser.add_argument('-p', '--path', default=os.environ.get('SSN_DOCUMENT_PATH', './data'), help='Path to document files')
    parser.add_argument('-m', '--max-results', type=int, default=100, help='Maximum number of results to return')
    parser.add_argument('--ssn-index', type=int, default=19, help='0-based index of the SSN field (default: 19)')
    parser.add_argument('--debug', action='store_true', help='Show raw parsed fields and SSN extraction for matches')
    args = parser.parse_args()

    if args.terms:
        # Allow passing terms as separate args or a single pipe-separated string
        search_terms = []
        for t in args.terms:
            for part in t.split('|'):
                if part.strip():
                    search_terms.append(part.strip())
    else:
        print("Enter your search terms separated by pipes (|):")
        search_input = input().strip()
        search_terms = [term.strip() for term in search_input.split('|') if term.strip()]

    print(f"Searching for: {', '.join(search_terms)}")
    print("This may take a while. Please wait...")

    start_time = time.time()
    try:
        results = optimized_search(search_terms, max_results=args.max_results, document_path=args.path, ssn_index=args.ssn_index, debug=args.debug)
    except FileNotFoundError as e:
        print(str(e))
        return
    end_time = time.time()

    print(f"\nSearch completed in {end_time - start_time:.2f} seconds.")
    print(f"Found {len(results)} matches.\n")

    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(result)
        print()

    print(f"Total results: {len(results)}")

if __name__ == "__main__":
    main()
