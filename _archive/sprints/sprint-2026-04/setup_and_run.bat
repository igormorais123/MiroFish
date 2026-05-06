@echo off
chcp 65001 >nul
echo ===== Mirofish INTEIA - Setup e Execucao =====
echo.

cd /d "C:\Users\IgorPC\.claude\projects\Mirofish INTEIA\backend"

echo [1/3] Criando ambiente virtual...
uv venv .venv
if errorlevel 1 (
    echo ERRO: Falha ao criar venv. Verifique se uv esta instalado.
    echo Instale com: pip install uv
    pause
    exit /b 1
)

echo [2/3] Instalando dependencias...
uv pip install -e ".[dev]"
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo [3/3] Iniciando backend na porta 5001...
echo Acesse http://localhost:5001/health para verificar
echo.
.venv\Scripts\python.exe run.py
