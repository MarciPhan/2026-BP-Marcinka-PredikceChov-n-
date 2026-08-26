import subprocess
with open('test.bat', 'w') as f:
    f.write('''@echo off
set /p INPUT_TOKEN="Enter: "
if "%INPUT_TOKEN%"=="" (
    echo empty
    goto skip
)
echo %INPUT_TOKEN%
:skip
echo done
''')
try:
    p = subprocess.run(['cmd.exe', '/c', 'test.bat'], input=b'\r\n', capture_output=True, timeout=2)
    print(p.stdout.decode())
except Exception as e:
    print(e)
