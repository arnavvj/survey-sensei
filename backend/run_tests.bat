@echo off
REM Survey Sensei Backend - Test Runner Script (Windows)

setlocal EnableDelayedExpansion

echo Survey Sensei Backend Test Suite
echo ====================================
echo.

REM Activate virtual environment if it exists
if exist venv (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
pip install -q pytest pytest-asyncio pytest-cov pytest-mock faker

REM Parse command line arguments
set RUN_INTEGRATION=0
set COVERAGE=1
set VERBOSE=0

:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--integration" set RUN_INTEGRATION=1
if "%~1"=="--no-coverage" set COVERAGE=0
if "%~1"=="--verbose" set VERBOSE=1
shift
goto parse_args
:end_parse

REM Build pytest command
set PYTEST_CMD=pytest

if !VERBOSE!==1 (
    set PYTEST_CMD=!PYTEST_CMD! -vv
)

if !RUN_INTEGRATION!==1 (
    echo WARNING: Running integration tests requires OpenAI API key
    set PYTEST_CMD=!PYTEST_CMD! --run-integration
) else (
    echo INFO: Skipping integration tests use --integration to enable
)

if !COVERAGE!==0 (
    set PYTEST_CMD=!PYTEST_CMD! --no-cov
)

REM Run tests
echo.
echo Running tests...
echo.

!PYTEST_CMD!

REM Check exit code
if !ERRORLEVEL! EQU 0 (
    echo.
    echo All tests passed!
    echo.

    if !COVERAGE!==1 (
        echo Coverage report generated: htmlcov\index.html
        echo Open in browser: file://%CD%\htmlcov\index.html
    )
) else (
    echo.
    echo Some tests failed
    exit /b 1
)

endlocal
