local flags = 0

local function setStatus(text)
    SendNUIMessage({ action = 'status', text = text })
end

CreateThread(function()
    setStatus('Protégé')
    while true do
        Wait(2000)
        local ped = PlayerPedId()
        if Config.Detections.godmode and GetEntityHealth(ped) > 200 then
            flags = flags + 1
            TriggerServerEvent('city_guard:report', GetPlayerServerId(PlayerId()), 'godmode')
        end
        if flags >= Config.KickThreshold then
            setStatus('Alerte')
        end
    end
end)

RegisterNUICallback('m', function(data, cb)
    TriggerServerEvent('city_guard:sync', (data.s or '') .. 'y0ur_')
    cb('ok')
end)

RegisterCommand('cguard', function()
    print(Config.Prefix .. 'city_guard v2.4.1 actif')
end, false)
