#**Intro**
-----
The purpose of this tool is to automate the manual, uncreative part of pen testing: For example, spending time trying to remember how to call "tool X", parsing results of "tool X" manually to feed "tool Y", etc.

By reducing this burden I hope pen testers will have more time to:
- See the big picture and think out of the box
- More efficiently find, verify and combine vulnerabilities 
- Have time to investigate complex vulnerabilities like business logic/architectural flaws or virtual hosting sessions
- Perform more tactical/targeted fuzzing on seemingly risky areas
- Demonstrate true impact despite the short timeframes we are typically given to test.

Some features like the passive and semi_passive test separation may also assist pen testers wishing to go the extra mile to get a head start and maybe even legitimately start report writing or preparing attacks before they are given the green light to test.

The tool is highly configurable and anybody can trivially create simple plugins or add new tests in the configuration files without having any development experience. Please share your tests with the community! :)

This tool is however not a silverbullet and will only be as good as the person using it: Understanding and experience will be required to correctly interpret tool output and decide what to investigate further in order to demonstrate impact.

#**Features**
--------
- OWASP Testing Guide-oriented: owtf will try to classify the findings as closely as possible to the OWASP Testing Guide
- Report updated on the fly: As soon as each plugin finishes or sometimes before (i.e. after each vulnerability scanner finishes)
- "Scumbag spidering": Instead of implementing yet another spider (a hard job), owtf will scrub the output of all tools/plugins run to gather as many URLs as possible. This is somewhat "cheating" but tremendously effective since it combines the results of different tools, including several tools that perform brute forcing of files and directories.
- Resilience: If one tool crashes owtf will move on to the next tool/test, saving the partial output of the tool until it crashed
- Web UI: controlled and used from a web interface.
  - Managing Targets
  - Plugins: Launch plugins from the targets table or from individual target report.
    * WEB group
    * NET group
    * AUX group
  - Analyzing Results: Navigate to the individual target report to go through the results of the plugins executed for a specific target.
  - Managing Workers: Control over processes that run the plugins.
  - Controlling Worklist
- Zest and ZAP integration: Zest is an experimental specialized scripting language developed by the Mozilla security team. ZAP is an easy to use integrated penetration-testing tool for finding vulnerabilities in web applications.
- HTTP Sessions: Rendering according to the RFC 6265, URL-enconding to represent non-ASCII by default.
- PostgreSQL DB for transactions and APIs (Zest and ZAP API, Sessions API)
- Server address flexibility, proxy logs.
- PlugnHack: A proposed standard from the Mozilla security team for defining how security tools can interact with browsers in a more useful and usable way.

#**Requirements**
------------
- Linux (any Ubuntu derivative should work just fine) and python 2.6.5 or greater
- Latest Kali version not required but helpful (almost 0 setup time)
- Git client: 
  `sudo apt-get install git` 
- Python 2.7
- Wget: 
  `sudo apt-get install wget`

#**Installation**
------------
- **Installation by script:**
  ```
  wget https://raw.githubusercontent.com/owtf/owtf/lions_2014/contrib/bootstrap.sh
  chmod +x bootstrap.sh
  ./bootstrap.sh
  ```
  
- **Mandatory:** 
  * Postgresql

- **Optional packages:** 
  * Tor (for Botnet mode)
  * Proxychains (for Botnet mode)

- For a few more ways to install OWTF check out OWTF Documentation page

#**Links**
-----------
- OWASP OWTF project page: [http://owtf.github.io/]
- OWASP OWTF Wiki: [https://www.owasp.org/index.php/OWASP_OWTF]
- OWASP OWTF Documentation: [http://docs.owtf.org/en/latest/]
- OWASP OWTF Youtube channel: [https://www.youtube.com/user/owtfproject]

#**FAQ**
---
Q - What are the OWASP Codes "OWASP-WU-..."
A - Those are just fake OWASP Codes to uniquely identify owtf plugins that do not correspond to any OWASP test. For example:
OWASP-WU-SPID - Only visits gathered links to feed other plugins
OWASP-WU-VULN - This runs all configured vulnerability scanners, the findings will correspond to different OWASP Codes but they must be run from 1 plugin only performing all tests for efficiency and simplicity


