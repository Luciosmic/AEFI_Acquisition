@echo off
echo Initialisation de l'environnement MSVC...

:: Chercher vcvarsall.bat dans les emplacements courants
set "VCVARSALL="
for %%i in (
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
    "C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat"
    "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
    "C:\Program Files\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvarsall.bat"
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat"
) do (
    if exist %%i (
        set "VCVARSALL=%%i"
        goto :found
    )
)

:found
if "%VCVARSALL%"=="" (
    echo Erreur: vcvarsall.bat non trouvé!
    echo Vérifiez que Visual Studio Build Tools est installé
    pause
    exit /b 1
)

echo Environnement trouvé: %VCVARSALL%
echo Initialisation...

:: Initialiser l'environnement MSVC (x64)
call "%VCVARSALL%" x64

echo.
echo Compilation du programme C++...
cl /EHsc /O2 /std:c++17 ultra_serial_cpp.cpp /Fe:ultra_serial_cpp.exe

if %ERRORLEVEL% == 0 (
    echo.
    echo Compilation réussie!
    echo Exécution du test...
    echo.
    ultra_serial_cpp.exe
) else (
    echo Erreur de compilation!
)

pause 