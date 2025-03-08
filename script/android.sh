MACOS:
/Users/jonathanstoff/Library/Android/sdk/emulator/emulator -avd Medium_Phone_API_35

WINDOWS:
emulator -avd Medium_Phone_API_35

sdkmanager "system-images;android-35;google_apis;x86_64"
avdmanager -v create avd -p D:/vbox -n ClipEM -k "system-images;android-35;google_apis;x86_64"
avdmanager create avd -n $ANDROID_AVD_NAME -k "system-images;android-$ANDROID_API_LEVEL;default;x86_64" --force