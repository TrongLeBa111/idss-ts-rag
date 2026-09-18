# Hướng dẫn Cài đặt IDSS Slack Bot

## Bước 1: Tạo Slack App
1. Vào https://api.slack.com/apps → Create New App → From scratch
2. Tên: IDSS-Bot → Chọn workspace test
3. OAuth & Permissions → Thêm scopes: chat:write, commands, app_mentions:read
4. Cài app → Copy Bot User OAuth Token (xoxb-...)
5. Basic Information → Copy Signing Secret

## Bước 2: Thêm Slash Commands
/forecast  — Dự báo doanh số
/anomaly   — Phát hiện bất thường
/idss      — Trợ lý IDSS

## Bước 3: Cấu hình .env
SLACK_BOT_TOKEN=xoxb-xxxx
SLACK_SIGNING_SECRET=xxxx
SLACK_APP_TOKEN=xapp-xxxx   # Socket Mode
SLACK_PORT=3000

## Bước 4: Chạy
pip install slack-bolt
python src/integrations/slack_bot.py

## Test
/forecast furniture november 2017
/anomaly technology
/idss help