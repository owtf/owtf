"""Plugin output rows should record their own creation time."""

import time

from sqlalchemy import create_engine, select

from owtf.models.plugin import Plugin  # noqa: F401 - registers the foreign key table
from owtf.models.plugin_output import PluginOutput
from owtf.models.target import Target  # noqa: F401 - registers the foreign key table


def test_plugin_output_creation_time_is_evaluated_for_each_insert():
    engine = create_engine("sqlite:///:memory:")
    table = PluginOutput.__table__
    table.create(engine)

    with engine.begin() as connection:
        connection.execute(table.insert())
        time.sleep(0.02)
        connection.execute(table.insert())
        dates = connection.execute(select(table.c.date_time).order_by(table.c.id)).scalars().all()

    assert dates[1] > dates[0]
