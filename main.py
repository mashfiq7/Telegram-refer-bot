import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8997974401:AAFQglruowt5WvyxKPSL_kOADhtygUOxsc8"
ADMIN_USERNAME = "Ownermusfiq"

CHANNELS = [
    {"name": "Funny Video MS", "url": "https://t.me/funnyvideoms"},
    {"name": "Income MS 9", "url": "https://t.me/incomems9"},
    {"name": "Payment Prop MS", "url": "https://t.me/paymentpropms"},
    {"name": "Referring Musfiq", "url": "https://t.me/referringmusfiq"},
    {"name": "XM Trader Community", "url": "https://t.me/xmtradercommunity"},
]

PER_REF = 0.05
MIN_WITHDRAW = 0.30

conn = sqlite3.connect('refer.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, referred_by INTEGER, balance REAL DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS withdraw (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, amount REAL, method TEXT, address TEXT, status TEXT DEFAULT 'Pending')''')
conn.commit()

def get_user(user_id):
    c.execute("SELECT referred_by, balance FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()

def get_refer_count(user_id):
    c.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
    return c.fetchone()[0]

async def check_join(user_id, context):
    for ch in CHANNELS:
        channel_username = ch["url"].split("/")[-1]
        try:
            member = await context.bot.get_chat_member(chat_id="@" + channel_username, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

async def send_join(update, context):
    keyboard = [[InlineKeyboardButton(f"✅ JOIN {ch['name']}", url=ch["url"])] for ch in CHANNELS]
    keyboard.append([InlineKeyboardButton("🎁 Joined All", callback_data="check_join")])
    await update.message.reply_text("⚠️ BOT USE KORTE AGE SOB CHANNEL JOIN KORO ⚠️", reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    if context.args:
        ref_id = int(context.args[0])
        if ref_id!= user_id:
            c.execute("INSERT OR IGNORE INTO users (user_id, username, referred_by) VALUES (?,?,?)", (user_id, username, ref_id))
            conn.commit()
            c.execute("UPDATE users SET balance = balance +? WHERE user_id=?", (PER_REF, ref_id))
            conn.commit()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (user_id, username))
    conn.commit()
    if not await check_join(user_id, context):
        await send_join(update, context)
        return
    await main_menu(update)

async def main_menu(update):
    keyboard = [[KeyboardButton("🧑‍🤝‍🧑 Refer & Earn"), KeyboardButton("💸 Balance")],[KeyboardButton("🎉 Withdraw🎉"), KeyboardButton("👤 My Details")]]
    text = "👋 Welcome to Refer Bot\nEarn $0.05 for each referral\nNicher button theke choose koro 👇"
    if update.message: await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    else: await update.callback_query.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    link = f"https://t.me/{context.bot.username}?start={user_id}"
    data = get_user(user_id)
    balance = data[1] if data else 0
    refer_count = get_refer_count(user_id)

    if text == "🧑‍🤝‍🧑 Refer & Earn":
        await update.message.reply_text(f"✅ Fake referrals are allowed. If you do, you will be banned.\n\nYour refer link 🖇️\n`{link}`\n\nYou will get $0.05 per referral😍", parse_mode="Markdown")
    elif text == "💸 Balance":
        await update.message.reply_text(f"💰 Your total refer: {refer_count}\n\nRefer $0.05 $\nTotal Balance: ${balance:.2f} $\n\nShare with your friends to earn more 🤩💸\n\nYou will get $0.05 per referral😍")
    elif text == "🎉 Withdraw":
        if balance < MIN_WITHDRAW:
            await update.message.reply_text(f"❌ Minimum withdrawal is ${MIN_WITHDRAW}\n♐Your balance: ${balance:.2f}")
            return
        keyboard = [[InlineKeyboardButton("1: BEP20 Address", callback_data="wd_bep20")],[InlineKeyboardButton("2: Bikash", callback_data="wd_bkash")]]
        await update.message.reply_text(f"🔸Minimum withdrawal is ${MIN_WITHDRAW}👇\n♐Your balance: ${balance:.2f}\n\n🔸Select how you want to withdraw 👇", reply_markup=InlineKeyboardMarkup(keyboard))
    elif text == "👤 My Details":
        await update.message.reply_text(f"👤 MY DETAILS 👤\n\n🆔 User ID: `{user_id}`\n👤 Username: @{update.effective_user.username}\n👥 Total Refer: {refer_count}\n💰 Current Balance: ${balance:.2f}\n🔗 Your Link: `{link}`", parse_mode="Markdown")

async def withdraw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['wd_method'] = query.data
    await query.message.reply_text("✅ Tomar BEP20 Address / Bikash Number pathao:")

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'wd_method' in context.user_data:
        user_id = update.effective_user.id
        username = update.effective_user.username
        address = update.message.text
        method = "BEP20" if context.user_data['wd_method']=="wd_bep20" else "Bikash"
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        amount = c.fetchone()[0]
        c.execute("INSERT INTO withdraw (user_id, username, amount, method, address) VALUES (?,?,?,?,?)", (user_id, username, amount, method, address))
        c.execute("UPDATE users SET balance=0 WHERE user_id=?", (user_id,))
        conn.commit()
        await update.message.reply_text(f"✅ Withdraw request submitted!\nAmount: ${amount:.2f}\nMethod: {method}\nStatus: Pending")
        admin_msg = f"🔔 NEW WITHDRAW REQUEST\n👤 User: @{username}\n🆔 ID: `{user_id}`\n💰 Amount: ${amount:.2f}\n💳 Method: {method}\n📍 Address: `{address}`"
        await context.bot.send_message(chat_id=ADMIN_USERNAME, text=admin_msg, parse_mode="Markdown")
        del context.user_data['wd_method']

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username!= ADMIN_USERNAME: return
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM withdraw WHERE status='Pending'")
    pending_wd = c.fetchone()[0]
    keyboard = [[InlineKeyboardButton("👥 Total Users", callback_data="admin_users")],[InlineKeyboardButton("💸 Pending Withdraw", callback_data="admin_wd")]]
    await update.message.reply_text(f"⚡ ADMIN PANEL ⚡\n\n👥 Total Users: {total_users}\n⏳ Pending WD: {pending_wd}", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.username!= ADMIN_USERNAME: return
    if query.data == "admin_users":
        c.execute("SELECT COUNT(*) FROM users")
        total = c.fetchone()[0]
        await query.edit_message_text(f"👥 Total Users: {total}")
    elif query.data == "admin_wd":
        c.execute("SELECT * FROM withdraw WHERE status='Pending' LIMIT 10")
        rows = c.fetchall()
        if not rows: return await query.edit_message_text("✅ No pending withdraw")
        for row in rows:
            wid, uid, uname, amt, method, addr, status = row
            keyboard = [[InlineKeyboardButton("✅ Paid", callback_data=f"paid_{wid}")],[InlineKeyboardButton("❌ Reject", callback_data=f"reject_{wid}")]]
            await context.bot.send_message(chat_id=ADMIN_USERNAME, text=f"WD ID: {wid}\nUser: @{uname}\nID: `{uid}`\nAmount: ${amt}\nMethod: {method}\nAddress: `{addr}`", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif query.data.startswith("paid_"):
        wid = query.data.split("_")[1]
        c.execute("UPDATE withdraw SET status='Paid' WHERE id=?", (wid,))
        conn.commit()
        await query.edit_message_text("✅ Marked as Paid")
    elif query.data.startswith("reject_"):
        wid = query.data.split("_")[1]
        c.execute("SELECT user_id, amount FROM withdraw WHERE id=?", (wid,))
        uid, amt = c.fetchone()
        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))
        c.execute("UPDATE withdraw SET status='Rejected' WHERE id=?", (wid,))
        conn.commit()
        await query.edit_message_text("❌ Rejected & Balance Returned")

async def check_join_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_join(query.from_user.id, context): await main_menu(query)
    else: await query.answer("❌ Age sob channel join koro!", show_alert=True)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(check_join_btn, pattern="check_join"))
app.add_handler(CallbackQueryHandler(withdraw_handler, pattern="wd_"))
app.add_handler(CallbackQueryHandler(admin_buttons, pattern="admin_"))
app.add_handler(CallbackQueryHandler(admin_buttons, pattern="paid_"))
app.add_handler(CallbackQueryHandler(admin_buttons, pattern="reject_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.CO in MMAND, buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_address))

print("Bot Running...")
app.run_polling()