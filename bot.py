import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import random
import sqlite3
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "VK Bot is alive!"

TOKEN = 'vk1.a.9AXQK0ZpxDPIppSw06M8VU5hC4uR3a8f1Q3mGvavHnlPfimEBewWV2-NPC9oyID3v1bRrMcLzVeA-6QSZoBFBBL7-ijtAIwAf3KiqV6krIuOvLxiIRLjdtn5v8bsYdK9vMmWxZVblUBh_fLXbMUfNjeS21cNex_uq72nTw_cEUnI2WCbPgHziUKM4carSh-4HphVN0s2uckkdJpjVJYPVg'

vk = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk)

games = {}

def get_city_starting_with(letter, used_cities):
    con = sqlite3.connect("cities.db")
    cur = con.cursor()
    result = cur.execute(f"""SELECT city FROM cities
                WHERE city LIKE '{letter}%'""").fetchall()
    s = [i[0] for i in result]
    random.shuffle(s)
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

def get_bot_first_city():
    con = sqlite3.connect("cities.db")
    cur = con.cursor()
    result = cur.execute(f"""SELECT city FROM cities
                    WHERE id LIKE ?""", (random.randrange(1, 1000),)).fetchall()
    s = [i[0] for i in result]
    con.close()
    return s[0]

def city_check(city, last_city, chat_id):
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
def send_messages(chat_id, text):
    random_id = random.randint(0, 10000)
    vk.method('messages.send', {'chat_id': chat_id, 'message': text, 'random_id': random_id})
def run_bot():
    flag = False
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                if event.from_chat:
                    msg = event.text.lower()
                    chat_id = event.chat_id
                    user_id = event.user_id
                    user_info = vk.method('users.get', {
                        'user_ids': user_id,
                        'fields': 'screen_name'
                    })[0]
                    first_name = user_info['first_name']
                    last_name = user_info['last_name']
                    username = f"@{user_info['screen_name']}" if 'screen_name' in user_info else ""
                    if chat_id not in games.keys():
                        games[chat_id] = {
                        'used': set(),
                        'last_city': None,
                        'counter': 0
                        }
                        send_messages(chat_id, f"Здравствуйте, {first_name}! Напишите 'Начать игру', чтобы сыграть в города. "
                                               f"Города - простая игра. Я вам называю город, а вы должны назвать другой город, который начинается с последней буквы моего города. "
                                               f"Буквы ь, ы, ъ не считаются. Удачной игры :)")
                    else:
                        if not flag:
                            if msg == 'начать игру':
                                a = get_bot_first_city()
                                games[chat_id]['used'].add(a)
                                games[chat_id]['last_city'] = a
                                send_messages(chat_id, f"Начинаем! Мой город - {a.capitalize()}, вам на {get_last_valid_letter(a).capitalize()}. Чтобы сдаться, напишите 'сдаюсь'")
                                flag = True
                            else:
                                send_messages(chat_id, "Напишите 'Начать игру', чтобы сыграть в города.")
                        else:
                            if msg.lower() == 'сдаюсь':
                                send_messages(chat_id, f"Игра окончена. Ваш счёт: {games[chat_id]['counter']}")
                                del games[chat_id]
                                flag = False
                            else:
                                last_city = games[chat_id]['last_city']
                                status = city_check(msg, last_city, chat_id)
                                if status == "OK":
                                    """Город подходит под условия, ход бота"""
                                    games[chat_id]['used'].add(msg)
                                    games[chat_id]['counter'] += 1
                                    last_letter = get_last_valid_letter(msg)

                                    bot_city = get_city_starting_with(last_letter, games[chat_id]['used'])
                                    if bot_city:
                                        games[chat_id]['used'].add(bot_city)
                                        games[chat_id]['last_city'] = bot_city
                                        """Бот отвечает своим городом"""
                                        send_messages(chat_id, f"Мой город: {bot_city.capitalize()}. Ваш ход!")
                                    else:
                                        """Город не найден, победил собеседник, завершение игры"""
                                        send_messages(chat_id, "Я не могу найти подходящий город. Вы победили!")
                                        del games[chat_id]
                                        flag = False
                                else:
                                    """Возникла ошибка, город по какой-то причине не подходит"""
                                    send_messages(chat_id, status)


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=3000)