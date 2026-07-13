# Kadr Studio Bron-bot — ishga tushirish

## 1. Bot yaratish (agar hali yo'q bo'lsa)

1. Telegram'da **@BotFather**ga yozing
2. `/newbot` buyrug'ini yuboring, nomini kiriting (masalan: `Kadr Studio Bron`)
3. Username so'raydi — masalan `kadr_studio_bron_bot` (oxiri `bot` bilan tugashi shart)
4. BotFather sizga **token** beradi (masalan `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxx`) — shuni saqlab qo'ying

## 2. Botni "Kadr jamoasi" guruhiga qo'shish

1. Yangi botni "Kadr jamoasi" guruhiga a'zo qilib qo'shing
2. Guruhda botga **admin** huquqi bering (xabar yuborishi uchun)
3. Guruhning `chat_id` raqamini bilish uchun: guruhga istalgan xabar yozing, so'ng brauzerda oching:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   (`<TOKEN>` o'rniga haqiqiy tokenni qo'ying) — javobda `"chat":{"id":-100...` qatorini toping, shu raqam `GROUP_CHAT_ID`

## 3. Mahalliy ishga tushirish (sinov uchun)

```bash
cd kadr-studio-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env faylini oching va BOT_TOKEN, GROUP_CHAT_ID, CARD_NUMBER, CARD_HOLDER, STUDIO_ADDRESS ni to'ldiring
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
6. **Environment** bo'limida quyidagilarni qo'shing (`.env.example` dagi kabi):
   - `BOT_TOKEN`
   - `GROUP_CHAT_ID`
   - `CARD_NUMBER`
   - `CARD_HOLDER`
   - `DEPOSIT_AMOUNT` (ixtiyoriy, standart 100000)
   - `STUDIO_ADDRESS`
   - `MANAGER_USERNAME`
7. Deploy tugmasini bosing — bir necha daqiqada bot 24/7 ishlay boshlaydi

**Muhim:** bookings.db fayli Render'ning bepul tarifida qayta deploy qilinganda o'chib ketishi mumkin (disk doimiy emas). Agar bronlar tarixi doimiy saqlanishi kerak bo'lsa, keyinchalik Render'ning bepul PostgreSQL bazasiga o'tkazish kerak bo'ladi — hozircha oddiy hajm uchun SQLite yetarli.
