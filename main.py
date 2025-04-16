import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import random

TOKEN = 'vk1.a.L3pFBJjGZSPzMMc2xcuLSoeaeMuMAj4HH0rVEtTlpelLP4CzxyPKT5upGcEFuxHx1hPYxRu3ETD2TWrihX9yvtCFNI7N2gRQw4KdmOvO1sKjNkPUiwZM1iH3FlrG7lr0mOqI_EQ_MnPJ0fMz2AbMraOrOaYAB2honTf4hR8ilMfiphgNBw3LaFFXOKivAtwfdpPwIWCVL2g6YHM3BOGzLA'

vk = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk)

with open('cities.txt', 'r', encoding='utf-8') as f:
    cities = [line.strip().lower() for line in f]

# Для хранения текущих игр
games = {}


def get_city_starting_with(letter, used_cities):
    """Находит город, начинающийся на заданную букву"""
    available = [city for city in cities
                 if city.startswith(letter) and city not in used_cities]
    if available:
        return random.choice(available)
    return None


def get_last_valid_letter(city_name):
    """Получаем последнюю букву, исключая мягкий/твердый знак"""
    last_char = city_name[-1]
    if last_char in ['ь', 'ъ', 'ы']:
        return get_last_valid_letter(city_name[:-1])
    return last_char


def send_message(chat_id, text):
    random_id = random.randint(0, 10 ^ 6)
    vk.method('messages.send', {'chat_id': chat_id, 'message': text, 'random_id': random_id})


# Основной цикл бота
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        msg = event.text
        chat_id = event.chat_id
        text = msg.lower()

        if text == 'начать игру':
            games[chat_id] = {
                'used': set(),
                'last_city': None
            }
            # Бот делает первый ход
            bot_city = random.choice(cities)
            games[chat_id]['used'].add(bot_city)
            games[chat_id]['last_city'] = bot_city
            send_message(chat_id, f"Начинаем игру! Мой город: {bot_city.capitalize()}. Ваш ход!")
            print(text, bot_city)

        elif chat_id in games.keys():
            # Продолжаем игру
            if text == 'сдаюсь':
                send_message(chat_id, "Игра окончена. Чтобы начать заново, напишите 'начать игру'")
                del games[chat_id]

            elif text in games[chat_id]['used']:
                send_message(chat_id, "Этот город уже был назван. Попробуйте другой.")

            elif text not in cities:
                send_message(chat_id, "Я не знаю такого города. Попробуйте другой.")

            else:
                last_city = games[chat_id]['last_city']
                if last_city:
                    required_letter = get_last_valid_letter(last_city)
                    if not text.startswith(required_letter):
                        send_message(chat_id,
                                     f"Город должен начинаться на букву '{required_letter}'. Попробуйте еще раз.")
                        continue

                # Город подходит
                games[chat_id]['used'].add(text)
                last_letter = get_last_valid_letter(text)

                # Ход бота
                bot_city = get_city_starting_with(last_letter, games[chat_id]['used'])
                if bot_city:
                    games[chat_id]['used'].add(bot_city)
                    games[chat_id]['last_city'] = bot_city
                    send_message(chat_id, f"Мой город: {bot_city.capitalize()}. Ваш ход!")
                else:
                    send_message(chat_id, "Я не могу найти подходящий город. Вы победили!")
                    del games[chat_id]

        else:
            send_message(chat_id, "Привет! Напишите 'начать игру', чтобы сыграть в города.")
