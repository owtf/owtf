"""
tests.unit.plugin.test_normalizer_integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for output deduplication with database backend.
"""
import unittest

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect

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

    def test_upgrade_adds_fingerprint_column_to_existing_table(self):
        """Migration should add fingerprint column to existing plugin_outputs table."""

        from owtf.db.migrations import upgrade_add_fingerprint_column

        # Create in-memory DB with OLD schema (no fingerprint column)
        engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()

        Table(
            "plugin_outputs",
            metadata,
            Column('id', Integer, primary_key=True),
            Column('plugin_key', String),
            Column('target_id', Integer),
            Column('output', String),
            Column('plugin_group', String),
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
