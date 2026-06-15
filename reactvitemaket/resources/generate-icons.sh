#!/usr/bin/env bash
#
# Генерация иконок Android + iOS по фирменному SVG «Белпомощник».
# Требует ImageMagick (`magick`).
#
# Запуск:  bash reactvitemaket/resources/generate-icons.sh
# Источник дизайна: resources/icon.svg и компонент Logo (belp-ui.tsx).
#
set -euo pipefail
cd "$(dirname "$0")/.."                       # → reactvitemaket/
RES="android/app/src/main/res"
IOS="ios/App/App/Assets.xcassets/AppIcon.appiconset"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- мастера 1024 ---
# ImageMagick без librsvg на разных машинах нестабильно рендерит SVG-градиент.
# Поэтому PNG собираем из тех же токенов, что записаны в resources/icon.svg.
magick -size 1024x1024 xc:"#0056FF" \
  \( -size 1024x1024 xc:"#2277FF" -alpha set -channel A -evaluate set 45% +channel \) -compose over -composite \
  \( -size 1024x1024 xc:"#9BB8FF" -alpha set -channel A -evaluate set 22% +channel \) -compose over -composite \
  "$TMP/bg.png"

magick "$TMP/bg.png" -gravity center -font "Arial-Bold" -pointsize 600 -fill white \
  -annotate +0+40 "Б" "$TMP/icon.png"        # полный знак (iOS + legacy Android)
magick -size 1024x1024 xc:none -gravity center -font "Arial-Bold" -pointsize 560 -fill white \
  -annotate +0+30 "Б" "$TMP/fg.png"          # foreground (только «Б», прозрачный фон)

# --- iOS (один файл 1024) ---
cp "$TMP/icon.png" "$IOS/AppIcon-512@2x.png"

# --- Android legacy ic_launcher / ic_launcher_round ---
for pair in "mdpi:48" "hdpi:72" "xhdpi:96" "xxhdpi:144" "xxxhdpi:192"; do
  d="${pair%%:*}"; s="${pair##*:}"
  magick "$TMP/icon.png" -resize "${s}x${s}" "$RES/mipmap-$d/ic_launcher.png"
  cp "$RES/mipmap-$d/ic_launcher.png" "$RES/mipmap-$d/ic_launcher_round.png"
done

# --- Android adaptive: foreground («Б») + background (градиент) ---
for pair in "mdpi:108" "hdpi:162" "xhdpi:216" "xxhdpi:324" "xxxhdpi:432"; do
  d="${pair%%:*}"; s="${pair##*:}"
  magick "$TMP/fg.png" -resize "${s}x${s}" "$RES/mipmap-$d/ic_launcher_foreground.png"
  magick "$TMP/bg.png" -resize "${s}x${s}" "$RES/mipmap-$d/ic_launcher_background.png"
done

# --- PWA / браузер (полный знак) ---
magick "$TMP/icon.png" -resize 512x512 public/icon-512.png
magick "$TMP/icon.png" -resize 192x192 public/icon-192.png
magick "$TMP/icon.png" -resize 180x180 public/apple-touch-icon.png

echo "✅ Иконки сгенерированы (Android mipmap-*, iOS AppIcon, PWA public/)."
echo "   adaptive-XML уже ссылается на @mipmap/ic_launcher_background (градиентный фон)."
