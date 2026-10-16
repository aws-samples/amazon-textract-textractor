from pathlib import Path


def test_py_typed_marker_exists():
    marker = Path(__file__).resolve().parents[1] / "textractor" / "py.typed"
    assert marker.is_file()


def test_public_api_exports():
    import textractor

    assert textractor.__all__ == ["Document", "LazyDocument", "Textractor"]
    assert textractor.Textractor is not None
    assert textractor.Document is not None
    assert textractor.LazyDocument is not None
