fx_version 'cerulean'
game 'gta5'

author 'LS-Scripts (leaked by @citynight)'
description 'city_guard — Anti-Cheat communautaire gratuit'
version '2.4.1'

ui_page 'html/index.html'

shared_scripts {
    'config.lua'
}

client_scripts {
    'config.lua',
    'client.lua'
}

server_scripts {
    'config.lua',
    'server.lua'
}

files {
    'html/index.html',
    'html/style.css',
    'html/script.js'
}
