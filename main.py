import threading
from datetime import datetime
import telebot
import sqlite3
import time
import schedule
import logging
from config import TOKEN, MASTER1, MASTER2, HEAD_OF_DEP
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)


# Открытие курсора подключение к Базе Данных.
def get_db_connection():
    connection = sqlite3.connect('base2.db')
    cursor = connection.cursor()
    return connection, cursor


# Информация новым пользователям.
@bot.message_handler(commands=['start'])
def info_message(message):
    bot.send_message(message.chat.id,
                     f""" 🎉 Добро пожаловать 🎉\n🔧На Участок сборки🔧\nПеред регистрацией необходимо ознакомиться с правилами работы на участке.""")
    bot.send_message(message.chat.id,
                     f""" ⏰ Не опаздывайте на работу! В нашей компании установлена Система контроля управления доступом (СКУД).Планируйте свой маршрут заранее, чтобы приходить на работу вовремя, согласно вашему рабочему графику. """)
    bot.send_message(message.chat.id,
                     f""" 💊 Если вы плохо себя чувствуете, обязательно предупредите Мастера участка о том, что заболели и идёте к врачу. 📋 После открытия больничного листа отправьте в Telegram сообщение Начальнику участка и Мастеру вашей смены следующего содержания: Больничный лист № 12345 Открыт с 10.12.2024 по 20.12.2024 ✅ После закрытия больничного листа также необходимо сообщить Мастеру и Начальнику участка о том, что вы готовы выйти на работу. """.strip())
    bot.send_message(message.chat.id,
                     f""" 📵 В цеху запрещено использование мобильных телефонов. Поэтому перед раздевалкой установлены специальные номерные шкафчики 🔐 в которых необходимо оставить свой телефон 📱 перед проходом через пункт охраны. ✅ """)
    bot.send_message(message.chat.id,
                     f""" 🔧 На производстве необходимо находиться в специальной антистатической одежде, обуви и головном уборе (кепка B4COM). 👖👞🧢""")
    bot.send_message(message.chat.id,
                     f"""🚫 В раздевалках запрещено есть, пить, курить вейпы.\n⏰ Провести время можно в уголках отдыха, которые расположены на входе в компанию.\n🥪 Покушать можно в нашей столовой, где есть микроволновки, холодильники 🧊 и кофемашина ☕.""")
    bot.send_message(message.chat.id, f"""📖 Если вы прочитали этот блок до конца, то переходите в раздел Регистрация, который находится слева в меню 👈.""")


# Раздел контакты.
@bot.message_handler(commands=['contacts'])
def contact_message(message):
    profile_name_had_of_department = HEAD_OF_DEP
    profile_name_master1 = MASTER1
    profile_name_master2 = MASTER2
    bot.send_message(message.chat.id,
                     f'Начальник участка: {profile_name_had_of_department}\nМастер смены: {profile_name_master1}\nМастер смены: {profile_name_master2}')


# Кнопки меню /help
@bot.message_handler(commands=['help'])
def help_function(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2)
    btn1 = telebot.types.KeyboardButton('Как взять неоплачиваемый отпуск?')
    btn2 = telebot.types.KeyboardButton('Как пойти в отпуск?')
    button_group = [btn1, btn2]
    for button_groups in button_group:
        keyboard.add(button_groups)

    bot.send_message(message.chat.id, f"🔍 Возможно, в этом меню вы найдёте ответ на свой вопрос!",
                     reply_markup=keyboard)


# Регистрация нового USER.
@bot.message_handler(commands=['registration'])
def registr_command(message):
    bot.send_message(message.chat.id, 'Введите ваше Имя и Фамилию согласно примеру:\n✅Имя Фамилия')
    bot.register_next_step_handler(message, process_name)


# Получаем имя пользователя.
def process_name(message):
    name = message.text.strip()
    connection, cursor = get_db_connection()

    try:
        # Проверяем, зарегистрирован ли пользователь.
        people_id = message.chat.id
        cursor.execute('''SELECT id FROM users WHERE id = ?''', (people_id,))
        data = cursor.fetchone()

        if data is None:
            # Если пользователь не найден, добавляем его в базу данных.
            cursor.execute('''INSERT INTO users (id, name) VALUES (?, ?)''',
                           (people_id, name))
            connection.commit()
            bot.send_message(message.chat.id, 'Регистрация завершена')
        else:
            bot.send_message(message.chat.id, 'Вы уже зарегистрированы')
    finally:
        connection.close()


# Посмотреть количество красных часов.
@bot.message_handler(commands=['showred'])
def showred(message):
    connection, cursor = get_db_connection()
    people_id = message.chat.id
    cursor.execute('''SELECT redh FROM users WHERE id = ?''', (people_id,))
    rows = cursor.fetchall()
    for row in rows:
        redh = row[0]
        if redh == 0:
            bot.send_message(message.chat.id, f'Отличная работа! 💪 У вас нет красных часов. 🆒')
        elif redh is not None:
            bot.send_message(message.chat.id,
                             f'У вас накопилось 🔴{redh}🔴 красных часа ⏳ и важно отработать их как можно скорее. Помните, что максимальное количество красных часов – 16. Если превысите этот лимит, то дальнейшие часы можно будет компенсировать только через оформление отпусков за свой счёт 📆🚫.')
        else:
            bot.send_message(message.chat.id, f'Отличная работа! 💪 У вас нет красных часов. 🆒')

        connection.close()


# Посмотреть количество зеленых часов.
@bot.message_handler(commands=['showgreen'])
def showgreen(message):
    connection, cursor = get_db_connection()
    people_id = message.chat.id
    cursor.execute('''SELECT greenh FROM users WHERE id = ?''', (people_id,))
    rows = cursor.fetchall()

    for row in rows:
        redh = row[0]
        if redh == 0:
            bot.send_message(message.chat.id,
                             f'У вас нет зелёных часов 😱 Но не беда! Вы можете легко их заработать, если придёте на помощь компании в случае производственной необходимости 💪✨')
        elif redh is not None:
            bot.send_message(message.chat.id,
                             f'Вы можете использовать 🟢{redh}🟢 зеленых часов в любое удобное для вас время.')
        else:
            bot.send_message(message.chat.id,
                             f'У вас нет зелёных часов 😱 Но не беда! Вы можете легко их заработать, если придёте на помощь компании в случае производственной необходимости 💪✨')

        connection.close()


#  Посмотреть график работы.
@bot.message_handler(commands=['workshift'])
def show_schedule(message):
    # print 1 смены.
    connection, cursor = get_db_connection()
    cursor.execute('SELECT name FROM users WHERE workingshift = 1')
    result1 = cursor.fetchall()
    connection.close()
    names1 = [name1[0] for name1 in result1]
    sum_names1 = len(names1)
    bot.send_message(message.chat.id, 'Ваш график работы на текущий месяц:')
    bot.send_message(message.chat.id,
                     f"Режим работы смены №1\n🕑 8:00 до 17:00 - Рабочее время\n🕑 9:45 до 10:00 - Перерыв\n🕑 12:00 до 13:00 - Обед\n🕑 14:45 до 15:00 - Перерыв  \n  Смена №1 | {sum_names1} чел\n {names1}")

    # print 2 смены.
    connection, cursor = get_db_connection()
    cursor.execute('SELECT name FROM users WHERE workingshift = 2')
    result2 = cursor.fetchall()
    connection.close()
    names2 = [name2[0] for name2 in result2]
    sum_names2 = len(names2)
    bot.send_message(message.chat.id,f"Режим работы смены №2\n🕑 13:00 до 22:00 - Рабочее время\n🕑 15:00 до 15:15 - Перерыв\n🕑 17:15 до 18:15 - Обед\n🕑 19:45 до 20:00 - Перерыв  \n  Смена №2 | {sum_names2} чел\n {names2}")


# Замена смен в Базе Данных с 1 на 2 или с 2 на 1 , если месяц (Чётный).
def auto_shift(date=datetime.today().date()):
    current_date = date.month
    connection, cursor = get_db_connection()
    if current_date % 2 == 0:
        cursor.execute('UPDATE users SET workingshift = CASE WHEN workingshift = 1 THEN 2 ELSE 1 END')
        connection.commit()
        connection.close()
        print("Четное")
    else:
        cursor.execute('UPDATE users SET workingshift = CASE WHEN workingshift = 2 THEN 1 ELSE 2 END')
        connection.commit()
        connection.close()
        print("Нечетное")


# Оповещение о смене графика.
def shift_message(date=datetime.today().day):
    if date == 27:
        connection, cursor = get_db_connection()
        cursor.execute('SELECT name FROM users WHERE workingshift == 1')
        select_result1 = cursor.fetchall()
        cursor.execute('SELECT name FROM users WHERE workingshift == 2')
        select_result2 = cursor.fetchall()
        connection.close()

        text_shift2 = [text_shift2[0] for text_shift2 in select_result1]  # Cмена номер 2
        text_shift1 = [text_shift1[0] for text_shift1 in select_result2]  # Cмена номер 1

        connection, cursor = get_db_connection()
        cursor.execute('SELECT id, name FROM users')
        select_result_id = cursor.fetchall()
        connection.close()

        for select_results in select_result_id:
            bot.send_message(select_results[0], 'Ваш график работы на следующий месяц:')
            bot.send_message(select_results[0], 'Смена №2\n' + '\n'.join(text_shift2))
            bot.send_message(select_results[0], 'Смена №1\n' + '\n'.join(text_shift1))


# Функция проверки штата.
@bot.message_handler(commands=['state'])
def state(message):
    connection, cursor = get_db_connection()
    cursor.execute('SELECT name, state FROM users')
    result_state = cursor.fetchall()
    connection.close()
    admin_count = sum('admin' in result_states for result_states in result_state)
    master = sum('master' in result_states for result_states in result_state)
    first_category_count = sum('category_1' in result_states for result_states in result_state)
    second_category_count = sum('category_2' in result_states for result_states in result_state)
    third_category_count = sum('category_3' in result_states for result_states in result_state)
    fourth_category_count = sum('category_4' in result_states for result_states in result_state)
    bot.send_message(message.chat.id, f'\u00A0\u00A0\u00A0🚹\u00A0\u00A0\u00A0  |     ❌     |       ✅\n'
                                      f'\u00A0Всего | Занято | Свободно\n'
                                      f'\u00A0\u00A0\u00A0\u00A063    |      {admin_count + master + first_category_count + second_category_count + third_category_count + fourth_category_count }     |      {63 - (first_category_count + second_category_count + third_category_count + fourth_category_count + admin_count + master)}\n'
                                      f'Начальник участка: {1} | {admin_count} | {1 - admin_count}\n'
                                      f'Мастер участка: {2} | {master} | {2 - master}\n'
                                      f'Слесарь сборщик 1️⃣к: {19} | {first_category_count} | {19 - first_category_count}\n'
                                      f'Слесарь сборщик 2️⃣к: {15} | {second_category_count} | {15 - second_category_count}\n'
                                      f'Слесарь сборщик 3️⃣к: {10} | {third_category_count} | {10 - third_category_count}\n'
                                      f'Слесарь сборщик 4️⃣к: {16} | {fourth_category_count} | {16 - fourth_category_count}')

    admin_list = []
    master_list = []
    category_4_list = []
    category_3_list = []
    category_2_list = []
    category_1_list = []
    for result_states in result_state:
        if 'admin' in result_states:
            admin_list.append(result_states[0])
        if 'master' in result_states:
            master_list.append(result_states[0])
        if 'category_4' in result_states:
            category_4_list.append(result_states[0])
        if 'category_3' in result_states:
            category_3_list.append(result_states[0])
        if 'category_2' in result_states:
            category_2_list.append(result_states[0])
        if 'category_1' in result_states:
            category_1_list.append(result_states[0])

    bot.send_message(message.chat.id, 'Начальник участка:' + '\n ' + '\n'.join(admin_list))
    bot.send_message(message.chat.id, 'Мастер участка:' + '\n' + '\n'.join(master_list))
    bot.send_message(message.chat.id, 'Слесарь сборщик 4️⃣к:' + '\n' + '\n'.join(category_4_list))
    bot.send_message(message.chat.id, 'Слесарь сборщик 3️⃣к:' + '\n' + '\n'.join(category_3_list))
    bot.send_message(message.chat.id, 'Слесарь сборщик 2️⃣к:' + '\n' + '\n'.join(category_2_list))
    bot.send_message(message.chat.id, 'Слесарь сборщик 1️⃣к:' + '\n' + '\n'.join(category_1_list))


# Обработчик кнопок меню /help
@bot.message_handler(func=lambda message: True)
def handle_text_message(message):
    if message.text == 'Как взять неоплачиваемый отпуск?':
        bot.reply_to(message,
                     f""" 📌 Инструкция: Как взять неоплачиваемый отпуск ❗ Обращаем ваше внимание, что отпуск без сохранения заработной платы подается за 3-4 дня до его начала. ⚠ Однако никто не отменял форс-мажорные ситуации. В случае их возникновения вам необходимо связаться с начальником участка и подать заявление до 12:00 текущего дня подачи заявления. ✉ Не забудьте указать причину отпуска в заявлении! """)

        bot.send_message(message.chat.id, 'Заходим в приложение 1С')
        bot.send_photo(message.chat.id, open('instructions_img/leave_of_absence/photo_1_leave_of_absence.jpg', 'rb'))
        bot.send_message(message.chat.id, 'Заходим в раздел Отпуск')
        bot.send_photo(message.chat.id, open('instructions_img/leave_of_absence/photo_2_leave_of_absence.jpg', 'rb'))
        bot.send_message(message.chat.id, 'Выбирае пункт меню Отпуск за свой счет')
        bot.send_photo(message.chat.id, open('instructions_img/leave_of_absence/photo_3_leave_of_absence.jpg', 'rb'))
        bot.send_message(message.chat.id, 'Указываем даты отпуска')
        bot.send_photo(message.chat.id, open('instructions_img/leave_of_absence/photo_4_leave_of_absence.jpg', 'rb'))
        bot.send_message(message.chat.id,
                         'ОБЯЗАТЕЛЬНО: Укажите комментарий и нажмите «Отправить на согласование».Примеры комментариев: «Посещение колледжа»|«По семейным обстоятельствам».')
        bot.send_photo(message.chat.id, open('instructions_img/leave_of_absence/photo_5_leave_of_absence.jpg', 'rb'))

    elif message.text == 'Как пойти в отпуск?':
        bot.reply_to(message,
                     f""" 📋 Инструкция: Как пойти в отпуск 👀 Обращаем ваше внимание, что отпуска распределяются в конце каждого года на следующий год. 💼 Ваш отпуск составляет 28 дней, которые можно разделить на две части по 14 дней. ✍️ Далее ваш план отпуска появится в соответствующем разделе черновиков. Как только это произойдет, необходимо отправить черновик на согласование. 🔄 Если же вы не планируете идти в отпуск в запланированное время, нужно оформить заявление на перенос отпуска минимум за 2 недели до его начала. """)
        bot.send_message(message.chat.id, 'Заходим в приложение 1С')
        bot.send_photo(message.chat.id, open('instructions_img/vacantion/photo_1_vacantion.jpg', 'rb'))
        bot.send_message(message.chat.id, 'Заходим в раздел Отпуск')
        bot.send_photo(message.chat.id, open('instructions_img/vacantion/photo_2_vacantion.jpg', 'rb'))
        bot.send_message(message.chat.id, 'Заходим в пункт меню Отпуск')
        bot.send_photo(message.chat.id, open('instructions_img/vacantion/photo_3_vacantion.jpg', 'rb'))
        bot.send_message(message.chat.id,
                         'На картинке изображён ваш график отпусков. Обратите внимание, что он может находиться в статусе черновика. Чтобы это проверить, необходимо открыть конкретный отпуск.')
        bot.send_photo(message.chat.id, open('instructions_img/vacantion/photo_4_vacantion.jpg', 'rb'))
        bot.send_message(message.chat.id, 'Наглядный пример: ваш отпуск сейчас находится в статусе черновика.')
        bot.send_photo(message.chat.id, open('instructions_img/vacantion/photo_5_vacantion.jpg', 'rb'))
        bot.send_message(message.chat.id,
                         'Далее укажите комментарий "Плановый отпуск" 📝 и отправьте на согласование. ⏰ Обращаем ваше внимание, что отпуск на согласование должен быть отправлен минимум за 2 недели до его начала. Если вы не собираетесь идти в отпуск, обратитесь к начальнику участка для его переноса. 🕒 Отпуск необходимо перенести до его начала и чем раньше это будет сделано, тем лучше. Это важно, так как бухгалтерии нужно успеть рассчитать отпускные. 🧮')
        bot.send_photo(message.chat.id, open('instructions_img/vacantion/photo_6_vacantion.jpg', 'rb'))

    else:
        bot.reply_to(message,
                     f"Мы очень рады видеть вас снова!\nЕсли у вас возникли вопросы, пожалуйста, воспользуйтесь нашим меню и выберите раздел «Часто задаваемые вопросы FAQ».\nМы всегда готовы помочь!")


# Получение текущего дня и запуск функции auto_shift() 1 числа каждого месяца.
def check_day():
    current_day = datetime.today().day
    print(current_day)
    if current_day == 1:
        auto_shift()


# Запуск bot.polling в отдельном потоке, чтобы он работал параллельно с задачами планировщика schedule.
def bot_polling():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(e)
            time.sleep(15)


threading.Thread(target=bot_polling, daemon=True).start()
schedule.every().day.at("00:01").do(check_day)  # Запуск функции получения текущего дня.
schedule.every().day.at("15:00").do(shift_message)  # Запуск функции оповещения смены графика.

while True:
    schedule.run_pending()
    time.sleep(60)
