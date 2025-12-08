@echo off
echo Compilation du programme C++ pour test de performance...

:: Utiliser le compilateur MSVC si disponible
where cl >nul 2>nul
if %ERRORLEVEL% == 0 (
    echo Compilation avec MSVC...
    cl /EHsc /O2 ultra_serial_cpp.cpp /Fe:ultra_serial_cpp.exe
) else (
    :: Sinon essayer g++ (MinGW)
    where g++ >nul 2>nul
    if %ERRORLEVEL% == 0 (
        echo Compilation avec g++...
        g++ -O3 -std=c++17 ultra_serial_cpp.cpp -o ultra_serial_cpp.exe
    ) else (
        echo Erreur: Aucun compilateur C++ trouvé (cl.exe ou g++.exe)
        echo Installez Visual Studio Build Tools ou MinGW
        pause
        exit /b 1
    )
)

if %ERRORLEVEL% == 0 (
    echo Compilation réussie!
    echo Exécution du test...
    echo.
    ultra_serial_cpp.exe
) else (
    echo Erreur de compilation!
)

pause 