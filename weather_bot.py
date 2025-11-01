import os

from dotenv import load_dotenv
from flask import Flask, abort, request
import requests
import telebot


# === Настройки ===
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://your-bot.onrender.com

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Flask-приложение (Render требует WSGI-приложение)
app = Flask(__name__)


# Установка webhook при запуске
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    response = requests.post(url, json={"url": f"{WEBHOOK_URL}/webhook"})
    return f"Webhook set: {response.json()}"


# Endpoint для Telegram
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ""
    else:
        abort(403)


# Обработчики бота
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message, "Привет! Напиши название города — и я скажу погоду 🌤️")


@bot.message_handler(func=lambda message: True)
def get_weather(message):
    city = message.text.strip()
    if not city:
        bot.reply_to(message, "Пожалуйста, введи название города.")
        return

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric", "lang": "ru"}

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"].capitalize()
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            answer = (
                f"🌤 Погода в {city}:\n"
                f"Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                f"Описание: {desc}\n"
                f"Влажность: {humidity}%\n"
                f"Ветер: {wind} м/с"
            )
            bot.reply_to(message, answer)
        else:
            bot.reply_to(message, "Город не найден. Проверь написание.")
    except Exception:
        bot.reply_to(message, "Ошибка при получении погоды. Попробуй позже.")


# Точка входа для Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 443))
    app.run(host="0.0.0.0", port=port)
