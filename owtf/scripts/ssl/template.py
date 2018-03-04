RESULTS = """
<!DOCTYPE html>
<html lang="en">
  <body>
    <div style="background-color: lightgrey;border:1px solid;border-radius:10px;width:300px;">
      <h1>SSL SCAN REPORT</h1>
    </div>
    <h2> Input url: {{host}}</h2>
    <h2> Domain: {{host}}</h2>
    <h2> HTTP status code: {{status_code}}</h2>
    <h2> IP: {{ip_address}}</h2>
    <h2> Grade : {{grade}}</h2>
    <h2> Secondary Grade: {{secondary_grade}}</h2>
    <h2> Freak : {{freak}}</h2>
    <h2> Poodle TLS : {{poodle}}  (-3:timeout,-2:TLS not supported,-1:test failed,0:unknown,1:not vulnerable,3:vulnerable)</h2>
    <h2> Insecure Renegotiation supported:  {{insecure_reneg}}</h2>
    <h2> openSslCcs test : {{openssl_ccs}} (-1:test failed,0: unknown,1: not vulnerable,2:possibly vulnerbale,3:vulnerable and exploitable)</h2>
    <h2> Insecure DH : {{insecure_dh}} </h2>
    {{protocol}}
    <h2> Certificate Expired  : {{cert_exp}}</h2>
    <h2> Self-signed cert: {{self_signed}}</h2>
    <h2> Supports RC4: {{rc4}}</h2>
    <h2> Forward secrecy support: {{fwd_sec}} (1:et if at least one browser from our simulations negotiated a Forward Secrecy suite,2:et based on Simulator results if FS is achieved with modern clients. For example, the server supports ECDHE suites, but not DHE,4:set if all simulated clients achieve FS. In other words, this requires an ECDHE + DHE combination to be supported.)</h2>
    {{cert_chains}}
    <h2> Secure renegotiation support: {{sec_reneg}}</h2>
  </body>
</html>
"""
