Manual Installation
^^^^^^^^^^^^^^^^^^^

Manual installation of OWTF is nothing but cloning the repo and running the owtf setup.

.. code-block:: bash

    git clone https://github.com/owtf/owtf.git
    cd owtf/
    make setup
    source /home/{username}/.virtualenvs/owtf/bin/activate
    python -m pip install .

Docker
^^^^^^

Docker automates the task of setting up owtf doing all the bootstraping it needs.
Just make sure that you have ``docker`` and ``docker-compose`` installed and run:

.. code-block:: bash

	make compose

* If you wish to override the environment variables for docker setup, use the file named ``owtf.env``

Requirements files
^^^^^^^^^^^^^^^^^^

The ``requirements`` directory remains the canonical source for pinned dependencies used by builds, documentation, tests, and development environments. The ``pyproject.toml`` file reads these lists dynamically, so the corresponding ``*.txt`` files should stay in the repository even though installation now relies on the PEP 517 workflow (``python -m pip install``).
