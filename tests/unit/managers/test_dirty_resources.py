from unittest import mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from owtf.models.resource import Resource


@pytest.mark.parametrize("custom_value", ["default-command", "user-edited-command"])
def test_reload_preserves_dirty_resource_and_updates_clean_defaults(tmp_path, custom_value):
    engine = create_engine("sqlite:///:memory:")
    Resource.__table__.create(engine)
    profile = tmp_path / "resources.cfg"
    profile.write_text(
        "scan_____Run_____default-command\nscan_____Clean_____new-clean\nother_____Run_____other-command\n"
    )
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers.resource import load_resources_from_file
    try:
        with sessionmaker(bind=engine)() as session:
            session.add(Resource(resource_type="scan", resource_name="Run", resource=custom_value, dirty=True))
            session.add(Resource(resource_type="scan", resource_name="Clean", resource="old-clean", dirty=False))
            session.commit()
            for _ in range(2):
                load_resources_from_file(session, str(profile), str(profile))
                rows = session.query(Resource).filter_by(resource_type="scan", resource_name="Run").all()
                expected = [(custom_value, True)]
                if custom_value != "default-command":
                    expected.append(("default-command", False))
                assert [(row.resource, row.dirty) for row in rows] == expected
                assert session.query(Resource).filter_by(resource_name="Clean").one().resource == "new-clean"
                assert session.query(Resource).filter_by(resource_type="other").one().resource == "other-command"
                assert session.query(Resource).count() == (3 if custom_value == "default-command" else 4)
    finally:
        engine.dispose()
