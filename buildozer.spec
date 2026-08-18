[app]

title = Detectores Rn
package.name = detectoresrn
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.include_patterns = assets/*,*.kv

requirements = python3,kivy,plyer,pillow,reportlab

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,CAMERA,ACCESS_FINE_LOCATION
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 23b
android.arch = arm64-v8a
