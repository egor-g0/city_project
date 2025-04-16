import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import random
import sqlite3

TOKEN = 'vk1.a.L3pFBJjGZSPzMMc2xcuLSoeaeMuMAj4HH0rVEtTlpelLP4CzxyPKT5upGcEFuxHx1hPYxRu3ETD2TWrihX9yvtCFNI7N2gRQw4KdmOvO1sKjNkPUiwZM1iH3FlrG7lr0mOqI_EQ_MnPJ0fMz2AbMraOrOaYAB2honTf4hR8ilMfiphgNBw3LaFFXOKivAtwfdpPwIWCVL2g6YHM3BOGzLA'

vk = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk)

# Для хранения текущих игр
games = {}

def get_city_starting_with(letter, used_cities):
    con = sqlite3.connect("cities.db")
    cur = con.cursor()
    result = cur.execute(f"""SELECT city FROM cities
                WHERE city LIKE '{letter}%'""").fetchall()
    s = [i[0] for i in result]
    con.close()
    if s:
        for j in s:
            if j not in used_cities:
                return j
    return None

def get_last_valid_letter(city_name):
    last_char = city_name[-1]
    if last_char in ['ь', 'ъ', 'ы']:
        return get_last_valid_letter(city_name[:-1])
    return last_char

def send_message(chat_id, text):
    random_id = random.randint(0, 10 ^ 4)
    vk.method('messages.send', {'chat_id': chat_id, 'message': text, 'random_id': random_id})

def get_bot_first_city():
    con = sqlite3.connect("cities.db")
    cur = con.cursor()
    result = cur.execute(f"""SELECT city FROM cities
                    WHERE id LIKE ?""", (random.randrange(1, 1000), )).fetchall()
    s = [i[0] for i in result]
    con.close()
    return s[0]

def city_check(city, last_city):
    if get_last_valid_letter(last_city) != city[0]:
        return "Город начинается не с той буквы, поробуйте другой! Чтобы сдаться, напишите 'сдаюсь'."
    con = sqlite3.connect("cities.db")
    cur = con.cursor()
    result = cur.execute(f"""SELECT city FROM cities
                WHERE city LIKE '{city}'""").fetchall()
    s = [i[0] for i in result]
    if not s:
        return "Я не знаю такого города. Попробуйте другой."
    if city in games[chat_id]['used']:
        return "Этот город уже был назван. Попробуйте другой."
    return "OK"

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        msg = event.text
        chat_id = event.chat_id
        text = msg.lower()
        print(text)

        """Собеседник неизвестен, выводится после его первого сообщения-приветствия"""
        if chat_id not in games.keys():
            print('hell')
            games[chat_id] = {
                'used': set(),
                'last_city': None
            }
            send_message(chat_id, "Привет! Напишите 'начать игру', чтобы сыграть в города.")

        """Собеседник известен и начинает игру, запись данных в словарь"""
        if text == 'начать игру':

            bot_city = get_bot_first_city()
            games[chat_id]['used'].add(bot_city)
            games[chat_id]['last_city'] = bot_city
            """Бот начинает игру и пишет свой город"""
            send_message(chat_id,
                         f"Начинаем игру! Мой город: {bot_city.capitalize()}. Ваш ход! Чтобы сдаться, напишите 'сдаюсь'")
        elif not chat_id:
            """Собеседник хочет сдаться, завершение игры"""
            if text == 'сдаюсь':
                print('flag3')
                send_message(chat_id, "Игра окончена. Чтобы начать заново, напишите 'начать игру'")
                del games[chat_id]
            else:
                print('flag1')
                last_city = games[chat_id]['last_city']
                status = city_check(text, last_city)
                print('flag2')
                if status == "OK":
                    """Город подходит под условия, ход бота"""
                    games[chat_id]['used'].add(text)
                    last_letter = get_last_valid_letter(text)

                    bot_city = get_city_starting_with(last_letter, games[chat_id]['used'])
                    if bot_city:
                        games[chat_id]['used'].add(bot_city)
                        games[chat_id]['last_city'] = bot_city
                        """Бот отвечает своим городом"""
                        send_message(chat_id, f"Мой город: {bot_city.capitalize()}. Ваш ход!")
                    else:
                        """Город не найден, победил собеседник, завершение игры"""
                        send_message(chat_id, "Я не могу найти подходящий город. Вы победили!")
                        del games[chat_id]
                else:
                    """Возникла ошибка, город по какой-то причине не подходит"""
                    send_message(chat_id, status)
