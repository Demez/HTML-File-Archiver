@echo off
setlocal enabledelayedexpansion

if not exist "offline\" mkdir "offline"
if not exist "old\" mkdir "old"

@REM this should be your user folder, it's needed for below
set "user_folder="

@REM python is normally in this folder, so only change if it's not
set "python_folder=C:\Users\!user_folder!\AppData\Local\Programs\Python\Python37-32"

for /F "delims=*" %%A in ('dir /b *.html') do (
	
	set "input_file=%%A"
	
	set "output_file=offline\!input_file!"
	set "output_folder=%%~nA files"
	
	"!python_folder!\python.exe" HTMLOfflineFileReplacer.py --input_file "!input_file!" --output_file "!output_file!" --output_folder "!output_folder!"
	echo.
	
	if exist "offline\%%A" move "%%A" "old\%%A"
	
	@REM move the output folder there since the script would put it in offline/name/filename lmao
	if not exist "offline\!output_folder!\" move "!output_folder!" "offline\!output_folder!"
	
	@REM pause
	echo.
)

pause

