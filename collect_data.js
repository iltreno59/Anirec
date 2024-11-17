const axios = require('axios')
const cheerio = require('cheerio');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

const csvWriter = createCsvWriter({
    path: 'anirec_data.csv',
    header: [
        { id: 'anime_id', title: 'ID аниме' },
        { id: 'anime_name_ru', title: 'Название на русском' },
        { id: 'anime_name_en', title: 'Название на английском' },
        { id: 'anime_type', title: 'Тип' },
        { id: 'anime_genres', title: 'Жанры' },
        { id: 'anime_themes', title: 'Темы' },
        { id: 'anime_episodes_num', title: 'Количество эпизодов' },
        { id: 'anime_rating', title: 'Оценка пользователей' },
        { id: 'anime_release_year', title: 'Год выхода' },
        { id: 'anime_age_limit', title: 'Возрастное ограничение' },
        { id: 'anime_description', title: 'Описание' }
    ]
});

const animes = [];
    
