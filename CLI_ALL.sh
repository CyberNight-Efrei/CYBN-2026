#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Configuration
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

ROOT="."
FILENAME="challenge.yml"
ACTION=""

# Environnement virtuel situé par défaut à côté du script.
# Peut être remplacé avec : VENV_DIR=/chemin/venv ./script.sh ...
VENV_DIR="${VENV_DIR:-${SCRIPT_DIR}/venv}"

# 1 = continuer après une erreur ; 0 = arrêter à la première erreur.
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-1}"

DRY_RUN=0

# Conserver le magasin de certificats utilisé pour CTFd.
if [[ -z "${REQUESTS_CA_BUNDLE:-}" &&
      -r /etc/ssl/certs/ca-certificates.crt ]]; then
    export REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
fi

# ============================================================
# Couleurs
# ============================================================

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
    RED=$'\033[0;31m'
    GREEN=$'\033[0;32m'
    BLUE=$'\033[0;34m'
    YELLOW=$'\033[1;33m'
    CYAN=$'\033[0;36m'
    NC=$'\033[0m'
else
    RED=""
    GREEN=""
    BLUE=""
    YELLOW=""
    CYAN=""
    NC=""
fi

info()    { printf '%s[INFO]%s %s\n' "$CYAN" "$NC" "$*"; }
success() { printf '%s[OK]%s %s\n' "$GREEN" "$NC" "$*"; }
warn()    { printf '%s[ATTENTION]%s %s\n' "$YELLOW" "$NC" "$*"; }
error()   { printf '%s[ERREUR]%s %s\n' "$RED" "$NC" "$*" >&2; }

# ============================================================
# Aide
# ============================================================

usage() {
    cat <<EOF
Usage :
  $0 <action> [root] [options]

Actions :
  add       Ajouter le challenge
  install   Installer le challenge
  sync      Synchroniser le challenge
  mirror    Miroir du challenge

Arguments :
  root                 Répertoire racine (défaut : .)

Options :
  --dry-run            Afficher les commandes sans les exécuter
  --stop-on-error      Arrêter à la première erreur
  -h, --help           Afficher cette aide

Variables d'environnement :
  VENV_DIR             Chemin du venv (défaut : ${SCRIPT_DIR}/venv)
  CONTINUE_ON_ERROR    1 pour continuer, 0 pour arrêter
  REQUESTS_CA_BUNDLE   Magasin de certificats CA utilisé par requests

Exemples :
  $0 sync .
  $0 install /opt/CYBN-2026
  $0 mirror . --dry-run
  $0 add . --stop-on-error
EOF
}

# ============================================================
# Arguments
# ============================================================

if [[ $# -lt 1 ]]; then
    usage
    exit 2
fi

ACTION="$1"
shift

case "$ACTION" in
    add|install|sync|mirror) ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        error "Action inconnue : $ACTION"
        usage
        exit 2
        ;;
esac

# Le premier argument restant, s'il ne s'agit pas d'une option,
# est le répertoire racine.
if [[ $# -gt 0 && "$1" != --* && "$1" != "-h" ]]; then
    ROOT="$1"
    shift
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            ;;
        --stop-on-error)
            CONTINUE_ON_ERROR=0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error "Argument inconnu : $1"
            usage
            exit 2
            ;;
    esac
    shift
done

if [[ "$CONTINUE_ON_ERROR" != 0 &&
      "$CONTINUE_ON_ERROR" != 1 ]]; then
    error "CONTINUE_ON_ERROR doit valoir 0 ou 1."
    exit 2
fi

# ============================================================
# Vérifications préalables
# ============================================================

if [[ ! -d "$ROOT" ]]; then
    error "Répertoire racine introuvable : $ROOT"
    exit 1
fi

ROOT="$(cd -- "$ROOT" && pwd -P)"

if [[ ! -x "$VENV_DIR/bin/ctf" ]]; then
    error "ctfcli introuvable ou non exécutable : $VENV_DIR/bin/ctf"
    error "Vérifie VENV_DIR et l'installation de ctfcli."
    exit 1
fi

CTF_BIN="$VENV_DIR/bin/ctf"

info "Action       : $ACTION"
info "Racine       : $ROOT"
info "Environnement: $VENV_DIR"
info "TLS CA       : ${REQUESTS_CA_BUNDLE:-valeur par défaut de Python}"
info "Mode         : $([[ "$DRY_RUN" -eq 1 ]] && echo "simulation" || echo "exécution")"

# ============================================================
# Recherche des challenges
# ============================================================

info "Recherche des fichiers $FILENAME..."

mapfile -d '' -t files < <(
    find "$ROOT" \
        -type d \( -name .git -o -name venv -o -name .venv \) -prune -o \
        -type f -name "$FILENAME" -print0 |
        sort -z
)

if [[ ${#files[@]} -eq 0 ]]; then
    error "Aucun fichier '$FILENAME' trouvé sous '$ROOT'."
    exit 1
fi

info "${#files[@]} challenge(s) trouvé(s)."

# ============================================================
# Exécution
# ============================================================

OK_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAILED_DIRS=()

for file in "${files[@]}"; do
    dir="$(dirname -- "$file")"

    printf '\n%s========== %s ==========%s\n' "$BLUE" "$dir" "$NC"

    printf -v display_cmd '%q ' "$CTF_BIN" challenge "$ACTION" "$dir"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        info "Simulation : $display_cmd"
        ((SKIP_COUNT += 1))
        continue
    fi

    info "Exécution : $display_cmd"

    if "$CTF_BIN" challenge "$ACTION" "$dir"; then
        success "$dir"
        ((OK_COUNT += 1))
    else
        error "Échec : $dir"
        ((FAIL_COUNT += 1))
        FAILED_DIRS+=("$dir")

        if [[ "$CONTINUE_ON_ERROR" -eq 0 ]]; then
            warn "Arrêt demandé après la première erreur."
            break
        fi
    fi
done

# ============================================================
# Bilan
# ============================================================

printf '\n%s========== BILAN ==========%s\n' "$BLUE" "$NC"
printf 'Action       : %s\n' "$ACTION"
printf 'Trouvés      : %d\n' "${#files[@]}"
printf 'Réussites    : %d\n' "$OK_COUNT"
printf 'Échecs       : %d\n' "$FAIL_COUNT"
printf 'Non exécutés : %d\n' "$SKIP_COUNT"

if [[ ${#FAILED_DIRS[@]} -gt 0 ]]; then
    printf '\n%sChallenges en échec :%s\n' "$RED" "$NC"
    for dir in "${FAILED_DIRS[@]}"; do
        printf '  - %s\n' "$dir"
    done
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    success "Simulation terminée : aucune action ctfcli exécutée."
elif [[ "$FAIL_COUNT" -gt 0 ]]; then
    error "Traitement terminé avec des erreurs."
    exit 1
else
    success "Traitement terminé sans erreur."
fi