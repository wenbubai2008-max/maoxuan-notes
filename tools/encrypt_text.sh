#!/usr/bin/env bash
# 用法：MAOXUAN_PASSWORD=密码 bash tools/encrypt_text.sh
# 把 build/site-text/ 里的明文原文页加密后放进 text/（只有加密后的文件进仓库）
set -euo pipefail
cd "$(dirname "$0")/.."
: "${MAOXUAN_PASSWORD:?请先设置 MAOXUAN_PASSWORD}"
mkdir -p text
npx --yes staticrypt@3.5.4 build/site-text/*.html -d text \
  --password "$MAOXUAN_PASSWORD" --config .staticrypt.json --remember 0 --short \
  --template-title "毛选读注 · 原文" \
  --template-instructions "原文在 2026 年 12 月 31 日前仅供个人阅读，请输入密码。2027 年 1 月 1 日起将自动公开。" \
  --template-button "打开" --template-placeholder "密码" \
  --template-remember "在这台设备上记住密码" --template-error "密码不对，请再试一次" \
  --template-color-primary "#b3261e" --template-color-secondary "#eef1f3"
