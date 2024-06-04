import json
import pymysql

# Загрузка конфигурации из файла
with open('data.json', 'r') as file:
    config = json.load(file)

# Подключение к базе данных
connection = pymysql.connect(
    host=config['host'],
    port=config['port'],
    user=config['user'],
    password=config['password'],
    database=config['database']
)

cur = connection.cursor()

# Создание таблицы для викторин, если она не существует
async def connection_start():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            User_ID INT NOT NULL,
            isSubscribed BOOLEAN NOT NULL DEFAULT 0,
            isModerator BOOLEAN NOT NULL DEFAULT 0,
            correctAnswers INT NOT NULL DEFAULT 0,
            PRIMARY KEY (User_ID)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            Poll_ID VARCHAR(255) NOT NULL,
            Correct_Option_ID INT NOT NULL,
            PRIMARY KEY (Poll_ID)
        )
    """)
    connection.commit()

# Создание пользователя (если он еще не существует)
async def create_user(user_id):
    cur.execute("INSERT INTO users (User_ID) VALUES (%s) ON DUPLICATE KEY UPDATE User_ID = User_ID", (user_id,))
    connection.commit()

# Подписка пользователя на рассылку
async def subscribe(user_id):
    cur.execute("SELECT isSubscribed FROM users WHERE User_ID=%s", (user_id,))
    result = cur.fetchone()
    if result and result[0] == 1:
        return "Вы уже подписаны на рассылку!"
    else:
        cur.execute("UPDATE users SET isSubscribed=1 WHERE User_ID=%s", (user_id,))
        connection.commit()
        return "Вы успешно подписались!"

# Отписка пользователя от рассылки
async def unsubscribe(user_id):
    cur.execute("SELECT isSubscribed FROM users WHERE User_ID=%s", (user_id,))
    result = cur.fetchone()
    if result and result[0] == 0:
        return "Вы уже отписаны от рассылки!"
    else:
        cur.execute("UPDATE users SET isSubscribed=0 WHERE User_ID=%s", (user_id,))
        connection.commit()
        return "Нам жаль, что мы вас расстроили! Вы успешно отписались от нашей рассылки!"

# Получение списка подписчиков
async def get_subscribers():
    cur.execute("SELECT User_ID FROM users WHERE isSubscribed = 1")
    subscribers = [row[0] for row in cur.fetchall()]
    return subscribers

async def get_moderators():
    cur.execute("SELECT User_ID FROM users WHERE isModerator = 1")
    moderators = [row[0] for row in cur.fetchall()]
    return moderators

async def update_correct_answers(user_id):
    cur.execute("UPDATE users SET correctAnswers = correctAnswers + 1 WHERE User_ID=%s", (user_id,))
    connection.commit()

async def get_user_info(user_id):
    cur.execute("SELECT correctAnswers FROM users WHERE User_ID=%s", (user_id,))
    result = cur.fetchone()
    return result[0] if result else 0

async def get_top_players():
    cur.execute("SELECT * FROM users ORDER BY correctAnswers DESC LIMIT 10")
    top_players = cur.fetchall()
    return top_players

async def save_quiz(poll_id, correct_option_id):
    cur.execute("INSERT INTO quizzes (Poll_ID, Correct_Option_ID) VALUES (%s, %s)", (poll_id, correct_option_id))
    connection.commit()

async def get_correct_option_id(poll_id):
    cur.execute("SELECT Correct_Option_ID FROM quizzes WHERE Poll_ID=%s", (poll_id,))
    result = cur.fetchone()
    return result[0] if result else None


def close_connection():
    cur.close()
    connection.close()
