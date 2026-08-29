@echo off
set NAME=social-emperors_0.04a

:main
call :pyInstaller
mkdir .\dist\%NAME%\saves
echo [+] pyInstaller Done.
pause>NUL
exit

:pyInstaller
echo [+] Starting pyInstaller...
pyinstaller ^
 --onedir ^
 --contents-directory "bundle" ^
 --console ^
 --noupx ^
 --noconfirm ^
 --add-data "..\..\assets;assets" ^
 --add-data "..\..\config;config" ^
 --add-data "..\..\stub;stub" ^
 --add-data "..\..\templates;templates" ^
 --add-data "..\..\villages;villages" ^
 --paths ..\. ^
 --workpath .\work ^
 --distpath .\dist ^
 --specpath .\bundle ^
 --icon=..\icon.ico ^
 --name %NAME% ..\server.py
REM --debug bootloader
EXIT /B 0

:clean
echo [+] Cleaning...
rm .\work\*
rm .\work\.*
rmdir .\work
rm .\dist\*
rm .\dist\.*
rmdir .\dist
rm .\bundle\*
rm .\bundle\.*
rmdir .\bundle
echo [+] Cleaning Done.
EXIT /B 0