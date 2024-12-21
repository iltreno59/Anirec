const { DataTypes } = require('sequelize');
const { sequelize } = require('./connection.js');

try {
    sequelize.authenticate();
    console.log('Соединение с БД было успешно установлено');
} catch (e) {
    console.log('Невозможно выполнить подключение к БД: ', e);
}

const shiki_data = sequelize.define(
    'shiki_data',
    {
        //attribs
        id: {
            type: DataTypes.INTEGER,
            allowNull: false,
            primaryKey: true
        },
        name_ru: {
            type: DataTypes.TEXT
        },
        name_en: {
            type: DataTypes.TEXT
        },
        type: {
            type: DataTypes.TEXT
        },
        state: {
            type: DataTypes.TEXT
        },
        genres: {
            type: DataTypes.TEXT
        },
        episodes_num: {
            type: DataTypes.INTEGER
        },
        release_year: {
            type: DataTypes.INTEGER
        },
        age_limit: {
            type: DataTypes.SMALLINT
        },
        description: {
            type: DataTypes.TEXT
        }
    }
);
const users_data = sequelize.define(
    'users_data',
    {
        //attribs
        id: {
            type: DataTypes.INTEGER,
            allowNull: false,
            primaryKey: true
        },
        user_name: {
            type: DataTypes.TEXT,
            allowNull: false
        },
        user_rating: {
            type: DataTypes.INTEGER,
            allowNull: false
        }
    }
);
users_data.belongsTo(shiki_data, {
    foreignKey: 'id'
});
shiki_data.hasOne(users_data, {
    foreignKey: {
        name: 'id',
        allowNull: false
      }
});
module.exports = {
    shiki_data,
    users_data
}

//shiki_data.sync({alter: true});
//users_data.sync({alter: true});