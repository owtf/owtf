from pathlib import Path

from owtf.utils.file import FileOperations


def test_creates_full_path_longer_than_255_characters(tmp_path):
    path = tmp_path / ("a" * 100) / ("b" * 100) / ("c" * 100)
    assert len(str(path)) > 255
    FileOperations.create_missing_dirs(str(path))
    assert path.is_dir()
    FileOperations.create_missing_dirs(str(path))
    assert path.is_dir()


def test_dump_file_uses_the_full_nested_directory(tmp_path):
    path = tmp_path / ("a" * 100) / ("b" * 100) / ("c" * 100)
    saved = FileOperations.dump_file("report.txt", "scan output", str(path))
    assert Path(saved).read_text() == "scan output"
    assert Path(saved).parent == path


def test_existing_file_path_uses_its_parent_directory(tmp_path):
    path = tmp_path / "existing.txt"
    path.write_text("keep")
    FileOperations.create_missing_dirs(str(path))
    assert path.read_text() == "keep"
