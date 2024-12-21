import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import psycopg2
import subprocess
import conn_options
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from anirec_token import TOKEN

# Глобальные переменные
predictions = []  # Список для хранения предсказаний
index = 0  # Глобальный индекс для отслеживания текущего аниме
user_name = None  # Глобальная переменная для хранения имени пользователя

class Anime:
    def __init__(self, name_ru, anime_type, genres, episodes_num, release_year, age_limit, user_rating):
        self.name_ru = name_ru  # Убрали запятую
        self.anime_type = anime_type  # Убрали запятую
        self.genres = genres  # Убрали запятую
        self.episodes_num = episodes_num  # Убрали запятую
        self.release_year = release_year  # Убрали запятую
        self.age_limit = age_limit  # Убрали запятую
        self.user_rating = user_rating  # Убрали запятую

def run_collect_data_user(url):
    try:
        result = subprocess.run(['node', 'orm_user.js', url], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Ошибка при выполнении скрипта: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот Anirec. Могу подобрать аниме вам по вкусам. Для этого отправьте мне имя пользователя на Шикимори.')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_name, predictions, index  # Используем глобальные переменные

    user_name = str(update.message.text)  # Сохраняем имя пользователя
    link = f"https://shikimori.one/{user_name.replace(' ', '+')}/list/anime?order=rate_score"
    await update.message.reply_text("Приступаю к работе...")
    run_collect_data_user(link)

    conn_params = {
        "dbname": conn_options.db_name,
        "user": conn_options.user_name,
        "password": conn_options.password,
        "host": conn_options.host,
        "port": conn_options.port 
    }

    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
    except psycopg2.Error as e:
        print("Ошибка при подключении к базе данных:", e)
        await update.message.reply_text("Ошибка при подключении к базе данных. Попробуйте позже.")
        return

    select_query1 = f"""
    SELECT shiki_data.name_ru, shiki_data.type, shiki_data.genres, 
    shiki_data.episodes_num,
    shiki_data.release_year, shiki_data.age_limit, users_data.user_rating 
    FROM shiki_data
    INNER JOIN users_data ON shiki_data.id = users_data.id
    WHERE users_data.user_name = '{user_name}'
    """

    user_list = []
    try:
        cursor.execute(select_query1)
        for row in cursor:
            name_ru = str(row[0])
            anime_type = str(row[1]) 
            genres = str(row[2])
            episodes_num = int(row[3]) 
            release_year = int(row[4])  
            age_limit = int(row[5])
            user_rating = int(row[6]) 

            user_list.append(Anime(name_ru, anime_type, genres, episodes_num, release_year, age_limit, user_rating))
    except psycopg2.Error as e:
        print("Ошибка при выполнении SQL-запроса:", e)
        await update.message.reply_text("Ошибка при выполнении запроса к базе данных. Попробуйте позже.")
        return

    data = []
    for anime in user_list:
        anime_xy = [anime.name_ru, anime.anime_type, anime.genres, anime.episodes_num, anime.release_year, anime.age_limit, anime.user_rating]
        data.append(anime_xy)

    df = pd.DataFrame(data, columns=["Название", "Тип", "Жанры", "Эпизоды", "Год выпуска", "Возрастной рейтинг", "Оценка"])

    df["Тип"] = df["Тип"].astype("category").cat.codes

    await update.message.reply_text("Собрал все данные о ваших предпочтениях, подбираю варианты...")

    genre_vectorizer = TfidfVectorizer()
    genres_vectors = genre_vectorizer.fit_transform(df["Жанры"])
    genres_df = pd.DataFrame(genres_vectors.toarray(), columns=genre_vectorizer.get_feature_names_out())

    numerical_features = df[["Эпизоды", "Возрастной рейтинг", "Год выпуска"]]
    numerical_features = numerical_features.fillna(0)
    numerical_features = numerical_features.astype(float)

    scaler = StandardScaler()
    numerical_features = scaler.fit_transform(numerical_features)
    numerical_df = pd.DataFrame(numerical_features, columns=["Эпизоды", "Возрастной рейтинг", "Год выпуска"])

    X = pd.concat([pd.DataFrame(df["Тип"]), genres_df, numerical_df], axis=1)
    y = df["Оценка"]  # Целевая переменная

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    select_query2 = f"""
    SELECT id, name_ru, type, state, genres, episodes_num, release_year, age_limit 
    FROM shiki_data WHERE id NOT IN(
    SELECT id FROM users_data WHERE user_name = '{user_name}'
    )
    """

    try:
        cursor.execute(select_query2)
        for row in cursor:
            if row[5] is None or row[6] is None or row[7] is None:
                continue  # Пропускаем строки с пустыми значениями

            sample = {
                "Тип": 0 if row[2] == 'TV Сериал' else 1,
                "Жанры": row[4],
                "Эпизоды": row[5],
                "Год выпуска": row[6],
                "Возрастной рейтинг": row[7]
            }

            sample_genres = genre_vectorizer.transform([sample["Жанры"]])
            sample_numerical = scaler.transform([[sample["Эпизоды"], sample["Возрастной рейтинг"], sample["Год выпуска"]]])
            sample_X = np.hstack([[[sample["Тип"]]], sample_genres.toarray(), sample_numerical])

            pred = model.predict(sample_X)
            predictions.append((row[1], pred[0]))  # Добавляем предсказание в список

        sorted_predictions = sorted(predictions, key=lambda x: x[1], reverse=True)
        predictions = sorted_predictions  # Обновляем список предсказаний

        await show_next_anime(update, context)
    except psycopg2.Error as e:
        print("Ошибка при выполнении SQL-запроса:", e)
        await update.message.reply_text("Ошибка при выполнении запроса к базе данных. Попробуйте позже.")
        return

async def show_next_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global index, predictions  # Используем глобальные переменные

    # Определяем, откуда пришло сообщение: из текстового сообщения или из callback_query
    message = update.message or update.callback_query.message

    if index >= len(predictions):
        await message.reply_text("Все аниме из списка были предложены.")
        return

    anime_name, anime_rating = predictions[index]

    select_anime_query = f"""
    SELECT * FROM shiki_data WHERE name_ru = '{anime_name}'
    """

    conn_params = {
        "dbname": conn_options.db_name,
        "user": conn_options.user_name,
        "password": conn_options.password,
        "host": conn_options.host,
        "port": conn_options.port 
    }

    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
    except psycopg2.Error as e:
        print("Ошибка при подключении к базе данных:", e)
        await update.message.reply_text("Ошибка при подключении к базе данных. Попробуйте позже.")
        return

    anime_type = ''
    anime_state = ''
    anime_episodes = 0
    anime_age_limit = 0
    anime_release_year = 0
    anime_genres = ''
    anime_description = ''
    try:
        cursor.execute(select_anime_query)
        for row in cursor:
            anime_type = row[3]
            anime_state = row[4]
            anime_genres = row[5]
            anime_episodes = row[6]
            anime_release_year = row[7]
            anime_age_limit = row[8]
            anime_description = row[11].replace('undefined', '')
    except psycopg2.Error as e:
        print("Ошибка при выполнении SQL-запроса:", e)
        await update.message.reply_text("Ошибка при выполнении запроса к базе данных. Попробуйте позже.")
        return

    keyboard = [[InlineKeyboardButton("Следующее", callback_data="next_anime")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(f"Я рекомендую вам посмотреть: {anime_name}\nТип: {anime_type}\nСтатус: {anime_state}\nЧисло эпизодов: {anime_episodes}\nЖанры: {anime_genres.replace(';', ', ')}\nГод выхода: {anime_release_year}\nВозрастное ограничение: {anime_age_limit}+\nОписание:\n{anime_description}", reply_markup=reply_markup)

    index += 1  # Увеличиваем индекс для следующего аниме

async def next_anime_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    await show_next_anime(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот Anirec. Могу подобрать аниме вам по вкусам. Для этого отправьте мне имя пользователя на Шикимори.')

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(CallbackQueryHandler(next_anime_handler))

    application.run_polling()

if __name__ == '__main__':
    main()