#!/bin/sh

STATE="${CLIPBOARD_STATE:-unknown}"
TEXT_BASE64="$(base64 -w 0)"

printf '{"state":"%s","textBase64":"%s"}\n' "$STATE" "$TEXT_BASE64"
