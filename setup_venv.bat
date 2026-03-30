@echo off
REM -------------------------------------------------
REM Setup virtual environment for BMAI FastAPI project
REM -------------------------------------------------

REM Create virtual environment in .venv folder
python -m venv .venv

REM Activate the virtual environment
call .venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install required packages
pip install -r requirements.txt

echo Virtual environment setup complete. To activate later, run:
echo   call .venv\Scripts\activate