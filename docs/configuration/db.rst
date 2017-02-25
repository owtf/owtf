Database Configuration
======================

Basic Setup
^^^^^^^^^^^

The connection settings for postgres database are present in ``~/.owtf/db.cfg``.

.. code-block:: ini

    DATABASE_IP: 127.0.0.1
    DATABASE_PORT: 5432
    DATABASE_NAME: owtfdb
    DATABASE_USER: owtf_db_user
    DATABASE_PASS: random_password

.. note::
    Before starting OWTF, make sure you have the postgres database server running.
    This can be easily ensured by using scripts/db_run.sh

Database & User Creation
^^^^^^^^^^^^^^^^^^^^^^^^

Make use of ``scripts/db_setup.sh`` to create the postgres db and user if needed.

.. code-block:: bash

    sh scripts/db_setup.sh init

Database & User Deletion
^^^^^^^^^^^^^^^^^^^^^^^^

Make use of ``scripts/db_setup.sh`` to delete the postgres db and user when needed.

.. code-block:: bash

    sh scripts/db_setup.sh clean
