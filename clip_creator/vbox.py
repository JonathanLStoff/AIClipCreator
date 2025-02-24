import subprocess
import time
import traceback
from clip_creator.conf import ANDROID_IMAGE_PATH

def start_android_vbox(vbox_vm_name, android_image_path, mode="screen"):
    """Starts a VirtualBox VM with Android and enables ADB connection.

    Args:
        vbox_vm_name: The name of the VirtualBox VM.
        android_image_path: The path to the Android image (ISO or VDI).
        mode: Either "headless" or "screen". Default is "screen".

    Raises:
        RuntimeError: If starting the VM or configuring ADB fails.
    """

    try:
        # Determine the VM start type from the mode
        if mode.lower() == "headless":
            start_type = "headless"
        elif mode.lower() == "screen":
            start_type = "gui"
        else:
            raise ValueError("Invalid mode. Choose 'headless' or 'screen'.")

        # 1. Create and configure the VM if it doesn't exist
        existing_vms = subprocess.run(
            ["VBoxManage", "list", "vms"],
            capture_output=True, text=True, check=True
        )
        if f'"{vbox_vm_name}"' in existing_vms.stdout:
            print(f"VM '{vbox_vm_name}' already exists. Skipping creation and configuration.")
        else:
            subprocess.run(
                ["VBoxManage", "createvm", "--name", vbox_vm_name, "--ostype", "Other_64", "--register"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            subprocess.run(
                ["VBoxManage", "modifyvm", vbox_vm_name, "--memory", "2048", "--cpus", "2"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            subprocess.run(
                ["VBoxManage", "storagectl", vbox_vm_name, "--name", "SATA Controller", "--add", "sata", "--controller", "IntelAhci"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            subprocess.run(
                ["VBoxManage", "storageattach", vbox_vm_name, "--storagectl", "SATA Controller", "--port", "0", "--device", "0", "--type", "hdd", "--medium", android_image_path],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            subprocess.run(
                ["VBoxManage", "modifyvm", vbox_vm_name, "--natpf1", "adb,tcp,,5555,,5555"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        check_vm_status_command = ["VBoxManage", "showvminfo", vbox_vm_name]
        vm_status_process = subprocess.run(check_vm_status_command, capture_output=True, text=True, check=True)
        vm_status_output = vm_status_process.stdout

        if "State: running" in vm_status_output:
            print(f"VM '{vbox_vm_name}' is already running.")
            raise RuntimeError(f"VM '{vbox_vm_name}' is already running. Please stop it first.")
        elif "State: powered off" not in vm_status_output and "State: saved" not in vm_status_output:
            raise RuntimeError(f"VM '{vbox_vm_name}' is in an unexpected state: {vm_status_output}")

        # 2. Start the VM with the chosen mode (headless or screen)
        print(f"Starting VM '{vbox_vm_name}' in {mode} mode...")
        subprocess.Popen(["VBoxManage", "startvm", vbox_vm_name, "--type", start_type],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 3. Wait for the VM to boot
        print("Waiting for Android VM to boot...")
        time.sleep(60)  # Adjust the sleep duration as needed

        # 4. Configure ADB connection
        adb_connect_command = ["adb", "connect", "127.0.0.1:5555"]
        subprocess.run(adb_connect_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ADB connection established.")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error executing command: {traceback.format_exc()}")
    except FileNotFoundError as e:
        raise RuntimeError(f"File not found: {traceback.format_exc()}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {traceback.format_exc()}")

if __name__ == "__main__":
    start_android_vbox("AndroidVM", ANDROID_IMAGE_PATH, mode="screen")