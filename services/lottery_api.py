import logging
import asyncio
import aiohttp
import config

logger = logging.getLogger(__name__)

class LotteryAPI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://draw.ar-lottery01.com',
            'Referer': 'https://draw.ar-lottery01.com/',
        }
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=8)
            self.session = aiohttp.ClientSession(headers=self.headers, timeout=timeout)
        return self.session

    def get_big_small(self, number: int) -> str:
        return 'BIG' if number >= 5 else 'SMALL'

    def get_next_issue(self, current_issue: str) -> str:
        try:
            current_issue = str(current_issue).strip()
            if current_issue.isdigit():
                next_val = int(current_issue) + 1
                return str(next_val)
        except Exception:
            pass
        return current_issue

    async def fetch_history(self, game_id: str = "wingo_1m", max_retries: int = 3):
        """Fetch latest game issue history for any WinGo duration (30s, 1m, 3m, 5m)"""
        game_info = config.WINGO_GAMES.get(game_id)
        if not game_info:
            logger.error(f"Unknown game_id: {game_id}")
            return None

        url = game_info["api_url"]

        for attempt in range(1, max_retries + 1):
            try:
                session = await self._get_session()
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.warning(f"[{game_id}] API HTTP {response.status} (Attempt {attempt}/{max_retries})")
                        await asyncio.sleep(1)
                        continue

                    data = await response.json(content_type=None)
                    raw_list = data.get("data", {}).get("list", [])
                    if not raw_list:
                        logger.warning(f"[{game_id}] Empty data list from API")
                        return None

                    formatted_list = []
                    for item in raw_list:
                        try:
                            num_str = str(item.get("number", "0"))
                            digits = [c for c in num_str if c.isdigit()]
                            number = int(digits[0]) if digits else 0
                            issue = str(item.get("issueNumber"))

                            formatted_list.append({
                                "issueNumber": issue,
                                "number": number,
                                "big_small": self.get_big_small(number),
                                "premium": item.get("premium", ""),
                                "sum": item.get("sum", "")
                            })
                        except Exception:
                            continue

                    return formatted_list

            except Exception as e:
                logger.error(f"[{game_id}] Error fetching lottery data (Attempt {attempt}): {e}")
                await asyncio.sleep(1)

        return None

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

lottery_api = LotteryAPI()
