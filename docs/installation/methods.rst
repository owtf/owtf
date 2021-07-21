Manual Installation
^^^^^^^^^^^^^^^^^^^

Manual installation of OWTF is nothing but cloning the repo and running the owtf setup.

.. code-block:: bash

    git clone https://github.com/owtf/owtf.git
    cd owtf/
    make setup
    source /home/{username}/.virtualenvs/owtf/bin/activate
    python setup.py install

Docker
^^^^^^

Docker automates the task of setting up owtf doing all the bootstraping it needs.
Just make sure that you have ``docker`` and ``docker-compose`` installed and run:

.. code-block:: bash

	make compose

* If you wish to override the environment variables for docker setup, use the file named ``owtf.env``
