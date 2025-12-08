@echo off
echo Creation du raccourci sur le bureau...

:: Chemin du script batch principal
set "batchPath=%~dp0start_EFImagingBench.bat"

:: Chemin du bureau
set "desktopPath=%USERPROFILE%\Desktop"

:: Nom du raccourci
set "shortcutName=EFImagingBench.lnk"

:: Création du raccourci VBScript
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%temp%\CreateShortcut.vbs"
echo sLinkFile = "%desktopPath%\%shortcutName%" >> "%temp%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%temp%\CreateShortcut.vbs"
echo oLink.TargetPath = "%batchPath%" >> "%temp%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%~dp0" >> "%temp%\CreateShortcut.vbs"
echo oLink.Description = "Interface de controle du banc d'acquisition EFImagingBench" >> "%temp%\CreateShortcut.vbs"
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll,21" >> "%temp%\CreateShortcut.vbs"
echo oLink.Save >> "%temp%\CreateShortcut.vbs"

:: Exécution du script VBS
cscript //nologo "%temp%\CreateShortcut.vbs"
del "%temp%\CreateShortcut.vbs"

echo Raccourci cree avec succes sur le bureau!
echo Nom: %shortcutName%
echo.
echo Vous pouvez maintenant lancer l'application en double-cliquant sur ce raccourci.
pause
