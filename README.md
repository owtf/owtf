Offensive Web Testing Framework
===

[![Requirements Status](https://requires.io/github/owtf/owtf/requirements.svg?branch=develop)](https://requires.io/github/owtf/owtf/requirements/?branch=develop)
[![Build Status](https://travis-ci.org/owtf/owtf.svg?branch=develop)](https://travis-ci.org/owtf/owtf)
[![License (3-Clause BSD)](https://img.shields.io/badge/license-BSD%203--Clause-blue.svg?style=flat-square)](http://opensource.org/licenses/BSD-3-Clause)
[![python](https://img.shields.io/badge/python-2.7-blue.svg)](https://www.python.org/downloads/)
[![python](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/)

<img src="https://www.owasp.org/images/7/73/OWTFLogo.png" height="150" width="120" />

**OWASP OWTF** is a project focused on penetration testing efficiency and alignment of security tests to security standards like the OWASP Testing Guide (v3 and v4), the OWASP Top 10, PTES and NIST so that pentesters will have more time to

- See the big picture and think out of the box
- More efficiently find, verify and combine vulnerabilities
- Have time to investigate complex vulnerabilities like business logic/architectural flaws or virtual hosting sessions
- Perform more tactical/targeted fuzzing on seemingly risky areas
- Demonstrate true impact despite the short timeframes we are typically given to test.

The tool is highly configurable and anybody can trivially create simple plugins or add new tests in the configuration files without having any development experience.

> **Note**: This tool is however not a **silverbullet** and will only be as good as the person using it: Understanding and experience will be required to correctly interpret tool output and decide what to investigate further in order to demonstrate impact.


Requirements
===

OWTF is developed on KaliLinux and macOS but it is made for Kali Linux (or other Debian derivatives)

OWTF supports both Python2 and Python3.

Installation
===

Recommended:

> Using a virtualenv is highly recommended!

`pip install owtf` or `pip install git+https://github.com/owtf/owtf#egg=owtf`

To install OWTF for development purposes, use
`OWTF_DEV=1 python setup.py install`

To run OWTF on Windows or MacOS, use the Dockerfile (requires **Docker** installed) provided to try OWTF:

 - `make docker-build`
 - `make docker-run`
 - Open `~/.owtf/conf` and change `SERVER_ADDR: 127.0.0.1` to `SERVER_ADDR: 0.0.0.0`.
 - Create a virtualenv, `virtualenv env` and activate it `source env/bin/activate`.
 - Install and run OWTF.
 
  ```bash
   $ cd owtf/
   # Install the develop version, so that any change made is instantly reflected.
   $ python setup.py develop
   # Run OWTF!
   $ python -m owtf
  ```
 - Open `localhost:8009` for OWTF web interface.

## Install on OSX

Dependencies: Install homebrew (https://brew.sh/) and follow the steps given below:

 
```bash
 $ virtualenv <venv name>
 $ source <venv name>/bin/activate
 $ brew install coreutils gnu-sed openssl
 # We need to install 'cryptography' first to avoid issues
 $ pip install cryptography --global-option=build_ext --global-option="-L/usr/local/opt/openssl/lib" --global-option="-I/usr/local/opt/openssl/include"
 $ git clone <this repo>
 $ cd owtf
 $ python setup.py install
 # Run OWTF!
 $ python -m owtf
```

In order to run the tools, install them and point the OWTF config `~/.owtf/conf/general.cfg` to the correct locations.


Features
===

- **Resilience**: If one tool crashes **OWTF**,  will move on to the next tool/test, saving the partial output of the tool until it crashed.

- **Flexibile**: Pause and resume your work.

- **Tests Separation**: **OWTF** separates its traffic to the target into mainly 3 types of plugins:

  - **Passive** : No traffic goes to the target
  - **Semi Passive** : Normal traffic to target
  - **Active**:  Direct vulnerability probing

- Extensive REST API.

- Has almost complete OWASP Testing Guide(v3, v4), Top 10, NIST, CWE coverage.

- **Web interface**: Easily manage large penetration engagements easily.

- **Interactive report**:
  - **Automated** plugin rankings from the tool output, fully configurable by the user.
  - **Configurable** risk rankings
  - **In-line notes editor** for each plugin.


License
===

Checkout [LICENSE](LICENSE.md)

Links
===

- [Project homepage](http://owtf.github.io/)
- [IRC](http://webchat.freenode.net/?randomnick=1&channels=%23owtf&prompt=1&uio=MTE9MjM20f)
- [Wiki](https://www.owasp.org/index.php/OWASP_OWTF)
- [Slack](https://owasp.herokuapp.com) and join channel `#project-owtf`
- [User Documentation](http://docs.owtf.org/en/latest/)
- [Youtube channel](https://www.youtube.com/user/owtfproject)
- [Slideshare](http://www.slideshare.net/abrahamaranguren/presentations)
- [Blog](http://blog.7-a.org/search/label/OWTF)
