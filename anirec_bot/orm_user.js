const get_all_users_anime = require('./collect_data_user');
const { users_data } = require('../create_tables');

async function main(user_url){
    const users_animes = await get_all_users_anime(user_url);
    const user_name = users_animes[0].user_name;
    for (let anime of users_animes){
        const anime_object = users_data.build({
            id: anime.id,
            user_name: user_name,
            user_rating: anime.user_rating
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
// Получаем URL из аргументов командной строки
const user_url = process.argv[2];
if (!user_url) {
    console.error('Ошибка: URL не был передан.');
    process.exit(1);
}

// Запускаем функцию main с переданным URL
main(user_url);