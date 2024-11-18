const axios = require('axios')
const cheerio = require('cheerio');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

const csvWriter = createCsvWriter({
    path: 'anirec_data.csv',
    header: [
        { id: 'id', title: 'ID аниме' },
        { id: 'name_ru', title: 'Название на русском' },
        { id: 'name_en', title: 'Название на английском' },
        { id: 'state', title: 'Статус' },
        { id: 'type', title: 'Тип' },
        { id: 'genres', title: 'Жанры' },
        { id: 'episodes_num', title: 'Количество эпизодов' },
        { id: 'rating', title: 'Оценка пользователей' },
        { id: 'release_year', title: 'Год выхода' },
        { id: 'age_limit', title: 'Возрастное ограничение' }
    ]
});

const animes = [];
let anime_id = 1;
let latest_anime_id = assignLatestAnimeId();

function send_request(anime_id) {
    return new Promise((resolve, reject) => {
        const url = `https://shikimori.one/animes/${anime_id}`;
        axios.get(url)
            .then(response => {
                if (response.status === 404) {
                console.log(`Anime with ID ${anime_id} not found. Skipping...`);
                resolve();
                return;
                }
                const $ = cheerio.load(response.data);
                const anime_name_ru = $("h1")[0].children[0].data.trim(); // название на русском
                if (anime_name_ru == 'Эта страница содержит "взрослый" контент, просматривать который могут только совершеннолетние пользователи.'){
                    console.log(`Anime with ID ${anime_id} is only for adults. Skipping...`);
                    resolve();
                    return;
                }
                const anime_name_en = $("h1")[0].children[2].data.trim(); // название на английском 
                const anime_type = $("div.b-entry-info .line-container .line .value")[0].children[0].data; // тип
                if (anime_type != "TV Сериал" && anime_type != "Фильм"){
                    console.log(`Anime with ID ${anime_id} is neither a tv show nor film. Skipping...`);
                    resolve();
                    return;
                }
                const anime_status_html = $("span.b-anime_status_tag").attr("data-text"); // статус
                let anime_status = "";
                if (anime_status_html == 'онгоинг') anime_status = "Ещё выходит";
                else if (anime_status_html == "вышло") anime_status = "Вышло";
                else{
                    console.log(`Anime with ID ${anime_id} is only anoinced. Skipping...`);
                    resolve();
                    return;
                }
                const anime_rating = Number($("div.score-value")[0].children[0].data); // рейтинг
                if (anime_rating < 6){
                    console.log(`Anime with ID ${anime_id} is too bad. Skipping...`);
                    resolve();
                    return;
                }
                const anime_genres = [];
                const anime_genres_html = $("div.b-entry-info .line-container .value .genre-ru");
                for (let genre = 0; genre < anime_genres_html.length; genre++) {
                    anime_genres.push(anime_genres_html[genre].children[0].data);
                }
                let anime_age_limit = 0;
                let anime_episodes_num = 1;

                const lines_count = $("div.b-entry-info .line-container .key").length;
                for (let line = 0; line < lines_count; line++) {
                    const param_key = $("div.b-entry-info .line-container .key")[line].children[0].data
                        .replace(':', '', 1).trim();
                    const param_value = $("div.b-entry-info .line-container .value")[line];
                    switch (param_key) {
                        case "Эпизоды":
                            anime_episodes_num = Number(param_value.children[0].data.split(' / ')[0]);
                            break;
                        case "Статус":
                            if (anime_type == "TV Сериал" && anime_status != "Ещё выходит"){
                            anime_release_year = Number(param_value
                                .children[1].next.attribs.title.trim()
                                .split(' по ')[0].replace('С ', '', 1).replace(' г.', '', 1)
                                .replace(' гг.', '').replace('в ', '').split('-')[0].split(' ').at(-1));
                            }
                            else{
                            anime_release_year = Number(param_value
                                .children[1].data.trim()
                                .split(' по ')[0].replace('С ', '', 1).replace(' г.', '', 1)
                                .replace(' гг.', '').replace('в ', '').split('-')[0].split(' ').at(-1));
                            }
                                break;
                        case "Рейтинг":
                                let anime_age_limit_html = param_value.children[0].attribs.title
                                .split(' ')[0].trim();
                                switch (anime_age_limit_html) {
                                    case "PG":
                                        anime_age_limit = 6;
                                        break;
                                    case "PG-13":
                                        anime_age_limit = 13;
                                        break;
                                    case "R-17":
                                        anime_age_limit = 17;
                                        break;
                                    case "R+":
                                        anime_age_limit = 18;
                                        break;
                                    case "RX":
                                        anime_age_limit = "WARNING: DELETE HENTAI NOW";
                                        console.log(`Anime with ID ${anime_id} is hentai. Skipping...`);
                                        resolve();
                                        return;
                                    default:
                                        break;
                                }
                                break;
                        default:
                            break;
                    }
                }
                const anime = {
                    id: anime_id,
                    name_ru: anime_name_ru.replace(';', ' '),
                    name_en: anime_name_en.replace(';', ' '),
                    type: anime_type,
                    state: anime_status,
                    genres: anime_genres.join(';'),
                    episodes_num: anime_episodes_num,
                    rating: anime_rating,
                    release_year: anime_release_year,
                    age_limit: anime_age_limit
                };
                //console.log(anime);
                animes.push(anime);
                resolve();
            })
            .catch(error => {
                if (error.response && error.response.status === 404) {
                    console.log(`Anime with ID ${anime_id} not found. Skipping...`);
                    resolve();
                } else {
                    console.error(`Error fetching data at anime id = ${anime_id}:`, error);
                    reject(error);
                }
            });
    });
}
async function find_last_anime(){
    await axios.get('https://shikimori.one/animes?order=id_desc')
    .then(response => {
        const $ = cheerio.load(response.data);
        latest_anime_id = Number($("article")[0].attribs.id);
    });
    return latest_anime_id;
}
async function assignLatestAnimeId() {
    latest_anime_id = await find_last_anime();
}

async function main() {
    await assignLatestAnimeId();
    while (anime_id <= latest_anime_id) {
        try{
            await send_request(anime_id);
        }
        finally{
            anime_id++;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    //console.log(animes);
    await csvWriter.writeRecords(animes)
    .then(() => {
        console.log('...Done writing');
    });
    console.log(`Количество записей: ${animes.length}`);
    console.log(`Количество столбцов: ${Object.keys(animes[0]).length}`);
}

main();
