
WINDOWS:

adb connect 127.0.0.1:5555
adb -e push {local file} /sdcard/Pictures/filename
adb -s 127.0.0.1:5555  push "D:/tmp/clips/reddit1j5d5ap.mp4" /sdcard/Pictures/reddit1j5d5ap.mp4
"C:\Program Files\BlueStacks_nxt\HD-Player.exe" --hidden --instance clipsphone

pm create-user User_Name
am switch-user User_ID
pm list users
pm remove-user User_ID

adb shell uiautomator dump /sdcard/window_dump.xml && adb pull /sdcard/window_dump.xml .
