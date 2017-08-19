httprint v0.301 (beta) - web server fingerprinting tool
(c) 2003-2005 net-square solutions pvt. ltd. - see readme.txt
http://net-square.com/httprint/
httprint@net-square.com

Usage:

httprint {-h <host> | -i <input file> | -x <nmap xml file>} -s <signatures> [... options]

-h <host>            host can be either an IP address, a symbolic name,
                     an IP range or a URL.
-i <input text file> file containing list of hosts as described above
                     in text format.
-x <nmap xml file>   Nmap -oX option generated xml file as input file.
                     Ports which can be considered as http ports are taken
                     from the nmapportlist.txt file.
-s <signatures>      file containing http fingerprint signatures.

Options:

-o <output file>     output in html format.
-oc <output file>    output in csv format.
-ox <output file>    output in xml format.
-noautossl           Disable automatic detection of SSL.
-tp <ping timeout>   Ping timeout in milliseconds.
                     Default is 4000 ms. Maximum 30000 ms.
-ct <1-100>          Default is 75. Do not change.
-ua <User Agent>     Default is Mozilla/4.0 (compatible; MSIE 5.01;
                     Windows NT 5.0.
-t <timeout>         Connection/read timeout in milliseconds.
                     Default is 10000 ms. Maximum 100000 ms.
-r <retry>           Number of retries. Default is 3. Maximum 30.
-P0                  Turn ICMP ping off.
-nr                  No redirection. Do not automatically follow 301,
                     302 responses. Enabled by default.
-th <threads>        Number of threads. Default is 8. Maximum 64.
-?                   Displays this message.

Examples:

httprint -h www1.example.com -s signatures.txt
httprint -h https://www2.example.com/ -s signatures.txt
httprint -h http://www3.example.com:8080/ -s signatures.txt
httprint -h www1.example.com -s signatures.txt -noautossl
httprint -h 10.0.1.1-10.0.1.254 -s signatures.txt -o 10_0_1_x.html
httprint -x nmap.xml -s signatures.txt -oc report.csv
httprint -x nmap.xml -s signatures.txt -ox report.xml
httprint -i input.txt -s signatures.txt -o output.html -th 16

==============================================================

***COPYRIGHT***

Copyright (C) 2003,2004 net-square solutions pvt. ltd.

***Terms of Use***

THIS SOFTWARE IS DISTRIBUTED "AS IS". NET-SQUARE MAKES
NO GUARANTEE ABOUT ITS EFFECTIVENESS, FITNESS OR COMPLETENESS
FOR ANY PARTICULAR USE. IT MAY CONTAIN BUGS, SO USE THIS TOOL 
AT YOUR OWN RISK. 

NET-SQUARE IS NOT TAKING ANY RESPONSILBITY FOR ANY DAMAGE THAT MAY 
UNINTENTIONALLY BE CAUSED THROUGH ITS USE. 

YOU DO NOT HAVE THE RIGHT TO MODIFY, REVERSE ENGINEER OR SELL THIS TOOL
WITHOUT EXPRESS WRITTEN PERMISSION OF NET-SQUARE.

HTTPRINT IS FREE FOR NON-COMMERCIAL, PERSONAL OR EDUCATIONAL USE.
FOR ALL OTHER USES OF HTTPRINT, PLEASE OBTAIN AN APPROPRIATE LICENSE
FROM NET-SQUARE.


Other licenses:

httprint uses expat and openssl. Their licenses are as follows:

expat:
------
Copyright (c) 1998, 1999, 2000 Thai Open Source Software Center Ltd
                               and Clark Cooper
Copyright (c) 2001, 2002 Expat maintainers.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


openssl:
--------

Copyright (c) 1998-2003 The OpenSSL Project.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer. 

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in
   the documentation and/or other materials provided with the
   distribution.

3. All advertising materials mentioning features or use of this
   software must display the following acknowledgment:
   "This product includes software developed by the OpenSSL Project
   for use in the OpenSSL Toolkit. (http://www.openssl.org/)"

4. The names "OpenSSL Toolkit" and "OpenSSL Project" must not be used to
   endorse or promote products derived from this software without
   prior written permission. For written permission, please contact
   openssl-core@openssl.org.

5. Products derived from this software may not be called "OpenSSL"
   nor may "OpenSSL" appear in their names without prior written
   permission of the OpenSSL Project.

6. Redistributions of any form whatsoever must retain the following
   acknowledgment:
   "This product includes software developed by the OpenSSL Project
   for use in the OpenSSL Toolkit (http://www.openssl.org/)"

THIS SOFTWARE IS PROVIDED BY THE OpenSSL PROJECT ``AS IS'' AND ANY
EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE OpenSSL PROJECT OR
ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

==============================================================

Support:

   For any problem or query, you may get in touch with us at
   httprint {at} net {hyphen} square {dot} com.


