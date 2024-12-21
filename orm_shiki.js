const get_all_animes = require('./collect_data_shiki');
const { shiki_data } = require('./create_tables');

async function main() {
    const animes = await get_all_animes();
    for (let anime of animes){
        const anime_object = shiki_data.build({
            id: anime.id,
            name_ru: anime.name_ru,
            name_en: anime.name_en,
            type: anime.type,
            state: anime.state,
            genres: anime.genres,
            episodes_num: anime.episodes_num,
            release_year: anime.release_year,
            age_limit: anime.age_limit,
            description: anime.description
        });
        try {
            await anime_object.save();
        }
        catch (e) {
            if (e.name == 'SequelizeUniqueConstraintError') continue;
            else {
                console.log('Непредвиденная ошибка при внесении данных в БД: ', e)
                break;
            }
        }
    }
}

main();