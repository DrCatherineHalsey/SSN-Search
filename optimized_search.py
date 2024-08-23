import os
import mmap
import re
import multiprocessing
from datetime import datetime
import time

# Set the correct path for the documents
DOCUMENT_PATH = '/Path/To/SSN/Files'

def format_ssn(ssn):
    if len(ssn) == 9:
        return f"{ssn[:3]}-{ssn[3:5]}-{ssn[5:]}"
    return ssn

def format_phone(phone):
    if len(phone) == 10:
        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
    return phone

def search_chunk(args):
    file_path, search_regex, max_results = args
    results = []
    
    with open(file_path, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        for line in iter(mm.readline, b''):
            if len(results) >= max_results:
                break
            line = line.decode('utf-8', errors='ignore')
            if search_regex.search(line):
                fields = line.strip().split(',')
                if len(fields) >= 20:
                    formatted_fields = []
                    
                    # Format name (fields 1-4)
                    name_parts = [part.strip() for part in fields[1:5] if part.strip()]
                    name = " ".join(name_parts).upper()
                    formatted_fields.append(name)
                    
                    # Format DOB (field 5)
                    if fields[5].strip():
                        try:
                            dob = datetime.strptime(fields[5].strip(), "%Y%m%d")
                            formatted_fields.append(f"DOB: {dob.strftime('%m/%d/%Y')}")
                        except ValueError:
                            formatted_fields.append(f"DOB: {fields[5].strip()}")
                    
                    # Format address (fields 6-10)
                    formatted_fields.append(fields[6].strip())  # Street address
                    formatted_fields.append(f"{fields[7].strip()}, {fields[9].strip()} {fields[10].strip()}")  # City, State ZIP
                    if fields[8].strip():  # If county is present
                        formatted_fields.append(fields[8].strip().upper())  # County on a separate line
                    
                    # Add phone (field 11)
                    if fields[11].strip():
                        formatted_fields.append(f"Phone: {format_phone(fields[11].strip())}")
                    
                    # Add alternate DOBs (fields 16-18)
                    for i, alt_dob in enumerate(fields[16:19], 1):
                        if alt_dob.strip():
                            try:
                                dob = datetime.strptime(alt_dob.strip(), "%Y%m%d")
                                formatted_fields.append(f"Alt DOB {i}: {dob.strftime('%m/%d/%Y')}")
                            except ValueError:
                                formatted_fields.append(f"Alt DOB {i}: {alt_dob.strip()}")
                    
                    # Add SSN (field 19)
                    if fields[19].strip():
                        formatted_fields.append(f"SSN: {format_ssn(fields[19].strip())}")
                    
                    results.append("\n".join(formatted_fields))
        mm.close()
    
    return results

def optimized_search(search_terms, max_results=100):
    all_files = [os.path.join(DOCUMENT_PATH, f) for f in os.listdir(DOCUMENT_PATH) if f.startswith('part_')]
    
    # Sort files to ensure consistent ordering
    all_files.sort()
    
    # Create a regex pattern for efficient searching
    pattern = r'(?i)' + r'.*'.join(re.escape(term) for term in search_terms)
    search_regex = re.compile(pattern)
    
    # Create a pool of worker processes
    with multiprocessing.Pool() as pool:
        # Map the search function to all files
        results = []
        for chunk_results in pool.imap_unordered(search_chunk, [(file, search_regex, max_results) for file in all_files]):
            results.extend(chunk_results)
            if len(results) >= max_results:
                pool.terminate()
                break
    
    return results[:max_results]

def main():
    print("Enter your search terms separated by pipes (|):")
    search_input = input().strip()
    search_terms = [term.strip() for term in search_input.split('|')]
    
    print(f"Searching for: {', '.join(search_terms)}")
    print("This may take a while. Please wait...")
    
    start_time = time.time()
    results = optimized_search(search_terms)
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
