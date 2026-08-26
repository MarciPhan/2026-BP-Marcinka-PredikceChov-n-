@echo off
set /p INPUT_TOKEN="Enter: "
if "%INPUT_TOKEN%"=="" (
    echo empty
    goto skip
)
echo %INPUT_TOKEN%
:skip
echo done
