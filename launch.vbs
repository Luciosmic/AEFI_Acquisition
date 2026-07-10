' Lance launch.bat sans fenêtre console.
' Limite connue : au tout premier lancement (avant que .venv existe),
' "uv sync" tourne caché sans affichage de progression ni d'erreur.
' Pour la toute première installation, lancer launch.bat directement une fois.
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set shell = CreateObject("WScript.Shell")
shell.Run """" & scriptDir & "\launch.bat""", 0, False
