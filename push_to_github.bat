@echo off
setlocal
echo ========================================================
echo  SHALIK FURNITURE - Push Updates to GitHub
echo ========================================================

set "PATH=C:\Users\archs\AppData\Local\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd;%PATH%"

git status
echo.
set /p msg="Enter commit message (or press ENTER for default): "
if "%msg%"=="" set msg=Update Shalik Furniture Suite

echo Staging all changes...
git add .

echo Committing...
git commit -m "%msg%"

echo Pushing to origin main...
git push -u origin main

echo.
echo ========================================================
echo  Finished! Check: https://github.com/arch-sakhawat/SHALIK-FURNITURE
echo ========================================================
pause
