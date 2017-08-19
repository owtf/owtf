# WAF Bypasser module

It assists the penetration testers to diagnose WAF rules and bypass WAFs.

# Run examples

+ Fuzzing using simple content placeholders. The response will be detected if the responce code is in range 300-599 or 100.

```sh-session
python wafbypasser.py -t 'http://127.0.0.1/xss.php?xss=@@@fuzzhere@@@' --mode fuzz -pl payloadlist.txt -rcd '300-599,100'
```
+ Fuzzing using simple content placeholders by adding cookies and post data

This example is fuzzing url using a payload list loaded from file, some post data, headers and a cookie. The response will be detected if contains the string 'permission'.

```sh-session
python wafbypasser.py -t 'http://127.0.0.1/xss.php?xss=@@@fuzzhere@@@' --mode fuzz -pl payloadlist.txt -X POST --contains' "permission" -H "Host: localhost" "Accept: */*" -d "var=1234" --cookie "name=tester"
```

+ Same example as above but fuzzing headers

```sh-session
python wafbypasser.py -t 'http://127.0.0.1/xss.php?xss=test' --mode fuzz -pl payloadlist.txt -X POST --contains' "permission" -H "Host: @@@fuzzhere@@@" "Accept: */*" -d "var=1234" --cookie "name=tester"
```
+ Same as above but reversing the detection functions (Negative testing).

```sh-session
python wafbypasser.py -t 'http://127.0.0.1/xss.php?xss=test' --mode fuzz -pl payloadlist.txt -X POST --contains' "permission" -H "Host: @@@fuzzhere@@@" "Accept: */*" -d "var=1234" --cookie "name=tester" -r
```

+ Testing usings CoNTains case_senvitice text

```sh-session
python wafbypasser.py -t 'http://127.0.0.1/xss.php?xss=test' --mode fuzz -pl payloadlist.txt -X POST --contains' "permission" cs -H "Host: @@@fuzzhere@@@" "Accept: */*" -d "var=1234" --cookie "name=tester" -r
```

+ Finding the fuzzing placeholder allowed length. The 'A' value is a white-listed character.

```sh-session
python wafbypasser.py -t http://demo.testfire.net?var=@@@length@@@ -cnt "long" --accepted_value A -m length
```

+ HTTP Parameter Pollution

ASP mode:  
This mode is splitting the payload at the comma ',' character and it is sending
it to a different variable

```sh-session
python wafbypasser.py -t http://127.0.0.1/xss.php -pl ./Backups/hpp.txt --contains 'whatever' --param_name xss --param_source URL  -m asp_hpp
```

+ Detecting Allowed sources

```sh-session
python wafbypasser.py -t http://127.0.0.1/xss.php --contains 'whatever' --detect_allowed_sources --accepted_method GET --param_name xss --accepted_param_value test --param_source URL
```

+ Fuzzing using templates and transforming payloads

The transformation functions are defined in the obfuscation_lib.py.

```sh-session
python wafbypasser.py -t 'http://127.0.0.1/xss.php' -pl xss2.txt -rcd '200-599,100' --data "xss=@@@<reverse><payload/></reverse>@@@" -m fuzz
```

```sh-session
python wafbypasser.py -t http://127.0.0.1/xss.php -rcd '200-599,100' --data "xss=@@@<utf8>Hello</utf8>@@@" -m fuzz
```

+ Testing for anomalies and bypasses by changing the Content-Type. 

```sh-session
python wafbypasser.py -t http://127.0.0.1/xss.php?xss=test --mode content_type_tamper
```

+ Overchar testing. Sending the payload after a stream with valid characters.
```
python wafbypasser.py -t 'http://127.0.0.1/xss.php?xss=@@@fuzzhere@@@' -rcd 403 -X GET --headers "Accept: */*" "Host: localhost" -m overchar -pl ./Backups/xss.txt --accepted_value 1 --length 8196
```