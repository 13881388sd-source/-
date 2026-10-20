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

icon.filename = %(source.dir)s/data/icon.png
icon.adaptive_foreground.filename = %(source.dir)s/data/icon_fg.png
icon.adaptive_background.filename = %(source.dir)s/data/icon_bg.png
presplash.filename = %(source.dir)s/data/presplash.png
android.presplash_color = #0A0A0A

android.api = 33
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
