[app]
title = SADAF Calculator
package.name = sadafcalc
package.domain = com.sadaf.calculator

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0
requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.api = 33
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
