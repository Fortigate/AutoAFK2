import os
import platform
from subprocess import Popen, PIPE, run

cwd = os.path.dirname(__file__)  # variable for current directory of AutoAFK.exe


# noinspection PyStatementEffect
def manage_adb_exe(command, device_name='127.0.0.1:5555'):
    if platform.system() == "Windows":
        # Get the right ADB path depending on whether we run from Pycharm or compiled .exe
        if os.path.isfile((cwd + '\\output\\adb\\adb.exe')):
            adbpath = os.path.join(cwd, 'output', 'adb', 'adb.exe')  # Locate adb.exe in working directory
        else:
            adbpath = os.path.join(cwd, 'adbutils', 'binaries', 'adb.exe')  # Locate adb.exe in working directory
    else:
        adbpath = "adb"
        if not adb_exist():
            adb_not_installed()

    if command == 'start':
        Popen([adbpath, "start-server"], stderr=PIPE).communicate()[0]

    if command == 'restart':
        Popen([adbpath, "kill-server"], stderr=PIPE).communicate()[0]
        Popen([adbpath, "start-server"], stderr=PIPE).communicate()[0]

    if command == 'connect':
        # logger.info(Popen([adbpath, 'connect', device_name], stdout=PIPE).communicate()[0].decode())
        Popen([adbpath, 'connect', device_name], stdout=PIPE).communicate()[0]


# Check if adb tool is installed
def adb_exist():
    try:
        # Run the 'adb version' command
        result = run(["adb", "version"], stdout=PIPE, stderr=PIPE, text=True)

        # Check if the command executed successfully
        if result.returncode == 0:
            print("ADB is installed.")
            print(result.stdout.strip())  # Print the version information
            return True
        else:
            print("ADB is not installed.")
            print(result.stderr.strip())  # Print the error message
            return False
    except FileNotFoundError:
        # ADB is not found in the system PATH
        print("ADB is not installed or not in PATH.")
        return False


# Print information to user that adb is not installed
# and helpful command that will let user install it
def adb_not_installed():
    if platform.system().lower() == "linux":
        if "arch" in platform.system_alias(platform.system(), platform.release(), platform.version()).lower():
            print("Arch Linux operating system detected")
            print("Try using the following command to install adb")
            print("sudo pacman -S android-tools")
        else:
            print("Linux operating system detected")
            print("Try using the following command to install adb")
            print("sudo apt install android-tools-adb")
    elif platform.system().lower() == "darwin":
        print("MacOS operating system detected")
        print("Try using the following command to install adb")
        print("brew install android-platform-tools")
    elif platform.system().lower() == "windows":
        # windows is currently using injected adb.exe
        return
        # for future - we could get rid of injected .exe, and used ask user to install it, if it is not installed already
        #
        # print("Windows operating system detected")
        # print("Try using the following command to install adb (launch either PowerShell or CMD in administrator mode)")
        # print("choco install adb -y")
    else:
        print("Unrecognized operating system")
