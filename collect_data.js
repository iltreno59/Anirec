const axios = require('axios')
const cheerio = require('cheerio');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

const csvWriter = createCsvWriter({
    path: 'anirec_data.csv',
    header: [
        { id: 'anime_id', title: 'ID аниме' },
        { id: 'anime_name_ru', title: 'Название на русском' },
        { id: 'anime_name_en', title: 'Название на английском' },
        { id: 'anime_status', title: 'Статус' },
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
let anime_id = 1;


function send_request(anime_id){

    const url = `https://shikimori.one/animes/${anime_id}`;
    axios.get(url)
    .then(response => {
        const id = anime_id;
        const $ = cheerio.load(response.data)
        const anime_name_ru = $("h1")[0].children[0].data.trim();
        //console.log(anime_name_ru);
        const anime_name_en = $("h1")[0].children[2].data.trim();
        //console.log(anime_name_en);
        const anime_type = $("div.b-entry-info .line-container .line .value")[0].children[0].data;
        //console.log(anime_type);
        const anime_status = $("span.b-anime_status_tag").attr("data-text");
        //console.log(anime_status);
        const anime_rating = Number($("div.score-value")[0].children[0].data);
        //console.log(anime_rating);
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });

}
send_request(anime_id);
