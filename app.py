from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timezone, timedelta

# ---------------- CONFIG ----------------
BOT_TOKEN = "8720706918:AAGGK98jFTGuiA7I9LoQgmuWM-SuqG09vgk"
GROUP_ID = -1003741489182
CHANNEL_ID = -1003815641639

# ---------------- MEMORY ----------------
active_trades = {}

# ---------------- TIME ----------------
def get_time():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")

# ---------------- NAME ----------------
def get_name(user):
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

# ---------------- FORMAT TP ----------------
def format_tp(tp_list):
    return " | ".join(str(int(x)) if x.is_integer() else str(x) for x in tp_list)

# ---------------- PREMIUM EMOJI ----------------
def e(emoji_id, fallback):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# ---------------- SIGNAL ----------------
async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if len(args) != 3:
        await update.message.reply_text("Usage: /signal ENTRY TP1-TP2-TP3 SL")
        return

    entry = float(args[0])
    tp = [float(x) for x in args[1].split("-")]
    sl = float(args[2])

    trade_type = "BUY" if entry > sl else "SELL"

    emoji = e("5449683594425410231", "🔼") if trade_type == "BUY" else e("5447183459602669338", "🔽")
    lightning = e("5456140674028019486", "⚡")
    money = e("5409048419211682843", "💵")
    warning = e("5420323339723881652", "⚠️")
    clock = e("5445010743021818722", "🕐")
    by = e("5388566643595031142", "👤")
    buysell = e("5429651785352501917", "↗️") if trade_type == "BUY" else e("5429518319243775957", "📉")
    alert = e("5395695537687123235", "🚨")
    name = get_name(update.effective_user)

    text = f"""
{buysell}        <b>{trade_type} XAUUSD</b>       {alert}
━━━━━━━━━━━━━
{lightning} Entry : <code>{entry}</code>
{money} TP : <code>{format_tp(tp)}</code>
{warning} SL : <code>{sl}</code>
━━━━━━━━━━━━━
{clock} Time: {get_time()}
{by} By: {name}

{emoji}{emoji}{emoji}{emoji}{emoji}{emoji}{emoji}{emoji}{emoji}
"""

    # 1️⃣ SEND TO GROUP
    group_msg = await context.bot.send_message(
        chat_id=GROUP_ID,
        text=text,
        parse_mode="HTML"
    )

    # 2️⃣ FORWARD TO CHANNEL
    channel_msg = await context.bot.forward_message(
        chat_id=CHANNEL_ID,
        from_chat_id=GROUP_ID,
        message_id=group_msg.message_id
    )

    # store mapping (important for cancel)
    active_trades[group_msg.message_id] = {
        "channel_msg_id": channel_msg.message_id
    }

# ---------------- CANCEL ----------------
async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to signal message to cancel.")
        return

    replied_id = update.message.reply_to_message.message_id

    if replied_id not in active_trades:
        await update.message.reply_text("Signal not found.")
        return

    cancel_text = f"""
{e("5210952531676504517","❌")} <b>SIGNAL CANCELLED</b>
"""

    # send reply in group
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=cancel_text,
        parse_mode="HTML",
        reply_to_message_id=replied_id
    )

    # send reply in channel to forwarded signal
    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=cancel_text,
        parse_mode="HTML",
        reply_to_message_id=active_trades[replied_id]["channel_msg_id"]
    )

    del active_trades[replied_id]

# ---------------- START BOT ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

app.post_init = post_init

app.add_handler(CommandHandler("signal", signal_cmd))
app.add_handler(CommandHandler("cancel", cancel_cmd))

print("Bot running...")
app.run_polling(drop_pending_updates=True)