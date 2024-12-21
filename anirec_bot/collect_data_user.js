const axios = require('axios')
const cheerio = require('cheerio');
const fs = require('fs');


let user_animes = [];

async function send_request(user_url){
    user_animes = [];
    const user_name = user_url.split('/')[3].replace('+', ' ');
    return new Promise((resolve, reject) => {
        axios.get(user_url)
            .then(response => {
                const $ = cheerio.load(response.data);
                const anime_list = $("div.list-groups tr.user_rate");
                let data = `${new Date().toUTCString()} : Link is valid\n`;
                                    fs.appendFile("logs.txt", data, function(err){
                                    if (err) throw err;
                                    })
                for (let anime of anime_list){
                    const anime_id = anime.attribs['data-target_id'];
                    const user_rating = anime.children[2].children[0].children[0].data;
                    if (isNaN(user_rating)) continue;
                    const user_anime_unit = {
                        user_name: user_name,
                        id: anime_id,
                        user_rating: user_rating
                    };
                    user_animes.push(user_anime_unit);
                    resolve();
                }
            })
    })
}

module.exports = async function get_all_users_anime(user_url){
    await send_request(user_url);
    return user_animes;
}