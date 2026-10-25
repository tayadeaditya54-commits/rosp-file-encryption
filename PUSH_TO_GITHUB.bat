@echo off
title Push ROSP File Encryption Project to GitHub - Aditya Tayade
color 0b
echo ======================================================================
echo    PUSHING ROSP FILE ENCRYPTION REPOSITORY TO GITHUB
echo    Presenter: Aditya Tayade ^| B.E. IT ^| ACPCE Kharghar
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/5] Checking Git installation...
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git was not found in your PATH.
    echo Please make sure Git for Windows is installed from: https://git-scm.com/
    pause
    exit /b 1
)

echo [2/5] Initializing Git repository if needed...
if not exist ".git" (
    git init
    git branch -M main
)

echo [3/5] Staging files for commit...
git add file_encryptor.py test_file_encryptor.py test_results.txt README.md
git add EXPERIMENT_10_TECHNICAL_REPORT_Aditya_Tayade.md
git add ROSP_File_Encryption_Interactive_White.html ROSP_File_Encryption_Classroom_Format.html
git add ROSP_File_Encryption_Interactive_White_Aditya_Tayade.pptx
git add ROSP_File_Encryption_Classroom_Format_Aditya_Tayade.pptx
git add PUSH_TO_GITHUB.bat

echo [4/5] Committing changes...
git commit -m "feat(crypto): open source secure file encryption system with authenticated AES-256 and HMAC-SHA256"

echo.
echo ======================================================================
echo Enter your GitHub repository URL:
echo (Example: https://github.com/adityatayade/rosp-file-encryption.git)
echo (Press ENTER to use default: https://github.com/adityatayade/rosp-file-encryption.git)
set /p REPO_URL="Repo URL: "
if "%REPO_URL%"=="" set REPO_URL=https://github.com/adityatayade/rosp-file-encryption.git

echo.
echo Target Repo: %REPO_URL%
git remote remove origin >nul 2>nul
git remote add origin %REPO_URL%

echo.
echo [5/5] Pushing to GitHub (main branch)...
echo (If prompted, sign in with your browser or enter your GitHub credentials)
echo.

git push -u origin main

echo.
echo ======================================================================
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Your repository has been pushed to GitHub!
    echo Refresh your browser at your GitHub repo.
) else (
    echo [NOTE] Push completed or requires GitHub authentication.
    echo If GitHub asks for sign-in, click "Sign in with your browser" in the popup.
)
echo ======================================================================
pause
