from pathlib import Path
from logging import getLogger

import requests
import discord

from config.config_manager import ConfigManager


logger = getLogger(__name__)


class DiscordFileDownloader:
    def __init__(self) -> None:
        cfg = ConfigManager().config
        self.token = cfg.DISCORD_TOKEN
        self.extensions = cfg.TARGET_FILE_EXTENSIONS
        self.start_dt = cfg.START_DATETIME
        self.end_dt = cfg.END_DATETIME

        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(
            intents=intents
        )

        self.download_dir = Path(cfg.ROOT_DIR) / "downloads"
        self.download_dir.mkdir(exist_ok=True)

    def run(self, channel_id: int) -> None:
        @self.client.event
        async def on_ready():
            logger.info(f"Logged in as {self.client.user}")

            channel = self.client.get_channel(channel_id)
            if channel is None:
                logger.error(f"Channel {channel_id} not found")
                await self.client.close()
                return

            if not isinstance(channel, discord.abc.Messageable):
                logger.error(f"Channel {channel_id} is not messageable (no history)")
                await self.client.close()
                return

            async for msg in channel.history(limit=None):
                # --- 期間フィルタ ---
                if not (self.start_dt <= msg.created_at <= self.end_dt):
                    continue

                logger.debug(f"Processing message {msg.id} at {msg.created_at} attachments: {msg.attachments}")

                # --- 添付ファイルフィルタ ---
                for attachment in msg.attachments:
                    if not self._match_extension(attachment.filename):
                        continue

                    await self._download_attachment(attachment)

            logger.info("Download completed.")
            await self.client.close()

        self.client.run(self.token)

    def _match_extension(self, filename: str) -> bool:
        lower = filename.lower()
        return any(lower.endswith(ext.lower()) for ext in self.extensions)

    async def _download_attachment(self, attachment: discord.Attachment) -> None:
        logger.info(f"Downloading {attachment.filename} from {attachment.url}")

        dst = self.download_dir / attachment.filename

        res = requests.get(attachment.url, timeout=6)
        with open(dst, "wb") as f:
            f.write(res.content)

        logger.info(f"Saved to {dst}")
