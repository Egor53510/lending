"""
Telegram Bot for Admin Notifications & Lead Management
Sends notifications and provides commands to view leads
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    user_id = str(update.effective_user.id)
    
    if user_id == TELEGRAM_ADMIN_ID:
        await update.message.reply_text(
            "🔔 <b>Бот управления заявками</b>\n\n"
            "Вы будете получать уведомления о новых заявках с лендинга.\n\n"
            "<b>Команды:</b>\n"
            "/start - Главное меню\n"
            "/leads - Все заявки\n"
            "/today - Заявки за сегодня\n"
            "/stats - Статистика\n"
            "/status - Статус бота\n"
            "/help - Помощь",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "⚠️ <b>Доступ запрещен</b>\n\n"
            "Этот бот предназначен только для администратора.",
            parse_mode='HTML'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    user_id = str(update.effective_user.id)
    
    if user_id != TELEGRAM_ADMIN_ID:
        return
    
    await update.message.reply_text(
        "❓ <b>Справка по командам</b>\n\n"
        "/start - Главное меню\n"
        "/leads - Показать все заявки (последние 20)\n"
        "/today - Заявки за сегодня\n"
        "/stats - Общая статистика\n"
        "/status - Проверка статуса бота\n"
        "/help - Эта справка\n\n"
        "<b>Автоматические уведомления:</b>\n"
        "• Новые заявки приходят мгновенно\n"
        "• Содержат все данные клиента\n"
        "• Можно отвечать напрямую в Telegram",
        parse_mode='HTML'
    )

async def get_leads_from_api(today_only=False):
    """Fetch leads from backend API"""
    try:
        async with httpx.AsyncClient() as client:
            if today_only:
                # Get all and filter by date
                response = await client.get(f"{BACKEND_URL}/api/leads?limit=100", timeout=10.0)
                if response.status_code == 200:
                    leads = response.json()
                    today = datetime.now().strftime("%Y-%m-%d")
                    return [l for l in leads if l['created_at'].startswith(today)]
                return []
            else:
                response = await client.get(f"{BACKEND_URL}/api/leads?limit=20", timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return []
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        return None

async def get_stats_from_api():
    """Fetch statistics from backend API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/api/stats", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return None

def format_lead_message(leads, title):
    """Format leads list for Telegram"""
    if not leads:
        return f"📭 <b>{title}</b>\n\nНет заявок"
    
    style_emojis = {
        "pop": "🎵", "rock": "🎸", "jazz": "🎺", "classical": "🎹",
        "electronic": "🎧", "hip-hop": "🎤", "ambient": "🌙", "cinematic": "🎬"
    }
    
    message = f"📋 <b>{title}</b> ({len(leads)} шт.)\n\n"
    
    for i, lead in enumerate(leads[:10], 1):  # Show max 10
        style = lead.get('style', 'unknown')
        emoji = style_emojis.get(style, '🎵')
        status = lead.get('status', 'new')
        status_emoji = {'new': '🟡', 'contacted': '🟠', 'converted': '🟢'}.get(status, '⚪')
        
        created = lead.get('created_at', '')
        if created:
            try:
                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                time_str = dt.strftime("%d.%m %H:%M")
            except:
                time_str = created[:16]
        else:
            time_str = "-"
        
        message += (
            f"{i}. <b>#{lead['id']}</b> {status_emoji}\n"
            f"   👤 {lead['name']}\n"
            f"   📱 {lead.get('phone', '-')}\n"
            f"   {emoji} {style.title()}\n"
            f"   📝 {time_str}\n\n"
        )
    
    if len(leads) > 10:
        message += f"... и еще {len(leads) - 10} заявок\n"
    
    message += f"\n🔗 <a href='http://localhost:8000/admin'>Открыть панель админа</a>"
    
    return message

async def leads_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all leads"""
    user_id = str(update.effective_user.id)
    if user_id != TELEGRAM_ADMIN_ID:
        return
    
    await update.message.reply_text("⏳ Загружаю заявки...")
    
    leads = await get_leads_from_api()
    if leads is None:
        await update.message.reply_text("❌ Ошибка соединения с сервером")
        return
    
    message = format_lead_message(leads, "Все заявки")
    await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's leads"""
    user_id = str(update.effective_user.id)
    if user_id != TELEGRAM_ADMIN_ID:
        return
    
    await update.message.reply_text("⏳ Загружаю заявки за сегодня...")
    
    leads = await get_leads_from_api(today_only=True)
    if leads is None:
        await update.message.reply_text("❌ Ошибка соединения с сервером")
        return
    
    today_str = datetime.now().strftime("%d.%m.%Y")
    message = format_lead_message(leads, f"Заявки за {today_str}")
    await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics"""
    user_id = str(update.effective_user.id)
    if user_id != TELEGRAM_ADMIN_ID:
        return
    
    await update.message.reply_text("⏳ Загружаю статистику...")
    
    stats = await get_stats_from_api()
    if stats is None:
        await update.message.reply_text("❌ Ошибка соединения с сервером")
        return
    
    message = (
        "📊 <b>Статистика лендинга</b>\n\n"
        f"📋 Всего заявок: <b>{stats.get('total_leads', 0)}</b>\n"
        f"🟡 Новых: <b>{stats.get('new_leads', 0)}</b>\n"
        f"📅 Сегодня: <b>{stats.get('today_leads', 0)}</b>\n"
        f"🎵 Треков создано: <b>{stats.get('total_tracks', 0)}</b>\n\n"
        f"🔗 <a href='http://localhost:8000/admin'>Панель администратора</a>"
    )
    await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status"""
    user_id = str(update.effective_user.id)
    
    if user_id != TELEGRAM_ADMIN_ID:
        return
    
    await update.message.reply_text(
        "📊 <b>Статус бота</b>\n\n"
        "🟢 Бот активен\n"
        f"👤 Admin ID: {TELEGRAM_ADMIN_ID}\n"
        f"🔑 Token: {'Установлен' if TELEGRAM_BOT_TOKEN else 'Не установлен'}\n\n"
        "Бот готов к получению уведомлений о заявках.",
        parse_mode='HTML'
    )

def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    if not TELEGRAM_ADMIN_ID:
        logger.error("TELEGRAM_ADMIN_ID not set!")
        return
    
    logger.info("Starting admin bot...")
    logger.info(f"Backend URL: {BACKEND_URL}")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("leads", leads_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Start bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
