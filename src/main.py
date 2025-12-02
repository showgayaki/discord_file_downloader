from logging import getLogger

from config.config_manager import ConfigManager
from logger import load_looger
from discord_downloader import DiscordFileDownloader


config = ConfigManager().config
logger = getLogger(__name__)


def main() -> None:
    load_looger(root_dir=config.ROOT_DIR)
    logger.info(f'Loaded configuration: {config.exclude_confidential()}')

    downloader = DiscordFileDownloader()
    downloader.run(config.TARGET_CHANNEL_ID)


if __name__ == '__main__':
    main()
