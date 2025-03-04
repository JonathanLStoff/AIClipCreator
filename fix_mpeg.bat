@echo off
setlocal

set "input_folder=C:\Users\legoc\Desktop\AI\AIClipCreator\tmp\clips"
set "output_folder=C:\Users\legoc\Desktop\AI\AIClipCreator\tmp\fixedclips"

if not exist "%output_folder%" mkdir "%output_folder%"

for %%i in ("%input_folder%\*.mp4") do (
    set "input_file=%input_folder%\%%~nxi"  REM: Full path with quotes
    set "output_file=%output_folder%\%%~ni.mp4"

    echo Processing "%input_folder%\%%~nxi"...
    ffmpeg -i "%input_folder%\%%~nxi" -c:v copy -c:a aac -strict experimental "%output_folder%\%%~ni.mp4"
    if errorlevel 1 (
        echo Error processing "%%~nxi"
    ) else (
        echo "%%~nxi" processed successfully.
    )
)

echo.
echo Finished processing all files.
endlocal
pause