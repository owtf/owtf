Framework Configuration (Optional)
==================================

Some basic settings like, where should the interface server listen etc.. can be controlled from a
config file present at ``framework/config/framework_config.cfg``. All the default values are ready
by default.

* The address on which the interface server listens can be changed which will allow you to access
  the interface over any network.

    .. code-block:: ini

        # ------------------------- Interface Server ------------------------- #
        SERVER_ADDR: 0.0.0.0
        UI_SERVER_PORT: 8009
        FILE_SERVER_PORT: 8010
