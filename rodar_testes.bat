@echo off
echo =======================================================================
echo           GABARITEI QUESTOES - SUITE DE TESTES UNITARIOS
echo =======================================================================
echo.
echo [INFO] Inicializando a execucao dos testes...
echo.

rem Executa os testes usando o Python do ambiente virtual
.\venv\Scripts\python.exe -m unittest discover -s tests

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================================
    echo           SUCESSO! Todos os testes unitarios passaram!
    echo =======================================================================
) else (
    echo.
    echo =======================================================================
    echo           ERRO! Alguns testes unitarios falharam.
    echo =======================================================================
)
echo.
pause
