@echo off
setlocal

set "ROOT=%~dp0"
set "PY_ENV_NAME=nanobot_env"
set "CONDA_BAT="

echo Starting Intelligent Environment Governance Hub...
echo.
echo Java backend: http://localhost:8080
echo Python API:   http://localhost:5001
echo Frontend:     http://localhost:3000
echo.

if not exist "%ROOT%back-end\pom.xml" (
    echo [ERROR] Cannot find back-end\pom.xml.
    pause
    exit /b 1
)

if not exist "%ROOT%back-end-python\app.py" (
    echo [ERROR] Cannot find back-end-python\app.py.
    pause
    exit /b 1
)

if not exist "%ROOT%front-end\package.json" (
    echo [ERROR] Cannot find front-end\package.json.
    pause
    exit /b 1
)

for %%P in (
    "%USERPROFILE%\anaconda3\condabin\conda.bat"
    "%USERPROFILE%\miniconda3\condabin\conda.bat"
    "%LOCALAPPDATA%\anaconda3\condabin\conda.bat"
    "%LOCALAPPDATA%\miniconda3\condabin\conda.bat"
    "%ProgramData%\anaconda3\condabin\conda.bat"
    "%ProgramData%\miniconda3\condabin\conda.bat"
    "D:\My\conda\condabin\conda.bat"
) do (
    if not defined CONDA_BAT if exist "%%~P" set "CONDA_BAT=%%~P"
)

where mvn >nul 2>nul
if not errorlevel 1 (
    set "MAVEN_CMD=mvn spring-boot:run"
) else if defined MAVEN_HOME if exist "%MAVEN_HOME%\bin\mvn.cmd" (
    set "MAVEN_CMD=""%MAVEN_HOME%\bin\mvn.cmd"" spring-boot:run"
) else if exist "D:\My\Java\apache-maven-3.9.10\bin\mvn.cmd" (
    set "MAVEN_CMD=""D:\My\Java\apache-maven-3.9.10\bin\mvn.cmd"" spring-boot:run"
) else (
    echo [WARN] Cannot find Maven command in this shell.
    echo        Java backend window will try: mvn spring-boot:run
    set "MAVEN_CMD=mvn spring-boot:run"
)

start "Java Backend - 8080" /D "%ROOT%back-end" cmd /k "%MAVEN_CMD%"
if defined CONDA_BAT (
    start "Python API - 5001" /D "%ROOT%back-end-python" cmd /k call "%CONDA_BAT%" activate %PY_ENV_NAME% ^&^& set TF_ENABLE_ONEDNN_OPTS=0 ^&^& python check_python_deps.py ^&^& python app.py
) else (
    start "Python API - 5001" /D "%ROOT%back-end-python" cmd /k conda activate %PY_ENV_NAME% ^&^& set TF_ENABLE_ONEDNN_OPTS=0 ^&^& python check_python_deps.py ^&^& python app.py
)
start "Frontend - 3000" /D "%ROOT%front-end" cmd /k "npm run dev"

echo Started three terminal windows.
echo Keep those windows open while using the project.
echo.
pause
