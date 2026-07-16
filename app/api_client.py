import aiohttp
import json
import logging
from app.config import config
from typing import Dict, Any, Optional

class APIError(Exception):
    pass

class APIClient:
    def __init__(self):
        self.base_url = config.api_base_url.rstrip("/")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        if not response.ok:
            if response.status >= 500:
                text = await response.text()
                logging.error(f"Server error {response.status} from {response.url}: {text}")
                raise APIError("An internal server error occurred. Please try again later.")
            try:
                data = await response.json()
                detail = data.get("detail", await response.text())
            except Exception:
                detail = await response.text()
            
            if isinstance(detail, list):
                msgs = []
                for err in detail:
                    msg = err.get("msg", "Validation error")
                    loc = " -> ".join(str(l) for l in err.get("loc", []) if str(l) != "body")
                    if loc:
                        msgs.append(f"• {loc}: {msg}")
                    else:
                        msgs.append(f"• {msg}")
                raise APIError("\n".join(msgs))
            else:
                raise APIError(str(detail))
        return await response.json()

    async def register(self, email: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/register"
        payload = {"email": email, "password": password}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await self._handle_response(response)

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/login"
        # The API expects Form Data: username=<email>&password=<password>
        payload = aiohttp.FormData()
        payload.add_field("username", email)
        payload.add_field("password", password)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                return await self._handle_response(response)

    async def add_business(self, token: str, name: str, lat: float, lon: float) -> Dict[str, Any]:
        url = f"{self.base_url}/businesses/"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "name": name,
            "biz_type": "cafe", # default or derived from user if needed
            "has_generator": True,
            "lat": lat,
            "lon": lon
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                return await self._handle_response(response)

    async def update_generator_status(self, token: str, business_id: str, is_running: bool) -> Dict[str, Any]:
        url = f"{self.base_url}/businesses/{business_id}/status"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "is_open": True,
            "generator_is_running": is_running
        }
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=payload) as response:
                return await self._handle_response(response)

    async def get_businesses(self) -> list:
        url = f"{self.base_url}/businesses/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await self._handle_response(response)

api_client = APIClient()
