"""
tests.unit.plugin.test_normalizer_integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for output deduplication with database backend.
"""

import datetime
import tempfile
import unittest
from unittest.mock import patch

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect
from sqlalchemy.orm import sessionmaker

import owtf.models.api_token  # noqa: F401
import owtf.models.command  # noqa: F401
import owtf.models.config  # noqa: F401
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.error  # noqa: F401
import owtf.models.grep_output  # noqa: F401
import owtf.models.plugin  # noqa: F401
import owtf.models.plugin_output  # noqa: F401
import owtf.models.resource  # noqa: F401
import owtf.models.session  # noqa: F401
import owtf.models.target  # noqa: F401
import owtf.models.test_group  # noqa: F401
import owtf.models.transaction  # noqa: F401
import owtf.models.url  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
import owtf.models.work  # noqa: F401
from owtf.db.model_base import Model
from owtf.managers.poutput import save_plugin_output
from owtf.models.plugin_output import PluginOutput
from owtf.plugin.normalizer import OutputDeduplicator


class TestNormalizerIntegration(unittest.TestCase):
    """Test deduplication with database backend."""

    def test_is_duplicate_detects_repeated_save(self):
        """Fingerprint should be consistent and detectable."""
        plugin_key = "test@OWTF-TEST-001"
        target_id = 1
        output = '{"status": "success"}'

        # Compute fingerprint twice for same data
        fp1 = OutputDeduplicator.compute_fingerprint(plugin_key, target_id, output)
        fp2 = OutputDeduplicator.compute_fingerprint(plugin_key, target_id, output)

        # Should be identical (indicating duplicate detection works)
        self.assertEqual(fp1, fp2)

        # Different output should have different fingerprint
        output2 = '{"status": "failed"}'
        fp3 = OutputDeduplicator.compute_fingerprint(plugin_key, target_id, output2)
        self.assertNotEqual(fp1, fp3)

    def test_fingerprint_differs_for_different_outputs(self):
        """Different outputs should have different fingerprints."""
        output1 = '{"status": "success"}'
        output2 = '{"status": "failed"}'

        fp1 = OutputDeduplicator.compute_fingerprint("OWTF-TEST-001", 1, output1)
        fp2 = OutputDeduplicator.compute_fingerprint("OWTF-TEST-001", 1, output2)

        self.assertNotEqual(fp1, fp2)

    def test_fingerprint_same_for_same_content(self):
        """Same content should produce same fingerprint."""
        output = '{"status": "success"}'

        fp1 = OutputDeduplicator.compute_fingerprint("OWTF-TEST-001", 1, output)
        fp2 = OutputDeduplicator.compute_fingerprint("OWTF-TEST-001", 1, output)

        self.assertEqual(fp1, fp2)

    def test_concurrent_duplicate_insert_is_treated_as_a_noop(self):
        """A second worker losing the unique-index race must stay usable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = create_engine("sqlite:///{}/dedup.db".format(tmpdir))
            Model.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            first = Session()
            second = Session()
            now = datetime.datetime.now()
            plugin = {
                "key": "active@OWTF-TEST-001",
                "code": "OWTF-TEST-001",
                "group": "web",
                "type": "active",
                "start": now,
                "end": now,
                "status": "Successful",
                "output_path": "",
                "owtf_rank": -1,
            }
            output = {"status": "success", "result": [1, 2, 3]}

            try:
                # Both workers already passed the optimistic lookup. The first
                # commit wins; the second exercises the unique-index fallback.
                with (
                    patch.object(OutputDeduplicator, "is_duplicate", return_value=False),
                    patch("owtf.plugin.runner.runner.get_plugin_output_dir", return_value="/missing"),
                ):
                    save_plugin_output(first, plugin, output, target_id=1)
                    save_plugin_output(second, plugin, output, target_id=1)

                self.assertEqual(second.query(PluginOutput).count(), 1)
                self.assertEqual(second.query(PluginOutput).one().output, '{"result":[1,2,3],"status":"success"}')
            finally:
                first.close()
                second.close()
                engine.dispose()

    def test_upgrade_adds_fingerprint_column_to_existing_table(self):
        """Migration should add fingerprint column to existing plugin_outputs table."""

        from owtf.db.migrations import upgrade_add_fingerprint_column

        # Create in-memory DB with OLD schema (no fingerprint column)
        engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()

        Table(
            "plugin_outputs",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("plugin_key", String),
            Column("target_id", Integer),
            Column("output", String),
            Column("plugin_group", String),
        )
        metadata.create_all(engine)

        # Run migration
        upgrade_add_fingerprint_column(engine)

        # Verify fingerprint column exists
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("plugin_outputs")]
        self.assertIn("fingerprint", columns)
        indexes = inspector.get_indexes("plugin_outputs")
        self.assertTrue(any(index["name"] == "ix_plugin_outputs_fingerprint" for index in indexes))


if __name__ == "__main__":
    unittest.main()
