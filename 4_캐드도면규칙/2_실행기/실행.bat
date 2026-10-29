@echo off
rem 도면 규칙 가르치기 v0.1 · 2026-10-29 · 4_캐드도면규칙\2_실행기
rem 파이썬을 찾고, ezdxf 가 없으면 깔고, 서버를 켜고 브라우저를 연다. 성공하면 창이 남아 서버가 돈다 (닫으면 서버가 꺼짐).
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 goto py
where python >nul 2>nul
if %errorlevel%==0 goto python
echo [!] 파이썬이 없습니다. python.org 에서 3.10 이상을 깔고 (Add to PATH 켬) 다시 여십시오.
pause
exit /b 1
:py
set PYEXE=py
goto run
:python
set PYEXE=python
:run
%PYEXE% -c "import ezdxf" >nul 2>nul
if %errorlevel%==0 goto start
echo ezdxf 를 처음 한 번 깝니다 ...
%PYEXE% -m pip install ezdxf
%PYEXE% -c "import ezdxf" >nul 2>nul
if not %errorlevel%==0 (
  echo [!] ezdxf 를 못 깔았습니다. 인터넷 · 프록시를 확인하고 다시 여십시오.
  pause
  exit /b 1
)
:start
echo 도면 규칙 가르치기 서버를 켭니다. 이 창을 닫으면 서버가 꺼집니다.
%PYEXE% "%~dp0서버.py"
if not %errorlevel%==0 pause
