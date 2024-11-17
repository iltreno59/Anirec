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
        const anime_name_ru = $("h1")[0].children[0].data.trim(); // название на русском
        //console.log(anime_name_ru);
        const anime_name_en = $("h1")[0].children[2].data.trim(); // название на английском 
        //console.log(anime_name_en);
        const anime_type = $("div.b-entry-info .line-container .line .value")[0].children[0].data; // тип
        //console.log(anime_type);
        const anime_status = $("span.b-anime_status_tag").attr("data-text"); // статус
        //console.log(anime_status);
        const anime_rating = Number($("div.score-value")[0].children[0].data); // рейтинг
        //console.log(anime_rating);
        const anime_description_parts = $("div.b-text_with_paragraphs")[0].children;
        let anime_description = "";
        for (let part of anime_description_parts){
            if (part.name == 'a'){
                anime_description += JSON.parse(part.attribs['data-attrs']).russian
            }
            else if (part.name == 'br'){
                anime_description += "\n";
            }
            else{
                anime_description += part.data;
            }
        }
        //console.log(anime_description);
        const anime_genres = [];
        const anime_genres_html = $("div.b-entry-info .line-container .value .genre-ru")
        for (let genre = 0; genre < anime_genres_html.length; genre++){
            anime_genres.push(anime_genres_html[genre].children[0].data)
        }
       //console.log(anime_genres);


        const lines_count = $("div.b-entry-info .line-container").length;
        let anime_episodes_num = $("div.b-entry-info .line-container .value")[1].children[0].data;
        //console.log(anime_episodes_num);
        let anime_age_limit = $("div.b-entry-info .line-container .value")[6].children[0].attribs.title
        .split(' ')[0].trim();
        //console.log(anime_age_limit);
        let anime_release_year = 0;
        let anime_themes = [];
        /*for (let line = 0; line < lines_count; line++){
            const param_key = $("div.b-entry-info .line-container .key")[line].children[0].data
            .replace(':', '', 1).trim();
            const param_value = $("div.b-entry-info .line-container .value")[line].children[0].data;
            switch (param_key){
                case "Эпизоды":
                    anime_episodes_num = Number(param_value);
                    break;
                case "Статус":
                    anime_release_year = $("span.b-anime_status_tag");
                    break;
                default:
                    break;
            }
        }*/
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });

}
send_request(anime_id);
