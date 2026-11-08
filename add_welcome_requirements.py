from pathlib import Path
import re
import sys

VALUE = "Bienvenue !"


def normalize_requirement(line):
    # Retirer l'indentation et le marqueur de liste
    value = re.sub(r"^\s+-\s*", "", line).strip()

    # Retirer les commentaires en fin de ligne
    value = re.split(r"\s+#", value, maxsplit=1)[0].strip()

    # Retirer les guillemets éventuels
    value = value.strip("\"'").strip()

    return value


def add_requirement(folder):
    folder = Path(folder)

    for file in folder.rglob("challenge*.yml"):
        if file.parts[0] == "Welcome":
            continue

        with file.open("r", encoding="utf-8", newline="") as f:
            content = f.read()

        lines = content.splitlines(keepends=True)

        # Repérer requirements à la racine
        req_index = next(
            (
                i for i, line in enumerate(lines)
                if re.match(r"^requirements\s*:", line)
            ),
            None
        )

        if req_index is None:
            # Champ absent : ajout en fin de fichier
            if content and not content.endswith(("\n", "\r")):
                content += "\n"

            if content and not content.endswith(("\n\n", "\r\n\r\n")):
                content += "\n"

            content += f'requirements:\n  - "{VALUE}"\n'

        else:
            # Déterminer la fin du bloc requirements
            end_index = len(lines)

            for i in range(req_index + 1, len(lines)):
                if re.match(r"^[^\s#][^:\n]*\s*:", lines[i]):
                    end_index = i
                    break

            block = lines[req_index + 1:end_index]

            # Vérifier si la valeur existe déjà
            already_exists = any(
                normalize_requirement(line) == VALUE
                for line in block
                if re.match(r"^\s+-\s+", line)
            )

            if already_exists:
                print(f"Ignoré (déjà présent) : {file}")
                continue

            # Chercher le dernier élément de la liste
            list_indexes = [
                i for i in range(req_index + 1, end_index)
                if re.match(r"^\s+-\s+", lines[i])
            ]

            if list_indexes:
                last_index = list_indexes[-1]

                indent = re.match(
                    r"^(\s*)-", lines[last_index]
                ).group(1)

                # Garantir un saut de ligne après le dernier élément
                if not lines[last_index].endswith(("\n", "\r")):
                    lines[last_index] += "\n"

                # Insérer la valeur sur une nouvelle ligne
                lines.insert(
                    last_index + 1,
                    f'{indent}- "{VALUE}"\n'
                )

            else:
                # Liste vide
                lines.insert(
                    req_index + 1,
                    f'  - "{VALUE}"\n'
                )

            content = "".join(lines)

        # Réécrire le fichier
        with file.open("w", encoding="utf-8", newline="") as f:
            f.write(content)

        print(f"Modifié : {file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        folder = "."
    else:
        folder = sys.argv[1]

    add_requirement(folder)
