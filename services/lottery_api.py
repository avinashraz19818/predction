import logging
import asyncio
from typing import Optional, List, Dict
import httpx

import config

logger = logging.getLogger(__name__)

class LotteryAPI:
    """
    High-performance WinGo Draw History API Client.
    Uses resilient httpx.AsyncClient with TLS verification bypass and persistent pooling,
    guaranteeing reliable connection across any cloud VPS without IPv6/connector hang issues.
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://draw.ar-lottery01.com',
            'Referer': 'https://draw.ar-lottery01.com/',
        }
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        async with self._lock:
            if self._client is None or self._client.is_closed:
                limits = httpx.Limits(max_keepalive_connections=15, max_connections=30)
                timeout = httpx.Timeout(10.0, connect=5.0)
                self._client = httpx.AsyncClient(
                    headers=self.headers,
                    limits=limits,
                    timeout=timeout,
                    verify=False,
                    follow_redirects=True
                )
            return self._client

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

    async def fetch_history(self, game_id: str = "wingo_1m", max_retries: int = 3) -> Optional[List[Dict]]:
        """Fetch latest game issue history for any WinGo duration (30s, 1m, 3m, 5m)"""
        game_info = config.WINGO_GAMES.get(game_id)
        if not game_info:
            logger.error(f"Unknown game_id: {game_id}")
            return None

        url = game_info["api_url"]

        for attempt in range(1, max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.get(url)

                if response.status_code != 200:
                    logger.warning(f"[{game_id}] API HTTP {response.status_code} (Attempt {attempt}/{max_retries})")
                    await asyncio.sleep(1)
                    continue

                data = response.json()
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
                err_type = type(e).__name__
                logger.error(f"[{game_id}] Error fetching lottery data (Attempt {attempt}/{max_retries}): {err_type}: {e}")
                # If client connector had an issue, reset client
                if attempt == max_retries:
                    await self.reset_client()
                await asyncio.sleep(1.0)

        return None

    async def reset_client(self):
        """Re-initializes client session if connection pool encountered network errors"""
        async with self._lock:
            if self._client and not self._client.is_closed:
                try:
                    await self._client.aclose()
                except Exception:
                    pass
            self._client = None

    async def close(self):
        await self.reset_client()


lottery_api = LotteryAPI()
