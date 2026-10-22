@echo off
REM Patch, brand and prepare TheCat Desktop for Windows (CI entry point).
REM Expects TDESKTOP_SRC to point at the tdesktop checkout; defaults to ..\tdesktop.
setlocal enabledelayedexpansion

if "%TDESKTOP_SRC%"=="" set "TDESKTOP_SRC=%~dp0..\tdesktop"
pushd "%~dp0.." || exit /b 1
set "REPO_ROOT=%CD%"
popd

echo ==^> 1/4 patch endpoint + RSA keys
python "%REPO_ROOT%\patch_thecat_endpoint.py" "%TDESKTOP_SRC%\Telegram\SourceFiles\mtproto\mtproto_dc_options.cpp"
if errorlevel 1 exit /b 1

echo ==^> 2/4 brand
python "%REPO_ROOT%\brand_thecat.py" --tdesktop "%TDESKTOP_SRC%"
if errorlevel 1 exit /b 1

echo ==^> 3/4 prepare libraries
REM No skip-release: prepare.py's "release:" lines are what produce the Release
REM variants of tg_angle.lib and avif.lib, and the app links those (LNK1181).
pushd "%TDESKTOP_SRC%\Telegram" || exit /b 1
call build\prepare\win.bat silent
if errorlevel 1 (
  popd
  exit /b 1
)

echo ==^> 4/4 configure
REM Test-only Telegram API credentials; theCat's server does not validate api_id.
call configure.bat -D TDESKTOP_API_ID=17349 -D TDESKTOP_API_HASH=344583e45741c457fe1862106095a5eb -D CMAKE_CONFIGURATION_TYPES=Release -D DESKTOP_APP_DISABLE_AUTOUPDATE=ON -D DESKTOP_APP_DISABLE_CRASH_REPORTS=ON
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
