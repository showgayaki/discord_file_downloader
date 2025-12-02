import os
from pathlib import Path
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    ROOT_DIR: Path
    DISCORD_TOKEN: str
    TARGET_CHANNEL_ID: int
    TARGET_FILE_EXTENSIONS: list[str]
    TIMEZONE: ZoneInfo
    START_DATETIME: datetime
    END_DATETIME: datetime

    def exclude_confidential(self) -> dict:
        """
        トークンやIDなどの機密情報を除外した辞書を返す
        """
        safe = {}
        for key, value in self.__dict__.items():
            if 'TOKEN' in key or 'ID' in key or 'PASSWORD' in key:
                safe[key] = '****'
            else:
                safe[key] = value
        return safe


def load_config() -> Config:
    load_dotenv()  # プロジェクトルートの`.env`ファイル読み込み
    timezone = _load_timezone()

    return Config(
        ROOT_DIR=Path(__file__).parents[2].resolve(),
        DISCORD_TOKEN=os.getenv('DISCORD_TOKEN', ''),
        TARGET_CHANNEL_ID=int(os.getenv('TARGET_CHANNEL_ID', '0')),
        TARGET_FILE_EXTENSIONS=_extensions(),
        TIMEZONE=timezone,
        START_DATETIME=_parse_datetime(os.getenv('START_DATETIME', ''), timezone),
        END_DATETIME=_parse_datetime(os.getenv('END_DATETIME', ''), timezone),
    )


def _extensions() -> list[str]:
    """
    環境変数からカンマ区切りの拡張子リストを取得する。
    空要素は取り除き、前後の空白を削除する。
    """
    # 環境変数はカンマ区切りの文字列として取得し、デフォルトは '.mp4' とする
    extensions_str = os.getenv('TARGET_FILE_EXTENSIONS', '.mp4')
    return [ext.strip() for ext in extensions_str.split(',') if ext.strip()]


def _load_timezone() -> ZoneInfo:
    """
    env の TIMEZONE を読み込んで ZoneInfo を返す。
    未設定の場合は Asia/Tokyo をデフォルトにする。
    """
    tz_name = os.getenv("TIMEZONE", "Asia/Tokyo")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        raise ValueError(f"Invalid timezone name: {tz_name}")


def _parse_datetime(value: str, tz: ZoneInfo) -> datetime:
    """
    START_DATETIME / END_DATETIME を柔軟にパースする
    - YYYY-MM-DD       → 0:00 として扱う
    - YYYY-MM-DD HH:MM:SS → そのまま扱う
    - タイムゾーンは env の TIMEZONE
    - 最終的には UTC に変換して返す
    """
    value = value.strip()

    # YYYY-MM-DD（10文字）の場合
    if len(value) == 10 and value.count("-") == 2:
        dt = datetime.strptime(value, "%Y-%m-%d")
        dt = datetime.combine(dt.date(), time(0, 0, 0))
        dt = dt.replace(tzinfo=tz)
        return dt.astimezone(timezone.utc)

    # YYYY-MM-DD HH:MM:SS の場合
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=tz)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    raise ValueError(f"Invalid datetime format: {value}")
