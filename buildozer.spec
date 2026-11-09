[app]
title = HomeQRcode
package.name = homeqrcode
package.domain = org.homeqrcode

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,key,txt
version = 0.5

# python3, hostpython3, Cython, setuptools, requests и прочее p4a подтягивает
# сам как зависимости рецептов. Здесь — только то, что реально импортирует код.
requirements = python3,kivy==2.3.1,numpy,opencv,Pillow,qrcode,pycryptodome,androidstorage4kivy

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 26
android.ndk = 27b

# Один ABI: сборка вдвое быстрее
android.archs = arm64-v8a

android.permissions = CAMERA,READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.accept_sdk_license = True
android.allow_backup = True

# Фиксируем p4a: сборка воспроизводима, и этот тег поставляет
# Python 3.14.2 + Kivy 2.3.1 + numpy 2.3.0 + opencv 4.12.0
p4a.branch = v2026.05.09
