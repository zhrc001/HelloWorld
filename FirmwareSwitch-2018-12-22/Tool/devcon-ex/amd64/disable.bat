@echo off

setlocal ENABLEDELAYEDEXPANSION

set HARDWARE_ID="PCI\VEN_8086&DEV_7360&CC_0D40"


devcon.exe disable %HARDWARE_ID%

