@echo off
setlocal

REM AutoForge backend - Windows one-click dev run
REM Creates a local venv, installs deps, and runs uvicorn.

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate.bat

python -m pip install --upgrade pip
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
