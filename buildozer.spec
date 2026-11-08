[app]
title = HomeQRcode
package.name = homeqrcode
package.domain = org.homeqrcode
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,key,txt
source.include_patterns = keys/*.key
version = 0.1
requirements = python3==3.12.1, hostpython3==3.12.1, kivy==2.3.0
orientation = portrait
fullscreen = 0
android.ndk = 27b
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
p4a.branch = master
