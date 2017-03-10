Troubleshooting
===============

* Unable to install **pycurl** library, getting **main.ConfigurationError: Could not run curl-config**?

    Luckily, we have faced this issue. If you ran the install script and still got this error, you can let us know. If not,
    check `this issue <https://github.com/owtf/owtf/issues/330>`_ on how to fix it.

* Unable to run OWTF because of **ImportError: No module named cryptography.hazmat.bindings.openssl.binding**?

    This actually means you do not have cryptography python module installed. It is recommended to rerun the install script (or)
    to just install the missing python libraries using the following command.

    .. code-block:: bash

        pip2 install --upgrade -r install/owtf.pip

* Unable to run OWTF because of **TypeError: parse_requirements() missing 1 required keyword argument: 'session'**

    This is because of an older version of pip installed in your System. To resolve this run the following commands

    .. code-block:: bash

        pip install --upgrade pip (run as root if required)
        python install/install.py

