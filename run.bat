@echo off
echo Select what do you want to run:
echo 1. Dailies
echo 2. Teamup

set /p choice=Enter your choice: 

if "%choice%"=="1" (
    py -3.9 AutoAFK2.py --dailies
) else if "%choice%"=="2" (
    py -3.9 AutoAFK2.py --teamup
) else (
    echo Invalid choice. Please select a valid option.
)

pause