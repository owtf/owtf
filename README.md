[![Code Health](https://landscape.io/github/owtf/owtf/lions_2014/landscape.png)](https://landscape.io/github/owtf/owtf/lions_2014)

Intro
===

**OWTF** aims to make pen testing:

- Aligned with **OWASP Testing Guide** + **PTES** + **NIST**
- More ***efficient***
- More ***comprehensive***
- More *creative and fun* (minimise un-creative work)

so that pentesters will have more time to

- See the big picture and think out of the box
- More efficiently find, verify and combine vulnerabilities
- Have time to investigate complex vulnerabilities like business logic/architectural flaws or virtual hosting sessions
- Perform more tactical/targeted fuzzing on seemingly risky areas
- Demonstrate true impact despite the short timeframes we are typically given to test.


The tool is highly configurable and anybody can trivially create simple plugins or add new tests in the configuration files without having any development experience.

> Please share your plugins/tests with the community! :)

> **Note**: This tool is however not a **silverbullet** and will only be as good as the   person using it: Understanding and experience will be required to correctly interpret tool output and decide what to investigate further in order to demonstrate impact.


Features
===

**OWTF** uses "*Scumbag spidering*", ie. instead of implementing yet another spider ([a hard job](http://w3af.org/dont-write-your-own-web-application-security-scanner)), **OWTF** will scrub the output of all tools/plugins run to gather as many URLs as possible.

> This is somewhat "cheating" but tremendously effective since it combines the results of different tools, including several tools that perform brute forcing of files and directories.

##### Resilience

If one tool crashes **OWTF**,  will move on to the next tool/test, saving the partial output of the tool until it crashed. **OWTF** also allow you to monitor worker processes and estimated plugin runtimes.

##### Flexibilty
If your internet connectivity or the target host goes down during an assessment, you can ***pause*** the relevant worker processes and **resume** them later avoiding losing data to little as possible.

----

### Tests Separation

**OWTF** separates its traffic to the target into mainly 3 types of plugins:

- **Passive** : No traffic goes to the target

- **Semi Passive** : Normal traffic to target

- **Active**:  Direct vulnerability probing

Some features like the *passive* and *semi_passive* **test separation** may also assist pen testers wishing to go the extra mile to get a head start and maybe even legitimately start report writing or preparing attacks before they are given the green light to test.

-----

### Easy to use APIs

OWTF uses **PostgreSQL** as the database backend. All core **OWTF** functions and options are exposed through APIs making it easy to add new features with little overhead.

----

### Follows popular pen-testing standards

**OWTF** will try to classify the findings as closely as possible to the **OWASP Testing Guide**. It also supports the **NIST** and the **PTES** standards.

**PlugnHack v2 support** :  **PlugnHack** is a *proposed* standard from the **Mozilla** security team for defining how security tools can interact with browsers in a more useful and usable way.

**Zest and OWASP-ZAP integration** : **Zest** is an experimental specialized *scripting language* (domain-specific ) developed by the **Mozilla** security team and is intended to be used in web oriented security tools.

----
### Responsive web interface

**OWTF** now has a default web interface which integrates all core **OWTF** options and makes it possible to manage large pentests easily.

- The web interface is built on **Twitter Bootstrap**, making it very easy to use and customize.

- The default configuration can be changed easily from the browser.

- Makes it easy to control worker processes and see the estimated run times for each plugin run.

- Manage a large number of target URLs easily

- **Searchable** transactions and URL *logs*.

----
### Interactive report updated on the fly:

- As soon as each plugin finishes or sometimes before (i.e. after each vulnerability scanner finishes), the report is updated **asynchronously** through the *OWTF APIs*.

- **Automated** plugin rankings from the tool output, fully configurable by the user.

-  **Configurable** risk rankings

- **In-line notes  editor** for each plugin.

Requirements
===

Currently, **OWTF** is developed and is supported on **Linux**, with out-of-box support for the **Kali Linux** and **Samurai-WTF**.

**OWTF** has been developed for *Python 2.7*, and therefore it **may** not run <u>as intended</u> on older *Python* versions.

For more information on third-party library requirements, please refer to the [requirements](https://github.com/owtf/owtf/blob/e8270f2b26e6846366dda9b622c694fa9342e1bf/install/owtf.pip).

Installation
===

Recommended:

```
wget https://raw.githubusercontent.com/owtf/bootstrap-script/master/bootstrap.sh -O bootstrap.sh; chmod +x bootstrap.sh; ./bootstrap.sh
```

or simply clone the latest version of **OWTF**.

Check out the [wiki](https://github.com/owtf/owtf/wiki/OWASP-OWTF-Installation) for more information.

Links
===

- [Project homepage](http://owtf.github.io/)
- [Wiki](https://www.owasp.org/index.php/OWASP_OWTF)
- [User Documentation](http://docs.owtf.org/en/latest/)
- [Youtube channel](https://www.youtube.com/user/owtfproject)
- [Slideshare](http://www.slideshare.net/abrahamaranguren/presentations)
- [Blog](http://blog.7-a.org/search/label/OWTF)
