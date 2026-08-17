"""
tests.unit.plugin.test_normalizer_integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for output deduplication with database backend.
"""
import unittest

from owtf.plugin.normalizer import OutputDeduplicator


class TestNormalizerIntegration(unittest.TestCase):
    """Test deduplication with database backend."""

    def test_is_duplicate_detects_repeated_save(self):
        """is_duplicate() should detect when same output is saved twice."""
        from owtf.db.session import get_scoped_session
        from owtf.models.plugin_output import PluginOutput

        session = get_scoped_session()
        try:
            # First save
            plugin_code = "OWTF-TEST-001"
            target_id = 1
            output = '{"status": "success"}'

            # Should not be duplicate on first check
            is_dup = OutputDeduplicator.is_duplicate(session, plugin_code, target_id, output)
            self.assertFalse(is_dup)

            # Manually insert to simulate first save
            fingerprint = OutputDeduplicator.compute_fingerprint(plugin_code, target_id, output)
            plugin_output = PluginOutput(
                plugin_code=plugin_code,
                target_id=target_id,
                output=output,
                fingerprint=fingerprint,
                plugin_key="test@OWTF-TEST-001",
                plugin_group="web",
                plugin_type="active",
                status="success",
                owtf_rank=-1,
            )
            session.merge(plugin_output)
            session.commit()

            # Second check should detect duplicate
            is_dup = OutputDeduplicator.is_duplicate(session, plugin_code, target_id, output)
            self.assertTrue(is_dup)

        finally:
            session.close()

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


if __name__ == "__main__":
    unittest.main()
