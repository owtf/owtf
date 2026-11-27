"""Process temporary storage must survive previous or concurrent launches."""

import os
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from owtf.utils import file as file_utils


@pytest.fixture
def storage_root(tmp_path, monkeypatch):
    original_join = file_utils.os.path.join

    def redirected_join(first, *parts):
        if first == "/tmp":
            first = str(tmp_path)
        return original_join(first, *parts)

    monkeypatch.setattr(
        file_utils,
        "os",
        SimpleNamespace(path=SimpleNamespace(join=redirected_join, exists=os.path.exists), makedirs=os.makedirs),
    )
    return tmp_path / "owtf"


def test_creates_parent_and_process_directory(storage_root):
    file_utils.create_temp_storage_dirs(123)
    assert (storage_root / "123").is_dir()


def test_creates_process_directory_when_parent_already_exists(storage_root):
    storage_root.mkdir()
    file_utils.create_temp_storage_dirs(123)
    assert (storage_root / "123").is_dir()


def test_keeps_existing_process_files_on_repeat_calls(storage_root):
    file_utils.create_temp_storage_dirs(123)
    marker = storage_root / "123" / "keep.txt"
    marker.write_text("existing data")
    file_utils.create_temp_storage_dirs(123)
    assert marker.read_text() == "existing data"


def test_separate_processes_each_get_a_directory(storage_root):
    file_utils.create_temp_storage_dirs(123)
    file_utils.create_temp_storage_dirs(456)
    assert (storage_root / "123").is_dir()
    assert (storage_root / "456").is_dir()


def test_concurrent_calls_are_idempotent(storage_root):
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(file_utils.create_temp_storage_dirs, [123] * 8))
    assert (storage_root / "123").is_dir()
