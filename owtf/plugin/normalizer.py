"""
owtf.plugin.normalizer
~~~~~~~~~~~~~~~~~~~~~~

Output deduplication for consistent reporting.
"""
import hashlib
import logging

logger = logging.getLogger(__name__)


class OutputDeduplicator:
    """Deduplicate plugin outputs based on content fingerprint."""

    @staticmethod
    def compute_fingerprint(plugin_code, target_id, output):
        """Compute SHA256 fingerprint of plugin output.

        :param plugin_code: Plugin code
        :type plugin_code: `str`
        :param target_id: Target ID
        :type target_id: `int`
        :param output: Plugin output (JSON string)
        :type output: `str`
        :return: SHA256 fingerprint
        :rtype: `str`
        """
        content = f"{plugin_code}|{target_id}|{output}"
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def is_duplicate(session, plugin_code, target_id, output):
        """Check if output with same fingerprint already exists in database.

        :param session: Database session
        :param plugin_code: Plugin code
        :param target_id: Target ID
        :param output: Plugin output (JSON string)
        :return: True if duplicate exists
        :rtype: `bool`
        """
        from owtf.models.plugin_output import PluginOutput

        fingerprint = OutputDeduplicator.compute_fingerprint(plugin_code, target_id, output)

        existing = session.query(PluginOutput).filter_by(fingerprint=fingerprint).first()
        if existing:
            logger.debug(
                "Duplicate output: plugin %s on target %d (existing output id %d)",
                plugin_code,
                target_id,
                existing.id,
            )
            return True
        return False
