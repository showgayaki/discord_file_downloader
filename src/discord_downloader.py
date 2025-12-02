from pathlib import Path
from logging import getLogger

import asyncio
import aiohttp
import discord

from config.config_loader import load_config


logger = getLogger(__name__)


class DiscordFileDownloader:
    def __init__(self) -> None:
        cfg = load_config()
        self.token = cfg.DISCORD_TOKEN
        self.extensions = cfg.TARGET_FILE_EXTENSIONS
        self.start_dt = cfg.START_DATETIME
        self.end_dt = cfg.END_DATETIME

        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)

        self.download_dir = Path(cfg.ROOT_DIR) / 'downloads'
        self.download_dir.mkdir(exist_ok=True)

        # 並列ダウンロード数（環境に応じて調整）
        self.semaphore = asyncio.Semaphore(5)

        # 成功 / 失敗の集計
        self.success = 0
        self.failed = 0

    def run(self, channel_id: int) -> None:
        @self.client.event
        async def on_ready():
            logger.info(f'Logged in as {self.client.user}')

            channel = self.client.get_channel(channel_id)
            if channel is None:
                logger.error(f'Channel {channel_id} not found')
                await self.client.close()
                return

            if not isinstance(channel, discord.abc.Messageable):
                logger.error(f'Channel {channel_id} is not messageable (no history)')
                await self.client.close()
                return

            # チャンネルごとのダウンロードディレクトリ作成
            self.download_dir = self.download_dir / channel.name
            self.download_dir.mkdir(exist_ok=True)

            # on_ready では重い処理をしない！
            asyncio.create_task(self._process_channel(channel))

        self.client.run(self.token)

    async def _process_channel(self, channel: discord.abc.Messageable):
        logger.info(f'Starting download from channel: {channel.name}')

        tasks = []
        before = None

        while True:
            try:
                history_async = channel.history(limit=100, before=before)
                batch = [m async for m in history_async]
            except Exception as e:
                logger.warning(f"History fetch failed, retrying: {e}")
                await asyncio.sleep(1)
                continue

            if not batch:
                break

            for msg in batch:
                if not (self.start_dt <= msg.created_at <= self.end_dt):
                    continue

                for attachment in msg.attachments:
                    if self._match_extension(attachment.filename):
                        tasks.append(self._download_attachment(attachment))

            before = discord.Object(id=batch[-1].id)

        logger.info(f"Starting {len(tasks)} downloads...")
        await asyncio.gather(*tasks)

        logger.info(f"Download completed: success={self.success}, failed={self.failed}")
        await self.client.close()

    def _match_extension(self, filename: str) -> bool:
        lower = filename.lower()
        return any(lower.endswith(ext.lower()) for ext in self.extensions)

    async def _download_attachment(self, attachment: discord.Attachment) -> None:
        async with self.semaphore:  # 同時に 5 件までダウンロード
            filename = attachment.filename
            url = attachment.url
            dst = self.download_dir / filename

            # 既にダウンロード済みならスキップ
            if dst.exists():
                logger.debug(f"Skip existing file: {dst}")
                return

            for attempt in range(5):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            if resp.status == 429:
                                retry = int(resp.headers.get("Retry-After", 1))
                                logger.warning(f"Rate limited, retrying in {retry}s...")
                                await asyncio.sleep(retry)
                                continue

                            if resp.status != 200:
                                raise RuntimeError(f"HTTP {resp.status}")

                            data = await resp.read()

                    # ファイル書き込みはスレッドセーフに
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, dst.write_bytes, data)

                    logger.info(f"Saved: {dst}")
                    self.success += 1

                    # ちょっと待機
                    await asyncio.sleep(1)
                    return

                except Exception as e:
                    wait = 2 ** attempt
                    logger.warning(f"Failed downloading {filename} (attempt {attempt + 1}/5): {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)

            logger.error(f"Giving up: {filename}")
            self.failed += 1
            # ちょっと待機
            await asyncio.sleep(1)
