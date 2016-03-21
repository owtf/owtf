#!/usr/bin/env python

import json
import sys
import traceback


with open(str(sys.argv[1]), 'r') as data_file:
    data = json.load(data_file)
orgName = str(sys.argv[1]).split('.json', 1)[0]
if data[0]['status'] == 'ERROR':
    print "sslscan finished with errors"
    sys.exit(0)
print "RESULT IN SSL_TLS_TESTING_FUNCTIONALITY_FROM_SSLLABS_REPORT.html"

try:

    f = open(orgName+'_report.html', 'w')
    f.write('<html>')
    f.write('<body>')
    f.write('<div style="background-color: lightgrey;border:1px solid;border-radius:10px;width:300px;"')
    f.write('<h1>SSL SCAN REPORT</h1>')
    f.write('</div>')
    f.write('<h2> Input Url : </h2>'+data[0]['host'])
    f.write('<h2> Domain : </h2>'+data[0]['host'])
    f.write('<h2> HTTP status code :</h2>' + str(data[0]['endpoints'][0]['details']['httpStatusCode']))
    f.write('<h2> IP : </h2>'+data[0]['endpoints'][0]['ipAddress'])
    f.write('<h2> Grade : </h2>'+data[0]['endpoints'][0]['grade'])
    f.write('<h2> Secondary Grade : </h2>'+data[0]['endpoints'][0]['gradeTrustIgnored'])
    f.write('<h2> Freak : </h2>'+str(data[0]['endpoints'][0]['details']['freak']))
    f.write('<h2> Poodle TLS :  </h2>'+str(data[0]['endpoints'][0]['details']['poodleTls'])+' (-3:timeout,-2:TLS not supported,-1:test failed,0:unknown,1:not vulnerable,3:vulnerable)')
    insecureRenegotiationSuported = 'true' if data[0]['endpoints'][0]['details']['renegSupport'] == 1 else 'false'
    f.write('<h2> Insecure renegotiation support : </h2>'+insecureRenegotiationSuported)
    f.write('<h2> openSslCcs test : </h2>'+str(data[0]['endpoints'][0]['details']['openSslCcs'])+'(-1:test failed,0: unknown,1: not vulnerable,2:possibly vulnerbale,3:vulnerable and exploitable)')
    if 'dhUsesKnownPrimes' in data[0]['endpoints'][0]['details']:
        insecureDH = 'true' if data[0]['endpoints'][0]['details']['dhUsesKnownPrimes'] == 2 else 'false'
        f.write('<h2> Insecure DH : </h2>'+insecureDH )
    for protocol in data[0]['endpoints'][0]['details']['protocols']:
        f.write('<h2> Protocol SSL/TLS version supported : </h2>'+protocol['name']+'  '+protocol['version'])
    certificateExpired = 'true' if data[0]['endpoints'][0]['details']['chain']['issues'] == 2 else 'false'
    f.write('<h2> Certificate Expired  : </h2>'+certificateExpired)
    selfSigned = 'true' if data[0]['endpoints'][0]['details']['cert']['issues'] == 64 else 'false'
    f.write('<h2> Self-signed cert: </h2>' +selfSigned)
    f.write('<h2> Supports RC4: </h2>'+str(data[0]['endpoints'][0]['details']['supportsRc4']))
    for chainCert in data[0]['endpoints'][0]['details']['chain']['certs']:
        f.write('<h2> Chain Cert issue: </h2>'+str(chainCert['issues'])+'(1:certificate not yet valid,2:certificate expired,4:weak key,8:weak signature,16:blacklisted) ')
        weakKey = 'true' if chainCert['issues'] == 4 else 'false'
        weakSignature = 'true' if chainCert['issues'] == 8 else 'false'
        f.write('<h2> Weak private key: </h2>' + weakKey )
        f.write('<h2> Weak certificate: </h2>' + weakSignature )
    f.write('<h2> Forward secrecy support: </h2>'+str(data[0]['endpoints'][0]['details']['forwardSecrecy'])+'(1:et if at least one browser from our simulations negotiated a Forward Secrecy suite,2:et based on Simulator results if FS is achieved with modern clients. For example, the server supports ECDHE suites, but not DHE,4:set if all simulated clients achieve FS. In other words, this requires an ECDHE + DHE combination to be supported.')
    secureRenegotiationSuported = 'true' if data[0]['endpoints'][0]['details']['renegSupport'] == 2 else 'false'
    f.write('<h2> Secure renegotiation support: </h2>' + secureRenegotiationSuported )
    f.write('</body>')
    f.write('</html>')
    f.close()
except:
    print('Something went wrong when parsing result')
    print traceback.format_exc()
    sys.exit(0)
sys.exit(0)
