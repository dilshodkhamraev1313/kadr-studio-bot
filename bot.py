from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import date, datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

import db

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "-1003920885751"))
GROUP_TOPIC_ID = int(os.environ.get("GROUP_TOPIC_ID", "87"))
CARD_NUMBER = os.environ.get("CARD_NUMBER", "5614 6835 1146 7011")
CARD_HOLDER = os.environ.get("CARD_HOLDER", "Xamrayev Dilshodjon")
DEPOSIT_AMOUNT = int(os.environ.get("DEPOSIT_AMOUNT", "100000"))
STUDIO_ADDRESS = os.environ.get("STUDIO_ADDRESS", "Toshkent shahri, Binokor ko'chasi 69")
MANAGER_USERNAME = os.environ.get("MANAGER_USERNAME", "kadr_studio_menejer")

ROOMS = {
    "white": {"label": "🤍 White zona", "price_per_hour": 300_000},
    "black": {"label": "🖤 Black zona", "price_per_hour": 400_000},
}


def hours_between(start_time: str, end_time: str) -> float:
    sh, sm = (int(x) for x in start_time.split(":"))
    eh, em = (int(x) for x in end_time.split(":"))
    return ((eh * 60 + em) - (sh * 60 + sm)) / 60

STUDIO_OPEN = "08:00"
STUDIO_CLOSE = "23:00"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kadr-studio-bot")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# The bot must never respond to messages in the team group — booking conversations
# only happen in a private chat with the bot. Callback buttons (confirm/reject) are
# unaffected since those are handled by callback_query handlers, not message handlers.
router.message.filter(F.chat.type == "private")


class Booking(StatesGroup):
    choosing_room = State()
    choosing_date = State()
    choosing_time = State()
    awaiting_proof = State()


def room_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{r['label']} — {r['price_per_hour']:,} so'm/soat".replace(",", " "),
            callback_data=f"room:{key}",
        )]
        for key, r in ROOMS.items()
    ])


def confirm_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm:{booking_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{booking_id}"),
    ]])


def fmt_money(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " so'm"


def parse_date(text: str) -> date | None:
    text = text.strip()
    m = re.match(r"^(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?$", text)
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), m.group(3)
    today = date.today()
    year = int(year) if year else today.year
    try:
        d = date(year, month, day)
    except ValueError:
        return None
    if not year_given(m) and d < today:
        d = date(year + 1, month, day)
    if d < today or d > today + timedelta(days=180):
        return None
    return d


def year_given(match: re.Match) -> bool:
    return match.group(3) is not None


def parse_time_range(text: str) -> tuple[str, str] | None:
    m = re.match(r"^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$", text.strip())
    if not m:
        return None
    sh, sm, eh, em = (int(x) for x in m.groups())
    if not (0 <= sh <= 23 and 0 <= eh <= 23 and 0 <= sm <= 59 and 0 <= em <= 59):
        return None
    start = f"{sh:02d}:{sm:02d}"
    end = f"{eh:02d}:{em:02d}"
    if start >= end:
        return None
    if start < STUDIO_OPEN or end > STUDIO_CLOSE:
        return None
    duration_minutes = (eh * 60 + em) - (sh * 60 + sm)
    if duration_minutes < 60:
        return None
    return start, end


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject):
    await state.clear()
    payload = (command.args or "").strip().lower()

    await message.answer(
        "👋 Assalomu alaykum, <b>Kadr Studio</b>ga xush kelibsiz!\n\n"
        "Men sizga studiyani bron qilishda yordam beraman.",
        parse_mode="HTML",
    )

    if payload in ROOMS:
        await state.update_data(room=payload)
        await state.set_state(Booking.choosing_date)
        r = ROOMS[payload]
        await message.answer(
            f"Siz tanladingiz: <b>{r['label']}</b> — {fmt_money(r['price_per_hour'])} / soat\n\n"
            "📅 Qaysi sanaga bron qilmoqchisiz?\n"
            "Masalan: <code>25.07</code>",
            parse_mode="HTML",
        )
    else:
        await state.set_state(Booking.choosing_room)
        await message.answer("Qaysi zonani tanlaysiz?", reply_markup=room_keyboard())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi. Qaytadan boshlash uchun /start bosing.")


@router.callback_query(F.data.startswith("room:"))
async def on_room_chosen(callback: CallbackQuery, state: FSMContext):
    room_key = callback.data.split(":", 1)[1]
    await state.update_data(room=room_key)
    await state.set_state(Booking.choosing_date)
    r = ROOMS[room_key]
    await callback.message.edit_text(f"Siz tanladingiz: {r['label']} — {fmt_money(r['price_per_hour'])} / soat")
    await callback.message.answer(
        "📅 Qaysi sanaga bron qilmoqchisiz?\nMasalan: <code>25.07</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Booking.choosing_date)
async def on_date_input(message: Message, state: FSMContext):
    d = parse_date(message.text or "")
    if not d:
        await message.answer(
            "Sanani to'g'ri formatda kiriting, masalan: <code>25.07</code> "
            "(kun.oy). Sana bugundan keyin bo'lishi kerak.",
            parse_mode="HTML",
        )
        return
    await state.update_data(booking_date=d.isoformat(), booking_date_human=d.strftime("%d.%m.%Y"))
    await state.set_state(Booking.choosing_time)
    await message.answer(
        "🕐 Necha soatdan nechigacha kerak?\n"
        f"Masalan: <code>10:00-13:00</code> (ish vaqti {STUDIO_OPEN}-{STUDIO_CLOSE}, min. 1 soat)",
        parse_mode="HTML",
    )


@router.message(Booking.choosing_time)
async def on_time_input(message: Message, state: FSMContext):
    rng = parse_time_range(message.text or "")
    if not rng:
        await message.answer(
            "Vaqtni to'g'ri formatda kiriting, masalan: <code>10:00-13:00</code>. "
            f"Studiya ish vaqti: {STUDIO_OPEN}-{STUDIO_CLOSE}, minimal davomiylik 1 soat.",
            parse_mode="HTML",
        )
        return
    start_time, end_time = rng
    data = await state.get_data()
    room_key = data["room"]
    booking_date = data["booking_date"]

    conflicts = db.find_conflicts(room_key, booking_date, start_time, end_time)
    if conflicts:
        busy = db.list_busy_ranges(room_key, booking_date)
        busy_text = "\n".join(f"  • {s}-{e}" for s, e in busy)
        await message.answer(
            "😔 Kechirasiz, bu vaqt band. Shu kuni band qilingan vaqtlar:\n"
            f"{busy_text}\n\n"
            "Boshqa vaqt kiriting (masalan: <code>14:00-17:00</code>):",
            parse_mode="HTML",
        )
        return

    duration = hours_between(start_time, end_time)
    total_price = round(duration * ROOMS[room_key]["price_per_hour"])
    await state.update_data(start_time=start_time, end_time=end_time, total_price=total_price)
    r = ROOMS[room_key]
    await state.set_state(Booking.awaiting_proof)

    duration_label = f"{duration:g} soat"
    summary = (
        "✅ <b>Bu vaqt bo'sh!</b>\n\n"
        f"🏠 Zona: {r['label']}\n"
        f"📅 Sana: {data['booking_date_human']}\n"
        f"🕐 Vaqt: {start_time}–{end_time} ({duration_label})\n"
        f"💰 Umumiy narx: {fmt_money(total_price)} ({fmt_money(r['price_per_hour'])}/soat)\n\n"
        f"Joyni ushlab turish uchun <b>minimal {fmt_money(DEPOSIT_AMOUNT)} avans</b> to'lashingiz kerak:\n\n"
        f"💳 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: {CARD_HOLDER}\n\n"
        "To'lovni amalga oshirib, chek/skrinshotni shu yerga rasm qilib yuboring 📸"
    )
    await message.answer(summary, parse_mode="HTML")


@router.message(Booking.awaiting_proof, F.photo)
async def on_proof_received(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    room_key = data["room"]
    r = ROOMS[room_key]
    user = message.from_user

    booking_id = db.create_booking(
        room=room_key,
        booking_date=data["booking_date"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        tg_user_id=user.id,
        tg_username=user.username or "",
        tg_fullname=user.full_name,
    )

    caption = (
        "🆕 <b>Yangi bron so'rovi</b>\n\n"
        f"👤 Mijoz: {user.full_name}"
        + (f" (@{user.username})" if user.username else " (username yo'q)") + "\n"
        f"🏠 Zona: {r['label']}\n"
        f"📅 Sana: {data['booking_date_human']}\n"
        f"🕐 Vaqt: {data['start_time']}–{data['end_time']}\n"
        f"💰 Narx: {fmt_money(data['total_price'])} (avans: {fmt_money(DEPOSIT_AMOUNT)})\n\n"
        f"Bron ID: #{booking_id}"
    )
    photo = message.photo[-1]
    sent = await bot.send_photo(
        GROUP_CHAT_ID,
        photo.file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=confirm_keyboard(booking_id),
        message_thread_id=GROUP_TOPIC_ID,
    )
    db.attach_receipt(booking_id, photo.file_id, GROUP_CHAT_ID, sent.message_id)

    await state.clear()
    await message.answer(
        "🙏 Rahmat! To'lovingiz jamoamiz tomonidan tekshirilmoqda.\n"
        "Tasdiqlangach sizga xabar beramiz ✅"
    )


@router.message(Booking.awaiting_proof)
async def on_proof_missing(message: Message):
    await message.answer("Iltimos, to'lov chekini rasm (skrinshot) shaklida yuboring 📸")


@router.callback_query(F.data.startswith("confirm:"))
async def on_confirm(callback: CallbackQuery, bot: Bot):
    booking_id = int(callback.data.split(":", 1)[1])
    booking = db.get_booking(booking_id)
    if not booking:
        await callback.answer("Bron topilmadi", show_alert=True)
        return
    if booking["status"] != "pending":
        await callback.answer("Bu bron allaqachon ko'rib chiqilgan", show_alert=True)
        return

    admin_name = callback.from_user.full_name
    db.set_status(booking_id, "confirmed", admin_name)

    r = ROOMS[booking["room"]]
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ <b>TASDIQLANDI</b> — {admin_name}",
        parse_mode="HTML",
        reply_markup=None,
    )
    try:
        await bot.send_message(
            booking["tg_user_id"],
            "🎉 <b>Bronlaringiz tasdiqlandi!</b>\n\n"
            f"🏠 Zona: {r['label']}\n"
            f"📅 Sana: {datetime.fromisoformat(booking['booking_date']).strftime('%d.%m.%Y')}\n"
            f"🕐 Vaqt: {booking['start_time']}–{booking['end_time']}\n\n"
            f"📍 Manzil: {STUDIO_ADDRESS}\n\n"
            f"Savol bo'lsa: @{MANAGER_USERNAME}\n"
            "Ko'rishguncha! 🎬",
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Failed to notify client %s", booking["tg_user_id"])
    await callback.answer("Tasdiqlandi ✅")


@router.callback_query(F.data.startswith("reject:"))
async def on_reject(callback: CallbackQuery, bot: Bot):
    booking_id = int(callback.data.split(":", 1)[1])
    booking = db.get_booking(booking_id)
    if not booking:
        await callback.answer("Bron topilmadi", show_alert=True)
        return
    if booking["status"] != "pending":
        await callback.answer("Bu bron allaqachon ko'rib chiqilgan", show_alert=True)
        return

    admin_name = callback.from_user.full_name
    db.set_status(booking_id, "rejected", admin_name)

    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n❌ <b>RAD ETILDI</b> — {admin_name}",
        parse_mode="HTML",
        reply_markup=None,
    )
    try:
        await bot.send_message(
            booking["tg_user_id"],
            "😔 Afsuski, to'lovingizni tasdiqlay olmadik.\n"
            f"Iltimos, menejer bilan bog'laning: @{MANAGER_USERNAME}\n"
            "Yoki qaytadan urinib ko'ring: /start",
        )
    except Exception:
        logger.exception("Failed to notify client %s", booking["tg_user_id"])
    await callback.answer("Rad etildi")


@router.message()
async def fallback(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer(
            "Studiyani bron qilish uchun /start ni bosing.\n"
            "Savol bo'lsa: @" + MANAGER_USERNAME
        )


async def run_healthcheck_server():
    """Tiny HTTP server so Render's free Web Service tier accepts this process
    (it requires binding to $PORT) and so an external uptime pinger can keep it awake."""
    from aiohttp import web

    async def health(request):
        return web.Response(text="Kadr Studio bot is running")

    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Healthcheck server listening on port %s", port)


async def main():
    db.init_db()
    logger.info("Kadr Studio booking bot starting...")
    await asyncio.gather(
        run_healthcheck_server(),
        dp.start_polling(bot),
    )


if __name__ == "__main__":
    asyncio.run(main())
