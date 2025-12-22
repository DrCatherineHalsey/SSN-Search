import os
import tempfile

from optimized_search import optimized_search


def write_part(path, name, lines):
    p = path / name
    p.write_text("\n".join(lines) + "\n")
    return p


def test_malformed_ssn_non_digits(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    # SSN with letters and dashes
    line = "1,John,,Doe,,19800101,1 Main St,City,County,ST,12345,5550000000,x,x,x,x,20000101,20010101,20020101,12A-45-678"
    write_part(d, "part_1.csv", [line])

    results = optimized_search(["john", "doe", "1980"], max_results=5, document_path=str(d), ssn_index=19)
    assert results, "No results for malformed SSN"
    assert any("SSN: 124-56-78" not in r for r in results)  # basic sanity: formatting shouldn't invent digits


def test_quoted_fields_and_commas(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    # Address contains a comma and is quoted; SSN at default index
    line = '1,"Jane, A.",,Smith,,19950202,"1234, Apt 5",Town,County,ST,54321,5550001234,x,x,x,x,20050202,20060202,20070202,987654321'
    write_part(d, "part_1.csv", [line])

    results = optimized_search(["jane", "smith", "1995"], max_results=5, document_path=str(d), ssn_index=19)
    assert results, "No results for quoted fields"
    assert any("SSN: 987-65-4321" in r for r in results)


def test_missing_ssn_field(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    # Line too short (no SSN field)
    line = "1,Short,,Line,,19900101,Addr,City,County,ST,00000,5550001111"
    write_part(d, "part_1.csv", [line])

    results = optimized_search(["short", "line", "1990"], max_results=5, document_path=str(d), ssn_index=19)
    # Should return a result but no SSN line appended
    assert results, "No results for short line"
    assert all("SSN:" not in r for r in results)


def test_large_file_performance(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    lines = []
    for i in range(1000):
        lines.append(f"{i},User,,Number,,19700101,Addr{i},City,County,ST,0000{i},555000{i:04d},x,x,x,x,19800101,19810101,19820101,{i:09d}")
    write_part(d, "part_1.csv", lines)

    results = optimized_search(["user", "number", "1970"], max_results=10, document_path=str(d), ssn_index=19)
    assert results, "No results found in large file"
    assert len(results) <= 10
