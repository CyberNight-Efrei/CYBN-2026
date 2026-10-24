#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Configuration
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

ROOT="."
FILENAME="build_docker.sh"
CONTINUE_ON_ERROR=1
RUN_FLAG=0

# Environnement virtuel : configurable via l'environnement
VENV_DIR="${VENV_DIR:-${SCRIPT_DIR}/venv}"

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
  $0 [options] [root] [filename]

Options :
  -s, --strict     Arrêter à la première erreur
  -r, --run        Ajouter l'option -r aux scripts exécutés
  -h, --help       Afficher cette aide
  --               Fin des options

Arguments :
  root             Racine de recherche (défaut : .)
  filename         Fichier recherché (défaut : build_docker.sh)

Variables d'environnement :
  VENV_DIR         Répertoire à exclure (défaut : ${SCRIPT_DIR}/venv)

Exemples :
  $0
  $0 /opt/CYBN-2026
  $0 --run /opt/CYBN-2026
  $0 --strict /opt/CYBN-2026 build_docker.sh
EOF
}

# ============================================================
# Analyse des arguments
# ============================================================

POSITIONAL=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--strict)
            CONTINUE_ON_ERROR=0
            shift
            ;;
        -r|--run)
            RUN_FLAG=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            POSITIONAL+=("$@")
            break
            ;;
        -*)
            error "Option inconnue : $1"
            usage
            exit 2
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

if [[ ${#POSITIONAL[@]} -gt 2 ]]; then
    error "Trop d'arguments positionnels."
    usage
    exit 2
fi

if [[ ${#POSITIONAL[@]} -ge 1 ]]; then
    ROOT="${POSITIONAL[0]}"
fi

if [[ ${#POSITIONAL[@]} -ge 2 ]]; then
    FILENAME="${POSITIONAL[1]}"
fi

# ============================================================
# Vérifications préalables
# ============================================================

if [[ ! -d "$ROOT" ]]; then
    error "Répertoire racine introuvable : $ROOT"
    exit 1
fi

ROOT="$(cd -- "$ROOT" && pwd -P)"
VENV_DIR_ABS="$(realpath -m -- "$VENV_DIR")"
TEMPLATE_DIR="$ROOT/0-CHALL-TEMPLATE"

info "Racine        : $ROOT"
info "Fichier       : $FILENAME"
info "Venv exclu    : $VENV_DIR_ABS"
info "Mode -r       : $RUN_FLAG"
info "Mode strict   : $((1 - CONTINUE_ON_ERROR))"

# ============================================================
# Recherche des scripts
# ============================================================

info "Recherche des fichiers..."

FILES_TMP="$(mktemp)"
trap 'rm -f -- "$FILES_TMP"' EXIT

if ! find "$ROOT" \
    \( -type d \( \
        -name '.*' \
        -o -path "$VENV_DIR_ABS" \
        -o -path "$TEMPLATE_DIR" \
    \) -prune \) -o \
    \( -type f -name "$FILENAME" -print0 \) |
    sort -z > "$FILES_TMP"; then
    error "La recherche des fichiers a échoué."
    exit 1
fi

mapfile -d '' -t files < "$FILES_TMP"

if [[ ${#files[@]} -eq 0 ]]; then
    error "Aucun fichier '$FILENAME' trouvé sous '$ROOT'."
    exit 1
fi

info "${#files[@]} fichier(s) trouvé(s)."

# ============================================================
# Préparation de l'exécution
# ============================================================

OK_COUNT=0
FAIL_COUNT=0
FAILED_FILES=()

RUN_ARGS=()
if [[ "$RUN_FLAG" -eq 1 ]]; then
    RUN_ARGS=(-r)
fi

# ============================================================
# Exécution des scripts trouvés
# ============================================================

for file in "${files[@]}"; do
    dir="$(dirname -- "$file")"
    base="$(basename -- "$file")"

    printf '\n%s========== %s ==========%s\n' "$BLUE" "$file" "$NC"

    printf -v display_cmd 'sudo bash %q' "./$base"
    if [[ "$RUN_FLAG" -eq 1 ]]; then
        display_cmd+=" -r"
    fi

    info "Exécution : $display_cmd"

    if (cd -- "$dir" && sudo bash "./$base" "${RUN_ARGS[@]}"); then
        success "$file"
        ((OK_COUNT += 1))
    else
        status=$?
        error "Échec : $file (code de retour : $status)"

        ((FAIL_COUNT += 1))
        FAILED_FILES+=("$file (code : $status)")

        if [[ "$CONTINUE_ON_ERROR" -eq 0 ]]; then
            warn "Mode strict : arrêt après cette erreur."
            break
        fi
    fi
done

# ============================================================
# Bilan final
# ============================================================

TOTAL_COUNT=${#files[@]}
PROCESSED_COUNT=$((OK_COUNT + FAIL_COUNT))
SKIPPED_COUNT=$((TOTAL_COUNT - PROCESSED_COUNT))

printf '\n%s========== BILAN FINAL ==========%s\n' "$BLUE" "$NC"
printf 'Fichiers trouvés       : %d\n' "$TOTAL_COUNT"
printf 'Fichiers traités       : %d\n' "$PROCESSED_COUNT"
printf '%sRéussites              : %d%s\n' "$GREEN" "$OK_COUNT" "$NC"
printf '%sÉchecs                 : %d%s\n' "$RED" "$FAIL_COUNT" "$NC"
printf 'Non exécutés           : %d\n' "$SKIPPED_COUNT"

if [[ ${#FAILED_FILES[@]} -gt 0 ]]; then
    printf '\n%s========== DÉTAIL DES ERREURS ==========%s\n' "$RED" "$NC"

    for failed in "${FAILED_FILES[@]}"; do
        printf '%s- %s%s\n' "$RED" "$failed" "$NC"
    done
fi

printf '\n'

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    error "Traitement terminé avec $FAIL_COUNT erreur(s)."
    exit 1
else
    success "Tous les scripts exécutés se sont terminés sans erreur."
    exit 0
fi