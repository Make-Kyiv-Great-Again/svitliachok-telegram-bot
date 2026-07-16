from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import aiohttp
from app.api_client import api_client, APIError
from app.db import get_token
import logging
import base64
import json

router = Router()

class AddBusinessState(StatesGroup):
    waiting_for_name = State()
    waiting_for_location = State()

def get_user_id_from_token(token: str) -> int:
    payload = token.split(".")[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    return int(json.loads(base64.b64decode(payload))["sub"])

@router.message(Command("add_business"))
async def cmd_add_business_start(message: types.Message, state: FSMContext):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("You must be logged in to do this. Use /login")
        return
    await state.set_state(AddBusinessState.waiting_for_name)
    await message.answer("What is the name of your business?")

@router.message(AddBusinessState.waiting_for_name)
async def process_business_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    await state.set_state(AddBusinessState.waiting_for_location)
    await message.answer("Please send the location of your business.\n\nYou have two options:\n1. 📎 Use the attachment menu -> **Location** to pick a spot on the map.\n2. ⌨️ Type the coordinates manually (e.g. `50.45 30.52`)", parse_mode="Markdown")

@router.message(AddBusinessState.waiting_for_location)
async def process_business_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
    elif message.text:
        try:
            parts = message.text.replace(",", " ").split()
            lat = float(parts[0])
            lon = float(parts[1])
        except (ValueError, IndexError):
            await message.answer("Invalid format. Please send a valid location or type coordinates like: `50.45 30.52`", parse_mode="Markdown")
            return
    else:
        await message.answer("Please send a location or type the coordinates.")
        return
    
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("You must be logged in to do this. Use /login", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    try:
        response = await api_client.add_business(token, name, lat, lon)
        await message.answer(f"Business '{name}' created successfully! Business ID: {response.get('id')}\nYou can now manage it via /my_businesses")
    except APIError as e:
        await message.answer(f"Failed to add business:\n{str(e)}")
    except Exception as e:
        logging.exception("Unexpected error in process_business_location")
        await message.answer("An unexpected error occurred. Please try again later.")
    finally:
        await state.clear()

async def _show_my_businesses(user_id: int, message: types.Message):
    token = await get_token(user_id)
    if not token:
        await message.answer("You must be logged in to do this. Use /login")
        return

    try:
        backend_user_id = get_user_id_from_token(token)
        all_businesses = await api_client.get_businesses()
        my_businesses = [b for b in all_businesses if b.get("owner_id") == backend_user_id]
        
        if not my_businesses:
            await message.answer("You don't have any businesses registered yet. Use /add_business to add one.")
            return

        text = "🏢 **Your Businesses:**\n\nSelect a business to manage its generator status:"
        buttons = []
        for b in my_businesses:
            status_emoji = "🟢" if b.get("generator_is_running") else "🔴"
            buttons.append([InlineKeyboardButton(text=f"{status_emoji} {b['name']}", callback_data=f"manage_{b['id']}")])
            
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(text, reply_markup=markup, parse_mode="Markdown")
        
    except APIError as e:
        await message.answer(f"Failed to fetch businesses:\n{str(e)}")
    except Exception as e:
        logging.exception("Unexpected error in _show_my_businesses")
        await message.answer("An unexpected error occurred. Please try again later.")

@router.message(Command("my_businesses"))
async def cmd_my_businesses(message: types.Message):
    await _show_my_businesses(message.from_user.id, message)

async def _show_manage_business(business_id: int, user_id: int, message: types.Message):
    token = await get_token(user_id)
    if not token:
        await message.edit_text("You must be logged in to do this.")
        return

    all_businesses = await api_client.get_businesses()
    business = next((b for b in all_businesses if b["id"] == business_id), None)
    
    if not business:
        await message.edit_text("Business not found.")
        return

    is_running = business.get("generator_is_running", False)
    status_text = "🟢 Running" if is_running else "🔴 Off"
    
    text = f"🏢 **{business['name']}**\n\nGenerator Status: {status_text}\nWhat would you like to do?"
    
    buttons = []
    if is_running:
        buttons.append([InlineKeyboardButton(text="Turn Generator OFF 🔴", callback_data=f"toggle_{business_id}_0")])
    else:
        buttons.append([InlineKeyboardButton(text="Turn Generator ON 🟢", callback_data=f"toggle_{business_id}_1")])
        
    buttons.append([InlineKeyboardButton(text="⬅️ Back to List", callback_data="back_to_businesses")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@router.callback_query(F.data.startswith("manage_"))
async def callback_manage_business(callback: types.CallbackQuery):
    business_id = int(callback.data.split("_")[1])
    try:
        await _show_manage_business(business_id, callback.from_user.id, callback.message)
    except Exception as e:
        logging.exception("Error in callback_manage_business")
        await callback.answer("An error occurred.", show_alert=True)
    else:
        await callback.answer()

@router.callback_query(F.data.startswith("toggle_"))
async def callback_toggle_business(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    business_id = int(parts[1])
    turn_on = parts[2] == "1"
    
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer("You are not logged in.", show_alert=True)
        return
        
    try:
        await api_client.update_generator_status(token, str(business_id), is_running=turn_on)
        await callback.answer(f"Generator turned {'ON' if turn_on else 'OFF'}")
        await _show_manage_business(business_id, callback.from_user.id, callback.message)
    except Exception as e:
        logging.exception("Error in callback_toggle_business")
        await callback.answer("Failed to update status.", show_alert=True)

@router.callback_query(F.data == "back_to_businesses")
async def callback_back_to_businesses(callback: types.CallbackQuery):
    await callback.message.delete()
    await _show_my_businesses(callback.from_user.id, callback.message)
    await callback.answer()
