from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
import aiohttp
from app.api_client import api_client, APIError
from app.db import set_token
import logging

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        "Welcome to the Svitliachok Bot! 🔦\n\n"
        "Available commands:\n"
        "/register <email> <password> - Register a new account\n"
        "/login <email> <password> - Log into your account\n"
        "/add_business - Register a new business interactively\n"
        "/my_businesses - Manage your businesses and generators"
    )
    await message.answer(welcome_text)

@router.message(Command("register"))
async def cmd_register(message: types.Message):
    args = message.text.split()[1:]
    if len(args) != 2:
        await message.answer("Usage: /register <email> <password>")
        return
    
    email, password = args[0], args[1]
    
    try:
        response = await api_client.register(email, password)
        await message.answer(f"Registration successful! User ID: {response.get('id')}\nYou can now /login")
    except APIError as e:
        await message.answer(f"Registration failed:\n{str(e)}")
    except Exception as e:
        logging.exception("Unexpected error in cmd_register")
        await message.answer("An unexpected error occurred. Please try again later.")

@router.message(Command("login"))
async def cmd_login(message: types.Message):
    args = message.text.split()[1:]
    if len(args) != 2:
        await message.answer("Usage: /login <email> <password>")
        return
    
    email, password = args[0], args[1]
    
    try:
        response = await api_client.login(email, password)
        access_token = response.get("access_token")
        if access_token:
            await set_token(message.from_user.id, access_token)
            await message.answer("Login successful! Token saved securely.")
        else:
            await message.answer("Login failed: No access token received.")
    except APIError as e:
        await message.answer(f"Login failed:\n{str(e)}")
    except Exception as e:
        logging.exception("Unexpected error in cmd_login")
        await message.answer("An unexpected error occurred. Please try again later.")
