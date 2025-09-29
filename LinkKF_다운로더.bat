@echo off
chcp 65001 >nul 2>&1
title LinkKF 다운로더 자동 실행

:: 조용히 백그라운드에서 모든 것을 체크하고 GUI 실행
echo 🎬 LinkKF 다운로더 시작 중...

:: Python 설치 확인 (조용히)
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python이 필요합니다. Microsoft Store에서 설치 중...
    start ms-windows-store://pdp/?ProductId=9NRWMJP3717K
    echo Microsoft Store에서 Python 설치 완료 후 다시 실행해주세요.
    pause
    exit /b 1
)

:: 필요한 라이브러리 자동 설치 (조용히)
python -c "import requests, bs4, lxml" >nul 2>&1
if %errorLevel% neq 0 (
    echo 필요한 라이브러리 설치 중...
    python -m pip install requests beautifulsoup4 lxml --quiet --disable-pip-version-check >nul 2>&1
)

:: FFmpeg 확인 (없어도 진행)
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo FFmpeg가 없습니다. 수동 설치가 필요할 수 있습니다.
)

:: downloads 폴더 생성
if not exist "downloads" mkdir downloads >nul 2>&1

:: GUI 파일 확인
if not exist "linkkf_gui.py" (
    echo linkkf_gui.py 파일이 없습니다!
    pause
    exit /b 1
)

:: 1초 후 GUI 실행 (CMD 창 숨김)
timeout /t 1 >nul
start /b pythonw linkkf_gui.py

:: CMD 창 자동 종료
exit 