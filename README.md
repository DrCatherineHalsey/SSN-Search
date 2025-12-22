# Optimized Search Script (optimized_search.py)

This Python script provides an efficient way to search through large datasets of personal information stored in multiple files. It is designed to handle Social Security Number (SSN) data and other related personal information.

## Features

- Multi-term search capability
- Optimized for large datasets using memory mapping
- Multi-processing for improved performance
- Customizable maximum results
- Formatted output for easy readability

## How it Works

1. The script searches through all files in the specified directory that start with 'part_'.
2. It uses memory mapping (mmap) to efficiently read large files.
3. The search is performed using regular expressions, allowing for case-insensitive, multi-term searches.
4. Multi-processing is utilized to search multiple files concurrently, improving performance.
5. Results are formatted for easy reading, including:
   - Full name (uppercase)
   - Date of Birth (DOB)
   - Address (including county if available)
   - Phone number (formatted)
   - Alternate DOBs
   - Social Security Number (SSN) (formatted)

## Usage

1. Run the script:
   ```
   python optimized_search.py
   ```
2. When prompted, enter your search terms separated by pipes (|). For example:
   ```
   JOHN | DOE | 1980
   ```
3. The script will display the search progress and results.

## Note

- The script no longer assumes files are located in '/Path/To/SSN/Files'. By default the script looks for files in the `./data` directory. You can modify the `DOCUMENT_PATH` variable in the script, set the `SSN_DOCUMENT_PATH` environment variable, or pass a different path with the `--path` (`-p`) option. Files must start with `part_`.
- The script is designed to work with CSV files where each line represents a person's information in a specific format. Ensure your data files match this expected format.

- If SSNs appear in a different field position in your CSV, use the `--ssn-index` option (0-based) to point to the correct field — default is `19`.
- For troubleshooting, use `--debug` to print the raw parsed fields and the SSN extraction for each match.

## Example

- Run with the default path in `./data`:

  python optimized_search.py "ryan|biggers|1983" -m 5

- Override the data path or SSN field index:

  python optimized_search.py "ann|smith|1990" -p ./my_files --ssn-index 10 --debug

These examples show how to override the data location and SSN index for cases where the SSN is stored in a different CSV field.

## Performance

The script is optimized for performance when dealing with large datasets:
- It uses memory mapping to efficiently read large files without loading them entirely into memory.
- Multi-processing is employed to search multiple files concurrently.
- The search stops as soon as the maximum number of results is reached, avoiding unnecessary processing.

## Caution

This script handles sensitive personal information. Ensure that you have the necessary permissions and are complying with all relevant data protection regulations when using this script.
