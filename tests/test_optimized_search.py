import os

from optimized_search import optimized_search


def test_ssn_index_and_path_override(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Standard CSV where SSN is at index 19
    line = "1,Ryan,,Biggers,,19830115,123 Main St,Springfield,SomeCounty,IL,62704,2175551234,x,x,x,x,19900101,19910101,19920101,123456789"
    (data_dir / "part_1.csv").write_text(line + "\n")

    results = optimized_search(["ryan", "biggers", "1983"], max_results=5, document_path=str(data_dir), ssn_index=19, debug=False)
    assert results, "No results found"
    assert any("SSN: 123-45-6789" in r for r in results)


def test_ssn_index_variation(tmp_path):
    data_dir = tmp_path / "data2"
    data_dir.mkdir()

    # Place SSN at index 10 (0-based)
    fields = ['1', 'Ann', '', 'Smith', '', '19900101', '123 Repo St', 'City', 'County', 'ST', '012345678', '5550001111', 'x', 'x', 'x', 'x', '20000101', '20010101', '20020101', '']
    line = ",".join(fields)
    (data_dir / "part_1.csv").write_text(line + "\n")

    results = optimized_search(["ann", "smith", "1990"], max_results=5, document_path=str(data_dir), ssn_index=10, debug=False)
    assert results, "No results found for ann smith"
    assert any("SSN: 012-34-5678" in r for r in results)
