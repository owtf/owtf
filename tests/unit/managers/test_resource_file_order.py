"""Resource execution order must follow the profile, with duplicates removed."""

from unittest import mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from owtf.models.resource import Resource


@pytest.fixture
def resource_manager():
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers import resource
    return resource


@pytest.fixture
def profile(tmp_path):
    path = tmp_path / "resources.cfg"
    path.write_text(
        "# Command order matters\n"
        "scan_____Run_____run-scanner\n"
        "scan_____ExtractURLs_____extract-urls\n"
        "scan_____Run_____run-scanner\n"
        "scan_____Report_____write-report\n"
    )
    return path


def test_parser_preserves_first_occurrence_order(resource_manager, profile):
    assert list(resource_manager.get_resources_from_file(profile)) == [
        ("scan", "Run", "run-scanner"),
        ("scan", "ExtractURLs", "extract-urls"),
        ("scan", "Report", "write-report"),
    ]


@pytest.mark.parametrize("use_fallback", [False, True])
def test_database_reload_preserves_command_order(resource_manager, profile, tmp_path, use_fallback):
    engine = create_engine("sqlite:///:memory:")
    Resource.__table__.create(engine)
    default = str(tmp_path / "missing.cfg") if use_fallback else str(profile)
    try:
        with sessionmaker(bind=engine)() as session:
            for _ in range(2):
                resource_manager.load_resources_from_file(session, default, str(profile))
                assert resource_manager.get_raw_resources(session, "scan") == [
                    ("Run", "run-scanner"),
                    ("ExtractURLs", "extract-urls"),
                    ("Report", "write-report"),
                ]
                assert session.query(Resource).count() == 3
    finally:
        engine.dispose()


def test_invalid_lines_are_reported_and_other_resources_are_kept(resource_manager, tmp_path, caplog):
    profile = tmp_path / "invalid.cfg"
    profile.write_text("scan_____Run_____run-scanner\ninvalid-line\nscan_____Report_____write-report\n")
    with caplog.at_level("INFO"):
        resources = resource_manager.get_resources_from_file(profile)
    assert list(resources) == [("scan", "Run", "run-scanner"), ("scan", "Report", "write-report")]
    assert "delimiter is incorrect" in caplog.text
