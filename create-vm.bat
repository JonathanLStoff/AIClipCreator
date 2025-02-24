@echo off
REM Create Android VM in VirtualBox
REM Usage: create-android-vm.bat <vm_name> <android_image_path>

if "%~1"=="" (
    echo Error: VM name not provided
    echo Usage: create-android-vm.bat ^<vm_name^> ^<android_image_path^>
    exit /b 1
)

if "%~2"=="" (
    echo Error: Android image path not provided
    echo Usage: create-android-vm.bat ^<vm_name^> ^<android_image_path^>
    exit /b 1
)

set VM_NAME=%~1
set ANDROID_IMAGE=%~2

REM Check if VM already exists
VBoxManage list vms | findstr /C:"%VM_NAME%" >nul
if %errorlevel% equ 0 (
    echo VM '%VM_NAME%' already exists. Skipping creation and configuration.
    exit /b 0
)

REM Create the VM
echo Creating VM '%VM_NAME%'...
VBoxManage createvm --name "%VM_NAME%" --ostype "Other_64" --register

REM Configure VM hardware
echo Configuring VM hardware...
VBoxManage modifyvm "%VM_NAME%" --memory 2048 --cpus 2

REM Create and configure storage controller
echo Setting up storage...
VBoxManage storagectl "%VM_NAME%" --name "SATA Controller" --add sata --controller IntelAhci

REM Attach Android image
echo Attaching Android image...
VBoxManage storageattach "%VM_NAME%" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "%ANDROID_IMAGE%"

REM Configure port forwarding for ADB
echo Setting up ADB port forwarding...
VBoxManage modifyvm "%VM_NAME%" --natpf1 "adb,tcp,,5555,,5555"

echo VM creation completed successfully.