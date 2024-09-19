import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler

# Токен вашего Telegram-бота
TOKEN = '7452348287:AAGkCtCsLpp4_p4-YPS92BHTqVIMsruTjDQ'

# ID Telegram-чата (группы), куда будут отправляться сообщения
CHAT_ID = -1002273788611  # например, -1001234567890

bot = Bot(token=TOKEN)

# URL для парсинга
URL = 'https://www.avito.ru/moskva/kvartiry/sdam/na_dlitelnyy_srok'

# Заголовки для имитации браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# Хранение отправленных объявлений
sent_ads = set()

async def parse_ads():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Поиск всех объявлений на странице
    ads = soup.find_all('div', {'data-marker': 'item'})

    for ad in ads:
        # Получение ссылки на объявление
        link_tag = ad.find('a', {'data-marker': 'item-title'})
        if not link_tag:
            continue
        link = 'https://www.avito.ru' + link_tag.get('href')

        # Проверка, отправляли ли мы уже это объявление
        if link in sent_ads:
            continue

        # Получение цены
        price_tag = ad.find('meta', itemprop='price')
        if price_tag:
            price = int(price_tag.get('content'))
        else:
            continue

        # Проверка ценового диапазона
        if price < 35000 or price > 60000:
            print(f"Объявление не прошло проверку по цене: {price}")
            continue

        # Получение заголовка
        title = link_tag.get_text(strip=True)
        print(f"Заголовок объявления: {title}")

        # Расширенная проверка количества комнат
        if '2-к' not in title.lower() and '2 комнат' not in title.lower() and 'двухкомнат' not in title.lower():
            print(f"Объявление не прошло проверку по количеству комнат: {title}")
            continue

        # Получение описания
        description_tag = ad.find('div', {'data-marker': 'item-description'})
        description = description_tag.get_text(strip=True) if description_tag else ''

        # Расширенная проверка возможности проживания с животными
        if 'животные' not in description.lower() and 'с животными' not in description.lower() and 'можно с животными' not in description.lower():
            print(f"Объявление не прошло проверку по возможности проживания с животными: {description}")
            continue

        # Исключение некоторых объявлений по ключевым фразам
        excluded_phrases = ['животных', 'без животных', 'нет животных']
        if any(phrase in description.lower() for phrase in excluded_phrases):
            print(f"Объявление не прошло проверку по исключающим фразам: {description}")
            continue

        # Отправка ссылки в Telegram
        await bot.send_message(chat_id=CHAT_ID, text=link)

        # Добавление объявления в отправленные
        sent_ads.add(link)
        print(f"Объявление отправлено: {link}")

async def start(update: Update, context):
    # Проверка, что команда /start адресована этому боту
    if update.message.text.startswith(f"/start@{context.bot.username}") or update.message.chat_id == CHAT_ID:
        await update.message.reply_text('Бот запущен и готов к поиску от 35 до 60к!')

async def main():
    # Создание приложения с использованием ApplicationBuilder
    application = ApplicationBuilder().token(TOKEN).build()

    # Добавление обработчика команды /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Сообщение о старте бота
    try:
        await bot.send_message(chat_id=CHAT_ID, text='Бот запущен и готов к поиску от 35 до 600 000к!')
    except Exception as e:
        print(f'Ошибка при отправке сообщения о старте: {e}')

    # Запуск задачи парсинга объявлений
    asyncio.create_task(parse_ads())

    # Запуск бота
    await application.start()
    await application.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
