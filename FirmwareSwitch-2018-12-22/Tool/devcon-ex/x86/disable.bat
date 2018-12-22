@echo off

setlocal ENABLEDELAYEDEXPANSION

set HARDWARE_ID="USB\fibo&02_0E_00"


devcon.exe disable %HARDWARE_ID%

