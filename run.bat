@echo off
echo Select what do you want to run:
echo 1. Dailies
echo 2. Teamup
echo 3. Abyss
echo 4. Towers
echo 5. Test

set /p choice=Enter your choice: 

if "%choice%"=="1" (
    py -3.9 AutoAFK2.py --dailies
) else if "%choice%"=="2" (
    py -3.9 AutoAFK2.py --teamup
) else if "%choice%"=="3" (
    py -3.9 AutoAFK2.py --abyss
) else if "%choice%"=="4" (
    py -3.9 AutoAFK2.py --legend
) else if "%choice%"=="5" (
    py -3.9 AutoAFK2.py --test
) else (
    echo Invalid choice. Please select a valid option.
)

pause