# Kadr Studio Bron-bot — ishga tushirish

## 1. Bot yaratish — ✅ BAJARILDI

Bot yaratilgan: **@kadr_studio_bron_bot** (t.me/kadr_studio_bron_bot)
Token BotFather chatingizda saqlangan (Telegram'da @BotFather bilan suhbatni oching, tokenni shu yerdan nusxalaysiz).

## 2. Guruhga qo'shish — ✅ BAJARILDI

Bot "Kadr jamoasi" guruhiga qo'shilgan.
**Muhim:** bot guruhda xabar yubora olishi (va tugmalar ishlashi) uchun uni **admin** qilib qo'yganingizga ishonch hosil qiling (Guruh → A'zolar → kadr_studio_bron_bot → Promote to admin, "Send Messages" huquqi yetarli).

Guruh `chat_id`si aniqlandi: **`-1003920885751`**

## 3. Mahalliy ishga tushirish (sinov uchun)

```bash
cd kadr-studio-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env faylini oching, faqat BOT_TOKEN va GROUP_CHAT_ID ni to'ldiring (qolganlari allaqachon to'g'ri qiymat bilan tayyor)
python3 bot.py
```

Botni Telegram'da toping va `/start` bosing.

## 4. Render'ga bepul deploy qilish (24/7 ishlashi uchun)

1. [render.com](https://render.com) da akkount oching (GitHub bilan kirsa bo'ladi)
2. Bu loyihani GitHub'ga yuklang (yangi repo, masalan `kadr-studio-bot`)
3. Render'da **New +** → **Background Worker** tanlang
4. GitHub repo'ni ulang
5. Sozlamalar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python3 bot.py`
6. **Environment** bo'limida faqat shu ikkitasini qo'shing (qolgan hammasi kodda standart qiymat bilan tayyor):
   - `BOT_TOKEN` — BotFather chatingizdagi token
   - `GROUP_CHAT_ID` — `-1003920885751`

   Agar kartani, manzilni yoki menejer usernamesini keyinchalik o'zgartirmoqchi bo'lsangiz, shu yerga
   `CARD_NUMBER`, `CARD_HOLDER`, `STUDIO_ADDRESS`, `MANAGER_USERNAME`, `DEPOSIT_AMOUNT` larni ham qo'shishingiz mumkin.
7. Deploy tugmasini bosing — bir necha daqiqada bot 24/7 ishlay boshlaydi

**Muhim:** bookings.db fayli Render'ning bepul tarifida qayta deploy qilinganda o'chib ketishi mumkin (disk doimiy emas). Agar bronlar tarixi doimiy saqlanishi kerak bo'lsa, keyinchalik Render'ning bepul PostgreSQL bazasiga o'tkazish kerak bo'ladi — hozircha oddiy hajm uchun SQLite yetarli.
