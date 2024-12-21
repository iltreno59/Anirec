const { Sequelize } = require('sequelize')
const params = require('./connection_params.js')

const sequelize = new Sequelize(params.db_name, params.username, params.password, {
    host: params.host,
    dialect: params.dialect,
    define: {
        freezeTableName: true,
      }
});
module.exports = { sequelize };