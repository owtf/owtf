> For people who want to participate in the Google Summer of Code 2016, please see [here](https://github.com/owtf/owtf/wiki/Google-Summer-of-Code-2016:-Getting-started) :=)

[![](https://badges.gitter.im/owtf/owtf.svg)](https://gitter.im/owtf/owtf?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

<img src="https://www.owasp.org/images/7/73/OWTFLogo.png" height="150" width="120" />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;![](https://www.owasp.org/images/5/59/Project_Type_Files_TOOL.jpg)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;![](https://www.owasp.org/images/d/dd/Mature_projects.png)

**OWASP OWTF** is a project focused on penetration testing efficiency and alignment of security tests to security standards like the OWASP Testing Guide (v3 and v4), the OWASP Top 10, PTES and NIST so that pentesters will have more time to

- See the big picture and think out of the box
- More efficiently find, verify and combine vulnerabilities
- Have time to investigate complex vulnerabilities like business logic/architectural flaws or virtual hosting sessions
- Perform more tactical/targeted fuzzing on seemingly risky areas
- Demonstrate true impact despite the short timeframes we are typically given to test.


The tool is highly configurable and anybody can trivially create simple plugins or add new tests in the configuration files without having any development experience.

> **Note**: This tool is however not a **silverbullet** and will only be as good as the   person using it: Understanding and experience will be required to correctly interpret tool output and decide what to investigate further in order to demonstrate impact.


Features
===

##### Resilience

If one tool crashes **OWTF**,  will move on to the next tool/test, saving the partial output of the tool until it crashed. **OWTF** also allow you to monitor worker processes and estimated plugin runtimes.

##### Flexibilty
If your internet connectivity or the target host goes down during an assessment, you can ***pause*** the relevant worker processes and **resume** them later avoiding losing data to little as possible.


##### Tests Separation

**OWTF** separates its traffic to the target into mainly 3 types of plugins:

- **Passive** : No traffic goes to the target

- **Semi Passive** : Normal traffic to target

- **Active**:  Direct vulnerability probing

Some features like the *passive* and *semi_passive* **test separation** may also assist pen testers wishing to go the extra mile to get a head start and maybe even legitimately start report writing or preparing attacks before they are given the green light to test.


##### Easy to use APIs

OWTF uses **PostgreSQL** as the database backend. All core **OWTF** functions and options are exposed through APIs making it easy to add new features with little effort.


##### Follows popular pen-testing standards

- **OWTF** will try to classify the findings as closely as possible to the **OWASP Testing Guide**. It also supports the **NIST** and the **PTES** standards.

- **PlugnHack v2 support** :  **PlugnHack** is a *proposed* standard from the **Mozilla** security team for defining how security tools can interact with browsers in a more useful and usable way.

- **Zest and OWASP-ZAP integration** : **Zest** is an experimental specialized *scripting language* (domain-specific ) developed by the **Mozilla** security team and is intended to be used in web oriented security tools.


##### Responsive web interface

**OWTF** now has a default web interface which integrates all core **OWTF** options and makes it possible to manage large pentests easily.

- The default configuration can be changed easily from the browser.

- Makes it easy to control worker processes and see the estimated run times for each plugin run.

- Manage a large number of target URLs easily

- **Searchable** transactions and URL *logs*.


##### Interactive report updated on the fly:

- **Automated** plugin rankings from the tool output, fully configurable by the user.

-  **Configurable** risk rankings

- **In-line notes  editor** for each plugin.


Requirements
===

Currently, **OWTF** is developed and is supported on **Linux**, with out-of-box support for the **Kali Linux** (1.x and 2.x).

**OWTF** has been developed for Python 2.7, and therefore it **may** not run <u>as intended</u> on older Python versions.

For more information on third-party library requirements, please refer to the [requirements](https://github.com/owtf/owtf/blob/e8270f2b26e6846366dda9b622c694fa9342e1bf/install/owtf.pip).

Installation
===

Recommended:

```bash
wget -N https://raw.githubusercontent.com/owtf/bootstrap-script/master/bootstrap.sh; bash bootstrap.sh
```

or simply `git clone https://github.com/owtf/owtf.git; cd owtf/; python2 install/install.py`

Check out the [wiki](https://github.com/owtf/owtf/wiki/OWASP-OWTF-Installation) for more information.

License
===

Checkout [LICENSE](LICENSE)

Links
===

- [Project homepage](http://owtf.github.io/)
- [IRC](http://webchat.freenode.net/?randomnick=1&channels=%23owtf&prompt=1&uio=MTE9MjM20f)
- [Wiki](https://www.owasp.org/index.php/OWASP_OWTF)
- [User Documentation](http://docs.owtf.org/en/latest/)
- [Youtube channel](https://www.youtube.com/user/owtfproject)
- [Slideshare](http://www.slideshare.net/abrahamaranguren/presentations)
- [Blog](http://blog.7-a.org/search/label/OWTF)
