@echo off

set cs_dir=%~dp0

powershell -NoProfile -Command "$s = New-Object -ComObject WScript.Shell; $sc = $s.CreateShortcut('%USERPROFILE%\\Desktop\\Craterstats-III.lnk'); $sc.TargetPath = 'cmd.exe'; $sc.Arguments = '/K %cs_dir%_internal/add_cs_path.bat && craterstats -v'; $sc.WorkingDirectory = '%USERPROFILE%'; $sc.Save()"

echo.
echo Craterstats-III command line shortcut created on desktop
echo (...to %cs_dir%craterstats.exe)
echo.
echo Default start-up directory will be: %USERPROFILE%
echo To modify: right-click shortcut, select Properties - Start in
echo.
echo Press any key to close...
pause >nul
