
# =====================================================
# WINDOWS CTF - CLEANUP
# =====================================================

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$DisableRdp
)

$ErrorActionPreference = "Continue"

$BasePath = "$env:PUBLIC\Music"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       WINDOWS CTF CLEANUP" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# =====================================================
# 1. ARRET DES AGENTS POWERSHELL
# =====================================================

Write-Host "`n[1] Recherche des agents actifs..." -ForegroundColor Yellow

$AgentPattern = [regex]::Escape($BasePath) +
    '\\[0-9a-fA-F]{32}\\[0-9a-fA-F]{32}\.ps1'

$Processes = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match '^(powershell|pwsh)\.exe$' -and
        $_.CommandLine -and
        $_.CommandLine -match $AgentPattern
    }

foreach ($Process in $Processes) {

    if ($PSCmdlet.ShouldProcess(
        "PID $($Process.ProcessId)",
        "Arrêter l'agent PowerShell"
    )) {
        try {
            Stop-Process -Id $Process.ProcessId -Force -ErrorAction Stop
            Write-Host "[+] Processus arrêté : $($Process.ProcessId)" -ForegroundColor Green
        }
        catch {
            Write-Warning "Impossible d'arrêter PID $($Process.ProcessId) : $_"
        }
    }
}

# =====================================================
# 2. SUPPRESSION DES TACHES PLANIFIEES
# =====================================================

Write-Host "`n[2] Recherche des tâches CTF..." -ForegroundColor Yellow

$Tasks = Get-ScheduledTask -ErrorAction SilentlyContinue |
    Where-Object {
        $_.TaskName -match 'FirefoxUpdater'
    }

foreach ($Task in $Tasks) {

    $FullName = "$($Task.TaskPath)$($Task.TaskName)"

    if ($PSCmdlet.ShouldProcess($FullName, "Supprimer la tâche planifiée")) {

        try {
            Stop-ScheduledTask `
                -TaskName $Task.TaskName `
                -TaskPath $Task.TaskPath `
                -ErrorAction SilentlyContinue

            Unregister-ScheduledTask `
                -TaskName $Task.TaskName `
                -TaskPath $Task.TaskPath `
                -Confirm:$false `
                -ErrorAction Stop

            Write-Host "[+] Tâche supprimée : $FullName" -ForegroundColor Green
        }
        catch {
            Write-Warning "Erreur sur $FullName : $_"
        }
    }
}

# =====================================================
# 3. SUPPRESSION DES DOSSIERS TEMPORAIRES
# =====================================================

Write-Host "`n[3] Nettoyage de Public\Music..." -ForegroundColor Yellow

if (Test-Path -LiteralPath $BasePath) {

    $Directories = Get-ChildItem `
        -LiteralPath $BasePath `
        -Directory `
        -Force |
        Where-Object {
            $_.Name -match '[0-9a-fA-F]{32}'
        }

    foreach ($Directory in $Directories) {

        if ($PSCmdlet.ShouldProcess(
            $Directory.FullName,
            "Supprimer le dossier temporaire"
        )) {

            try {
                Remove-Item `
                    -LiteralPath $Directory.FullName `
                    -Recurse `
                    -Force `
                    -ErrorAction Stop

                Write-Host "[+] Dossier supprimé : $($Directory.Name)" -ForegroundColor Green
            }
            catch {
                Write-Warning "Impossible de supprimer $($Directory.FullName) : $_"
            }
        }
    }
}

# =====================================================
# 4. SUPPRESSION DE L'ANCIEN FICHIER DE LIAISON
# =====================================================

Write-Host "`n[4] Nettoyage des fichiers de liaison..." -ForegroundColor Yellow

if (Test-Path -LiteralPath $StateFile) {

    if ($PSCmdlet.ShouldProcess($StateFile, "Supprimer le fichier de liaison")) {

        Remove-Item -LiteralPath $StateFile -Force

        Write-Host "[+] Fichier de liaison supprimé" -ForegroundColor Green
    }
}

# =====================================================
# 5. VERIFICATION FINALE
# =====================================================

Write-Host "`n[6] Vérification finale..." -ForegroundColor Yellow

$RemainingTasks = Get-ScheduledTask -ErrorAction SilentlyContinue |
    Where-Object {
        $_.TaskName -match 'FirefoxUpdater'
    }

$RemainingDirs = Get-ChildItem `
    -LiteralPath $BasePath `
    -Directory `
    -Force `
    -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match '[0-9a-fA-F]{32}'
    }

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "             CLEANUP RESULT" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "Tâches restantes : $(@($RemainingTasks).Count)"
Write-Host "Dossiers GUID restants : $(@($RemainingDirs).Count)"

if (@($RemainingTasks).Count -eq 0 -and @($RemainingDirs).Count -eq 0) {
    Write-Host "`n[+] Nettoyage terminé !" -ForegroundColor Green
}
else {
    Write-Warning "Certains éléments n'ont pas été supprimés."
}

Write-Host "`nSysmon et NXLog ont été conservés."
Write-Host "Les journaux Windows n'ont pas été effacés."
