import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import re
import psycopg2
import subprocess
import conn_options
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ContextTypes, ApplicationBuilder, MessageHandler, filters
from anirec_token import TOKEN

class Anime:
    def __init__(self, name_ru, anime_type, genres, episodes_num, release_year, age_limit, user_rating):
        self.name_ru = name_ru,
        self.anime_type = anime_type,
        self.genres = genres,
        self.episodes_num = episodes_num,
        self.release_year = release_year,
        self.age_limit = age_limit,
        self.user_rating = user_rating




def run_collect_data_user(url):
    try:
        result = subprocess.run(['node', 'orm_user.js', url], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Ошибка при выполнении скрипта: {e}"
# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот Anirec. Могу подобрать аниме вам по вкусам. Для этого отправьте мне имя пользователя на Шикимори.')

# Обработчик текстовых сообщений
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = str(update.message.text)
    link = f"https://shikimori.one/{user_name.replace(' ', '+')}/list/anime?order=rate_score"
    await update.message.reply_text("Приступаю к работе...")
    run_collect_data_user(link)

    # Параметры подключения к базе данных
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

    # SQL-запрос для получения данных пользователя
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

    # Преобразуем данные в DataFrame
    data = []
    for anime in user_list:
        anime_xy = [anime.name_ru[0], anime.anime_type[0], anime.genres[0], anime.episodes_num[0], anime.release_year[0], anime.age_limit[0], anime.user_rating]
        print(anime_xy)
        data.append(anime_xy)

    df = pd.DataFrame(data, columns=["Название", "Тип", "Жанры", "Эпизоды", "Год выпуска", "Возрастной рейтинг", "Оценка"])

    df["Тип"] = df["Тип"].astype("category").cat.codes

    await update.message.reply_text("Собрал все данные о ваших предпочтениях, подбираю варианты...")

    # Преобразование жанров в векторы с использованием TfidfVectorizer
    genre_vectorizer = TfidfVectorizer()
    genres_vectors = genre_vectorizer.fit_transform(df["Жанры"])
    genres_df = pd.DataFrame(genres_vectors.toarray(), columns=genre_vectorizer.get_feature_names_out())

    # Нормализация числовых признаков (Эпизоды, Возрастной рейтинг, Год выпуска)
    numerical_features = df[["Эпизоды", "Возрастной рейтинг", "Год выпуска"]]

    # Проверка на пустые значения и замена их на 0
    numerical_features = numerical_features.fillna(0)

    # Убедимся, что все значения числовые
    numerical_features = numerical_features.astype(float)

    # Нормализация числовых признаков
    scaler = StandardScaler()
    numerical_features = scaler.fit_transform(numerical_features)
    numerical_df = pd.DataFrame(numerical_features, columns=["Эпизоды", "Возрастной рейтинг", "Год выпуска"])

    # Объединение всех признаков
    X = pd.concat([pd.DataFrame(df["Тип"]), genres_df, numerical_df], axis=1)
    y = df["Оценка"]  # Целевая переменная

    # Используем случайный лес для регрессии
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    # SQL-запрос для получения данных о новых аниме
    select_query2 = f"""
    SELECT id, name_ru, type, state, genres, episodes_num, release_year, age_limit 
    FROM shiki_data WHERE id NOT IN(
    SELECT id FROM users_data WHERE user_name = '{user_name}'
    )
    """

    predictions = {}
    try:
        cursor.execute(select_query2)
        for row in cursor:
            sample = {
                "Тип": 0 if row[2] == 'TV Сериал' else 1,
                "Жанры": row[4],
                "Эпизоды": row[5],
                "Год выпуска": row[6],
                "Возрастной рейтинг": row[7]
            }

            # Преобразуем жанры в вектор
            sample_genres = genre_vectorizer.transform([sample["Жанры"]])

            # Преобразуем числовые признаки
            sample_numerical = scaler.transform([[sample["Эпизоды"], sample["Возрастной рейтинг"], sample["Год выпуска"]]])

            # Объединяем признаки
            sample_X = np.hstack([[[sample["Тип"]]], sample_genres.toarray(), sample_numerical])

            # Предсказываем оценку
            pred = model.predict(sample_X)
            predictions[row[1]] = pred[0]  # Сохраняем предсказание

        # Отсортируем predictions по предсказанной оценке в порядке убывания
        sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)

        # Выберем аниме с самым высоким рейтингом
        top_anime = sorted_predictions[0]

        # Отправляем результат пользователю
        await update.message.reply_text(f"Я рекомендую вам посмотреть: {top_anime[0]}")
    except psycopg2.Error as e:
        print("Ошибка при выполнении SQL-запроса:", e)
        await update.message.reply_text("Ошибка при выполнении запроса к базе данных. Попробуйте позже.")
        return
    


# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот Anirec. Могу подобрать аниме вам по вкусам. Для этого отправьте мне имя пользователя на Шикимори.')
# Основная функция
def main():
    # Создаем приложение бота
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()