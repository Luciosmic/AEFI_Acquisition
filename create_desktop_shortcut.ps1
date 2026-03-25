# Script pour créer un raccourci sur le bureau pour AEFI Acquisition

$scriptPath = $PSScriptRoot
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "AEFI Acquisition.lnk"
$targetPath = Join-Path $scriptPath "launch.bat"
$workingDirectory = $scriptPath

# Créer le raccourci
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $workingDirectory
$shortcut.Description = "Lanceur pour AEFI Acquisition Interface"
$shortcut.Save()

Write-Host "Raccourci créé sur le bureau: $shortcutPath" -ForegroundColor Green
Write-Host "Vous pouvez maintenant lancer l'application depuis le bureau!" -ForegroundColor Green
