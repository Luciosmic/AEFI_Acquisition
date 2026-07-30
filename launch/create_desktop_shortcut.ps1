# Script pour créer un raccourci sur le bureau pour AEFI Acquisition

$scriptPath = $PSScriptRoot
$repoRoot = Split-Path $scriptPath -Parent
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "AEFI Acquisition.lnk"
$targetPath = Join-Path $scriptPath "launch.vbs"
$iconPath = Join-Path $repoRoot "src\interface\assets\app_icon.ico"
$workingDirectory = $repoRoot

# Créer le raccourci (lance launch.vbs, qui lance launch.bat sans fenêtre console)
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $workingDirectory
$shortcut.IconLocation = $iconPath
$shortcut.Description = "Lanceur pour AEFI Acquisition Interface"
$shortcut.Save()

Write-Host "Raccourci créé sur le bureau: $shortcutPath" -ForegroundColor Green
Write-Host "Vous pouvez maintenant lancer l'application depuis le bureau!" -ForegroundColor Green
