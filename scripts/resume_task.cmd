@echo off
REM Reboot-proof batch-collection driver invoked by the AG_BatchResume scheduled tasks.
REM cd into the repo, run resume.py with the system Python, and append all output to the log.
cd /d "C:\Users\USER01\Dropbox\Workplace\D\George\PAPERS\Paroysiaseis\Cyprus 2025\ag-llm-stylometry"
"C:\Users\USER01\AppData\Local\Programs\Python\Python312\python.exe" src\resume.py >> "output\logs\resume.log" 2>&1
