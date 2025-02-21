import subprocess
import time
def start_android_vbox(vbox_vm_name, android_image_path):
    """Starts a VirtualBox VM with Android and enables ADB connection.

    Args:
        vbox_vm_name: The name of the VirtualBox VM.
        android_image_path: The path to the Android image (e.g., an ISO or VDI).

    Raises:
        RuntimeError: If starting the VM or configuring ADB fails.
    """

    try:
        # 1. Start the VirtualBox VM (replace with your actual command)
        #  - headless: Start VM in headless mode (no GUI)
        #  - separate: Start VM in separate process
        #  - --startvm <vmname>
        #  - --type gui: Start VM with GUI
        #  - --type headless: Start VM without GUI
        #  - --type separate: Start VM in separate process
        # Example using VBoxManage:
        # subprocess.Popen(["VBoxManage", "startvm", vbox_vm_name, "--type", "gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Create a new VM registered with VirtualBox using the provided android_image_path
        # Check if the VM already exists
        existing_vms = subprocess.run(
            ["VBoxManage", "list", "vms"],
            capture_output=True, text=True, check=True
        )
        if f'"{vbox_vm_name}"' in existing_vms.stdout:
            print(f"VM '{vbox_vm_name}' already exists. Skipping creation and configuration.")
        else:
            subprocess.run(
            ["VBoxManage", "createvm", "--name", vbox_vm_name, "--ostype", "OtherLinux", "--register"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # (Optional) Configure the VM settings, such as memory and CPUs
            subprocess.run(
            ["VBoxManage", "modifyvm", vbox_vm_name, "--memory", "2048", "--cpus", "2"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Add a SATA storage controller named "SATA Controller"
            subprocess.run(
            ["VBoxManage", "storagectl", vbox_vm_name, "--name", "SATA Controller", "--add", "sata", "--controller", "IntelAhci"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Attach the Android image as the primary hard disk
            subprocess.run(
            ["VBoxManage", "storageattach", vbox_vm_name, "--storagectl", "SATA Controller", "--port", "0", "--device", "0", "--type", "hdd", "--medium", android_image_path],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Set up NAT port forwarding so that ADB on the host can access port 5555 on the VM
            subprocess.run(
            ["VBoxManage", "modifyvm", vbox_vm_name, "--natpf1", "adb,tcp,,5555,,5555"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        check_vm_status_command = ["VBoxManage", "showvminfo", vbox_vm_name]
        vm_status_process = subprocess.run(check_vm_status_command, capture_output=True, text=True, check=True)  # capture_output and text for easier parsing
        vm_status_output = vm_status_process.stdout

        if "State: running" in vm_status_output:
            print(f"VM '{vbox_vm_name}' is already running.")
            # If you want to connect to ADB even if already running, uncomment these lines:
            # adb_connect(vbox_vm_name)
            # return  # Exit the start_android_vbox function
            raise RuntimeError(f"VM '{vbox_vm_name}' is already running. Please stop it first.") # Or raise an error
        elif "State: powered off" not in vm_status_output and "State: saved" not in vm_status_output: # Check for other states that might prevent starting
            raise RuntimeError(f"VM '{vbox_vm_name}' is in an unexpected state: {vm_status_output}")



        # 2. Start the VirtualBox VM
        print(f"Starting VM '{vbox_vm_name}'...")
        vm_process = subprocess.Popen(["VBoxManage", "startvm", vbox_vm_name, "--type", "separate"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # ... (rest of the code for waiting, ADB connection, scrcpy remains the same)

        # 3. Wait a bit for the VM to boot (adjust as needed)
        print("Waiting for Android VM to boot...")
        time.sleep(60)  # Wait for 60 seconds (adjust as needed)

        # 3. Configure ADB connection (replace with your actual device details).
        # This usually involves connecting to the VM's guest port.
        # You might need to forward a port in VirtualBox's network settings.
        # Check your Android VM's network settings.  Commonly, the guest will be 5555.
        # Example using adb connect (you may need to specify the IP/port):
        #  - In VirtualBox, go to the VM settings -> Network -> Adapter 1 (or your adapter) -> Port Forwarding.
        #  - Add a rule: Host Port: 5555, Guest Port: 5555.  Make sure the IP is correct.
        #  - If the Android VM is using NAT, the host and guest ports are usually the same.
        #  - If the Android VM is using Bridged Adapter, you might need to find the Android VM's IP address and use that.
        adb_connect_command = ["adb", "connect", "127.0.0.1:5555"]  # Use 127.0.0.1 if using port forwarding
        # If using Bridged Adapter and you know the IP:
        # adb_connect_command = ["adb", "connect", "192.168.1.100:5555"]  # Example IP

        subprocess.run(adb_connect_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ADB connection established.")

        # 4. (Optional) Start a GUI tool to view the Android screen.
        # You can use tools like `scrcpy` (recommended) or `adb shell wm size` with `adb shell dumpsys window windows | grep Display` to find the resolution and then `ffmpeg` to record.
        # Install scrcpy:  `sudo apt install scrcpy` (or the equivalent for your system).
        # Example using scrcpy:
        subprocess.Popen(["scrcpy"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # Start scrcpy in a new process

        print("Android screen displayed (using scrcpy).")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error executing command: {e}")
    except FileNotFoundError as e:
        raise RuntimeError(f"File not found: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")