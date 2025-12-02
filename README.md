# discord_file_downloader

## Discord Settings
### OAuth2
#### OAuth2 URL Generator
##### Scopes
✅ bot

###### Bot Permissions
✅ View Channels  
✅ Read Message History


### Bot
#### Privileged Gateway Intents
🟢 Message Content Intent


## .envサンプル
`.env`ファイルをプロジェクトルートに置く
```
DISCORD_TOKEN=
TARGET_CHANNEL_ID=  # ファイルダウンロード対象のチャンネルID
TARGET_FILE_EXTENSIONS=.mp4  # 複数指定する場合は、カンマ区切りにする

TIMEZONE=Asia/Tokyo
# 時間なしで、日付のみ(ex: START_DATETIME=2024-11-16)の指定でもOK
# その場合は`00:00:00`になる
START_DATETIME=2024-11-16 03:00:00
END_DATETIME=2025-04-03 16:00:00
```
