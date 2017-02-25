Installation
============

Prerequisites
-------------

There are few packages which are mandatory before you proceed

    * Git client: ``sudo apt-get install git``
    * Python 2.7, installed by default in most systems
    * Wget: ``sudo apt-get install wget``

Installation
------------

There are two ways in which you can proceed. Both the methods execute the install script:

    .. toctree::
       :maxdepth: 2

       installation/methods.rst

Install Script
^^^^^^^^^^^^^^

The install script :

    * Prompts you to select a distro from the list that are supported

    .. note::
        If your distro is not listed, please go through Advanced Installation as well.

    * Installs some tools, dictionaries and configration files
    * Installs python libraries using ``pip``

.. include:: installation/advanced.rst
