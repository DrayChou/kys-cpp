@echo off
chcp 936 >nul
cd /d "%~dp0"

if not exist "game\" (
  echo 找不到 game 目录，请把资源放到 %~dp0game
  pause
  exit /b 1
)

if exist "dist\kys.exe" (
  start "" "%~dp0dist\kys.exe" "%~dp0game"
) else (
  start "" "%~dp0src\build\kys.exe" "%~dp0game"
)