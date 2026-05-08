import logging
import json
import hmac
import hashlib
from urllib.parse import parse_qsl
from aiohttp import web
import aiohttp_jinja2
import jinja2

from database.db import get_schedules, add_schedule, get_user_role
try:
    from config import ADMIN_IDS, TOKEN
except ImportError:
    ADMIN_IDS = []
    TOKEN = ""

routes = web.RouteTableDef()

@routes.get('/webapp')
@aiohttp_jinja2.template('webapp.html')
async def webapp_handler(request):
    return {}

@routes.get('/api/schedules')
async def api_get_schedules(request):
    schedules = get_schedules()
    return web.json_response(schedules)

@routes.post('/api/schedules')
async def api_post_schedules(request):
    try:
        data = await request.json()

        # Secure auth check using Telegram initData
        init_data = data.get('initData')
        if not init_data:
            return web.json_response({"error": "Unauthorized, missing initData"}, status=403)

        if not check_webapp_signature(TOKEN, init_data):
             return web.json_response({"error": "Invalid signature"}, status=403)

        parsed_data = dict(parse_qsl(init_data))
        user_data = json.loads(parsed_data.get('user', '{}'))
        user_id = user_data.get('id')

        if not user_id or int(user_id) not in ADMIN_IDS:
            return web.json_response({"error": "Unauthorized, not an admin"}, status=403)

        day = data.get('day')
        time = data.get('time')
        subject = data.get('subject')
        teacher = data.get('teacher')

        if not all([day, time, subject, teacher]):
            return web.json_response({"error": "Missing fields"}, status=400)

        add_schedule(day, time, subject, teacher)
        return web.json_response({"status": "ok"})
    except Exception as e:
        logging.error(f"Error in api_post_schedules: {e}")
        return web.json_response({"error": "Server error"}, status=500)

@routes.get('/api/role')
async def api_get_role(request):
    try:
        init_data = request.query.get('initData')
        if not init_data or not check_webapp_signature(TOKEN, init_data):
            return web.json_response({"error": "Invalid or missing signature"}, status=403)

        parsed_data = dict(parse_qsl(init_data))
        user_data = json.loads(parsed_data.get('user', '{}'))
        user_id = user_data.get('id')

        if not user_id:
             return web.json_response({"error": "Missing user_id in initData"}, status=400)

        user_id = int(user_id)
        if user_id in ADMIN_IDS:
            return web.json_response({"role": "admin"})

        role = get_user_role(user_id)
        return web.json_response({"role": role if role else "unknown"})
    except Exception as e:
         logging.error(f"Error in api_get_role: {e}")
         return web.json_response({"error": "Server error"}, status=500)


def check_webapp_signature(token: str, init_data: str) -> bool:
    """
    Validates the data received from the Telegram Web App,
    using the method described at https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        return False

    if "hash" not in parsed_data:
        return False

    hash_from_telegram = parsed_data.pop("hash")

    # Sort keys alphabetically
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=token.encode(),
        digestmod=hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    return calculated_hash == hash_from_telegram

def init_webapp():
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
    app.add_routes(routes)
    return app
