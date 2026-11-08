#!/usr/bin/env python3
"""Mini application RH/Paie fictive pour le challenge CTF Julie v2.

La zone de stockage du notebook est confinée à HOME_DIR :
- résolution composant par composant avec openat/dir_fd et O_NOFOLLOW ;
- refus des chemins absolus hors de HOME_DIR et des segments . / .. ;
- lecture des fichiers ordinaires uniquement ;
- écriture dans un nouveau fichier temporaire puis remplacement atomique ;
- aucune ouverture avec O_TRUNC du fichier cible (protection contre les hard links).

Hypothèses de déploiement : HOME_DIR et ses répertoires parents doivent être
protégés contre les modifications par des utilisateurs non fiables. Les
montages/bind mounts placés sous HOME_DIR doivent également être maîtrisés.
"""

from __future__ import annotations

import html
import os
import secrets
import stat
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"
PORT = 8080
HOME_DIR = "/home/app"
MAX_FILE_BYTES = 1024 * 1024
MAX_REQUEST_BYTES = MAX_FILE_BYTES * 3 + 64 * 1024


class NotebookError(Exception):
    """Erreur de chemin ou d'accès au notebook."""


# Ne jamais désactiver silencieusement O_NOFOLLOW : sans ce flag, le
# confinement contre les liens symboliques ne peut pas être garanti.
if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise RuntimeError(
        "Plateforme non compatible : O_NOFOLLOW et O_DIRECTORY sont obligatoires."
    )

_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW


def _components(user_path: str) -> list[str]:
    """Convertit un chemin en composants relatifs à HOME_DIR.

    Les chemins absolus sont acceptés uniquement sous HOME_DIR. Les segments
    vides, '.' et '..', ainsi que les caractères NUL, sont refusés.
    """
    if not isinstance(user_path, str):
        raise NotebookError("Chemin invalide.")

    raw = user_path.strip()
    if not raw or "\x00" in raw:
        raise NotebookError("Indiquez un chemin de fichier valide.")

    home = HOME_DIR.rstrip("/")
    if not home or not HOME_DIR.startswith("/"):
        raise RuntimeError("HOME_DIR doit être un chemin absolu non racine.")

    if raw.startswith("/"):
        if raw == home or raw == home + "/":
            raise NotebookError("Le notebook attend un fichier, pas un dossier.")
        if not raw.startswith(home + "/"):
            raise NotebookError(
                f"Accès refusé : le notebook est limité à {home}."
            )
        raw = raw[len(home) + 1 :]

    parts = raw.split("/")
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise NotebookError(
            "Chemin refusé : utilisez un chemin simple sous /home/app."
        )

    return parts


def _open_home_dir() -> int:
    """Ouvre HOME_DIR depuis /, sans suivre de lien symbolique.

    Chaque composant est ouvert relativement au descripteur du parent. Cela
    évite de suivre un lien symbolique dans /home ou /home/app.
    """
    if not HOME_DIR.startswith("/"):
        raise RuntimeError("HOME_DIR doit être un chemin absolu.")

    components = HOME_DIR.strip("/").split("/")
    if not components or any(part in ("", ".", "..") for part in components):
        raise RuntimeError("HOME_DIR est invalide.")

    try:
        current_fd = os.open(
            "/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
        )
    except OSError as exc:
        raise NotebookError("Impossible d'ouvrir la racine du système.") from exc

    try:
        for component in components:
            try:
                next_fd = os.open(component, _DIR_FLAGS, dir_fd=current_fd)
            except OSError as exc:
                raise NotebookError(
                    "Répertoire de base indisponible, invalide ou lien symbolique détecté."
                ) from exc

            old_fd = current_fd
            current_fd = next_fd
            os.close(old_fd)

        return current_fd
    except Exception:
        os.close(current_fd)
        raise


def _open_parent(parts: list[str], create: bool) -> tuple[int, str]:
    """Ouvre le dossier parent sans suivre de lien symbolique."""
    if not parts:
        raise NotebookError("Indiquez un nom de fichier.")

    current_fd = _open_home_dir()
    try:
        for component in parts[:-1]:
            try:
                next_fd = os.open(component, _DIR_FLAGS, dir_fd=current_fd)
            except FileNotFoundError:
                if not create:
                    raise NotebookError("Le dossier demandé n'existe pas.")

                try:
                    os.mkdir(component, 0o700, dir_fd=current_fd)
                except FileExistsError:
                    # Un autre worker a pu créer le dossier entre-temps.
                    # L'ouverture ci-dessous vérifiera qu'il s'agit bien d'un
                    # vrai répertoire et non d'un lien symbolique.
                    pass
                except OSError as exc:
                    raise NotebookError(
                        "Impossible de créer le dossier demandé."
                    ) from exc

                try:
                    next_fd = os.open(component, _DIR_FLAGS, dir_fd=current_fd)
                except OSError as exc:
                    raise NotebookError(
                        "Dossier invalide ou lien symbolique détecté."
                    ) from exc
            except OSError as exc:
                raise NotebookError(
                    "Chemin refusé : dossier invalide ou lien symbolique."
                ) from exc

            old_fd = current_fd
            current_fd = next_fd
            os.close(old_fd)

        return current_fd, parts[-1]
    except Exception:
        os.close(current_fd)
        raise


def notebook_read(user_path: str) -> str:
    parts = _components(user_path)
    parent_fd, filename = _open_parent(parts, create=False)
    flags = (
        os.O_RDONLY
        | os.O_CLOEXEC
        | os.O_NOFOLLOW
        | getattr(os, "O_NONBLOCK", 0)
    )

    try:
        try:
            file_fd = os.open(filename, flags, dir_fd=parent_fd)
        except FileNotFoundError as exc:
            raise NotebookError("Ce fichier n'existe pas encore.") from exc
        except OSError as exc:
            raise NotebookError(
                "Impossible d'ouvrir ce fichier (lien symbolique ou accès refusé)."
            ) from exc

        try:
            info = os.fstat(file_fd)
            if not stat.S_ISREG(info.st_mode):
                raise NotebookError(
                    "Le notebook ne lit que des fichiers ordinaires."
                )
            if info.st_nlink > 1:
                raise NotebookError(
                    "Lecture refusée : les fichiers liés physiquement ne sont pas acceptés."
                )
            if info.st_size > MAX_FILE_BYTES:
                raise NotebookError("Fichier trop volumineux (limite : 1 Mio).")

            chunks: list[bytes] = []
            remaining = MAX_FILE_BYTES + 1
            while remaining > 0:
                chunk = os.read(file_fd, min(65536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)

            data = b"".join(chunks)
            if len(data) > MAX_FILE_BYTES:
                raise NotebookError("Fichier trop volumineux (limite : 1 Mio).")

            return data.decode("utf-8", errors="replace")
        finally:
            os.close(file_fd)
    finally:
        os.close(parent_fd)


def notebook_write(user_path: str, content: str) -> int:
    """Écrit sans ouvrir ni tronquer le fichier cible.

    Un nouveau fichier temporaire est créé dans le répertoire parent déjà
    sécurisé. os.replace remplace ensuite uniquement l'entrée du répertoire :
    une cible symbolique ou hard-linkée n'est jamais suivie ni modifiée.
    """
    parts = _components(user_path)
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_FILE_BYTES:
        raise NotebookError("Texte trop volumineux (limite : 1 Mio).")

    parent_fd, filename = _open_parent(parts, create=True)
    temp_name = f".julie-tmp-{secrets.token_hex(16)}"
    temp_fd: int | None = None
    temp_created = False

    try:
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_CLOEXEC
            | os.O_NOFOLLOW
        )
        try:
            temp_fd = os.open(
                temp_name,
                flags,
                0o600,
                dir_fd=parent_fd,
            )
            temp_created = True
        except OSError as exc:
            raise NotebookError(
                "Impossible de créer le fichier temporaire."
            ) from exc

        info = os.fstat(temp_fd)
        if not stat.S_ISREG(info.st_mode):
            raise NotebookError(
                "Le notebook écrit uniquement dans des fichiers ordinaires."
            )

        view = memoryview(encoded)
        written = 0
        while written < len(view):
            count = os.write(temp_fd, view[written:])
            if count <= 0:
                raise NotebookError("Écriture interrompue.")
            written += count

        os.fsync(temp_fd)
        os.close(temp_fd)
        temp_fd = None

        # Source et destination sont des noms simples, dans le même dossier
        # identifié par parent_fd. Le rename ne suit pas un lien cible.
        os.replace(
            temp_name,
            filename,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )

        # Rend durable la modification de l'entrée du répertoire lorsque le
        # système de fichiers prend en charge fsync sur les répertoires.
        try:
            os.fsync(parent_fd)
        except OSError:
            pass

        return written

    except NotebookError:
        raise
    except OSError as exc:
        raise NotebookError("Impossible d'enregistrer le fichier.") from exc
    finally:
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except OSError:
                pass

        if temp_created:
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except OSError:
                # Après un os.replace réussi, le nom temporaire n'existe plus.
                pass

        os.close(parent_fd)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, content: str) -> bytes:
    nav = """
    <table class="menu" cellpadding="5" cellspacing="2" width="100%">
      <tr>
        <td><a href="/">Accueil</a></td>
        <td><a href="/rh">Ressources humaines</a></td>
        <td><a href="/paie">Bulletins de paie</a></td>
        <td><a href="/notebook">Bloc-notes</a></td>
      </tr>
    </table>
    """
    document = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} - Gestion RH Julie</title>
<style>
  body {{ background:#c0c0c0; color:#000; font-family:Tahoma,Arial,sans-serif; font-size:14px; }}
  a {{ color:#0000ee; }} a:visited {{ color:#551a8b; }}
  .cadre {{ max-width:900px; margin:18px auto; padding:12px; background:#eeeeee; border:4px ridge #fff; }}
  .bandeau {{ background:#000080; color:#fff; padding:10px; text-align:center; }}
  .bandeau h1 {{ margin:4px; font-family:"Times New Roman",serif; font-size:30px; }}
  .menu {{ background:#ffffcc; border:2px outset #fff; text-align:center; font-weight:bold; }}
  .panneau {{ background:#fff; border:2px inset #aaa; padding:12px; margin-top:12px; }}
  .notice {{ color:#800000; font-weight:bold; }}
  .petit {{ font-size:11px; color:#555; }}
  .bouton {{ border:3px outset #fff; background:#ddd; padding:4px 12px; font-weight:bold; cursor:pointer; }}
  input[type=text], textarea {{ box-sizing:border-box; width:100%; border:2px inset #aaa; padding:5px; font-family:monospace; }}
  textarea {{ min-height:230px; }}
  .compteur {{ color:#008000; font-family:monospace; }}
  hr {{ border:0; border-top:2px groove #fff; }}
</style>
</head>
<body>
<div class="cadre">
  <div class="bandeau">
    <div style="font-size:12px">★ ★ ★ INTRANET DE L'ENTREPRISE ★ ★ ★</div>
    <h1>Gestion RH &amp; Paie</h1>
    <div>Le personnel, c'est notre richesse !</div>
  </div>
  {nav}
  {content}
  <hr>
  <center class="petit">© 1998 - Service informatique - Optimisé pour Netscape Navigator 4.0</center>
  <center class="compteur">Vous êtes le visiteur n° 000042</center>
</div>
</body>
</html>"""
    return document.encode("utf-8")


class JulieHandler(BaseHTTPRequestHandler):
    server_version = "JulieRH/2.0"
    sys_version = ""

    def log_message(self, fmt: str, *args: object) -> None:
        print("[WEB] " + (fmt % args), flush=True)

    def send_html(self, body: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlsplit(self.path)
        route = parsed.path

        if route == "/":
            content = """
            <div class="panneau">
              <center><h2>Bienvenue sur l'intranet RH !</h2>
                <p><font color="#cc0000"><b>*** NOUVEAU : le portail RH passe en version 2 ***</b></font></p>
                <p>Bonjour, ici Julie, votre responsable des ressources humaines.</p>
                <p>Retrouvez les dossiers du personnel, les bulletins de paie et mon nouveau bloc-notes électronique.</p>
                <p><img alt="" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"> <b>Me contacter :</b> julie@entreprise.invalid</p>
                <p class="notice">Attention : sauvegardez vos notes avant de quitter le service !</p>
                <p>Dernière mise à jour : 04/07/1998</p>
              </center>
            </div>
            <div class="panneau"><b>Accès rapide</b><ul>
              <li><a href="/rh">Annuaire des salariés</a></li>
              <li><a href="/paie">Consulter un bulletin de paie</a></li>
              <li><a href="/notebook">Ouvrir le bloc-notes de Julie</a></li>
            </ul></div>
            """
            self.send_html(page("Accueil", content))
            return

        if route == "/rh":
            content = """
            <div class="panneau"><h2>Annuaire du personnel</h2>
              <table border="1" cellpadding="7" cellspacing="0" width="100%">
                <tr bgcolor="#ccccff"><th>Matricule</th><th>Nom</th><th>Service</th><th>Poste</th></tr>
                <tr><td>0042</td><td>Julie Martin</td><td>Ressources humaines</td><td>Responsable RH</td></tr>
                <tr><td>0017</td><td>Michel Durand</td><td>Informatique</td><td>Technicien système</td></tr>
                <tr><td>0023</td><td>Claude Bernard</td><td>Comptabilité</td><td>Comptable</td></tr>
              </table>
              <p><b>Message de Julie :</b> « Pour toute question concernant votre fiche de paie, passez me voir au bureau 12. »</p>
            </div>
            """
            self.send_html(page("Ressources humaines", content))
            return

        if route == "/paie":
            content = """
            <div class="panneau"><h2>Bulletin de paie - Décembre 1998</h2>
              <p>Salarié : <b>Michel Durand</b> &nbsp; Matricule : 0017</p>
              <table border="1" cellpadding="7" cellspacing="0" width="100%">
                <tr bgcolor="#ccccff"><th>Désignation</th><th>Montant (FRF)</th></tr>
                <tr><td>Salaire brut</td><td align="right">12 500,00</td></tr>
                <tr><td>Cotisations sociales</td><td align="right">- 2 625,00</td></tr>
                <tr><td>Indemnité de transport</td><td align="right">250,00</td></tr>
                <tr bgcolor="#ffffcc"><td><b>Net à payer</b></td><td align="right"><b>10 125,00</b></td></tr>
              </table>
              <p class="petit">Document fictif - Ne pas transmettre à l'extérieur de l'entreprise.</p>
            </div>
            """
            self.send_html(page("Bulletins de paie", content))
            return

        if route == "/notebook":
            query = urllib.parse.parse_qs(
                parsed.query, keep_blank_values=True, max_num_fields=8
            )
            filepath = query.get("path", ["note.txt"])[0]
            message = "Le bloc-notes de Julie est prêt."
            text = ""
            try:
                text = notebook_read(filepath)
                message = "Fichier chargé avec succès."
            except NotebookError as exc:
                if "n'existe pas encore" in str(exc) or "dossier demandé" in str(exc):
                    message = "Nouveau fichier : saisissez votre texte puis cliquez sur Enregistrer."
                else:
                    message = str(exc)
            except ValueError:
                message = "Requête invalide."
            self.render_notebook(filepath, text, message)
            return

        if route == "/health":
            self.send_html(page("État", '<div class="panneau">SERVICE OK</div>'))
            return

        self.send_html(
            page(
                "Page introuvable",
                '<div class="panneau"><h2>Erreur 404</h2>Cette page n’existe pas sur le serveur de Julie.</div>',
            ),
            404,
        )

    def render_notebook(
        self, filepath: str, text: str, message: str, status: int = 200
    ) -> None:
        body = f"""
        <div class="panneau">
          <h2>Bloc-notes électronique de Julie</h2>
          <p>Conservez ici vos notes de service et vos pense-bêtes.</p>
          <p class="notice">{esc(message)}</p>
          <form method="post" action="/notebook">
            <label for="path"><b>Nom ou chemin du fichier</b></label><br>
            <input id="path" name="path" type="text" value="{esc(filepath)}" required>
            <p class="petit">Chemin relatif à <code>/home/app</code> ou chemin absolu situé dans ce dossier.</p>
            <label for="content"><b>Contenu du carnet</b></label><br>
            <textarea id="content" name="content" spellcheck="false">{esc(text)}</textarea><br><br>
            <button class="bouton" type="submit" name="action" value="read">Lire</button>
            <button class="bouton" type="submit" name="action" value="write">Enregistrer</button>
          </form>
          <p class="petit">Format texte UTF-8 - Taille maximale : 1 Mio - Les dossiers manquants sont créés automatiquement.</p>
        </div>
        <div class="panneau"><b>Astuce de Julie :</b> rangez vos documents dans des sous-dossiers pour les retrouver plus facilement.</div>
        """
        self.send_html(page("Bloc-notes", body), status)

    def do_POST(self) -> None:  # noqa: N802
        if urllib.parse.urlsplit(self.path).path != "/notebook":
            self.send_html(
                page("Page introuvable", '<div class="panneau">Page introuvable.</div>'),
                404,
            )
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_html(
                page("Erreur", '<div class="panneau">Requête invalide.</div>'),
                400,
            )
            return

        if length <= 0 or length > MAX_REQUEST_BYTES:
            self.send_html(
                page("Erreur", '<div class="panneau">Requête trop volumineuse ou vide.</div>'),
                413,
            )
            return

        raw = self.rfile.read(length)
        if len(raw) != length:
            self.send_html(
                page("Erreur", '<div class="panneau">Requête incomplète.</div>'),
                400,
            )
            return

        try:
            fields = urllib.parse.parse_qs(
                raw.decode("utf-8", errors="replace"),
                keep_blank_values=True,
                max_num_fields=8,
            )
        except ValueError:
            self.send_html(
                page("Erreur", '<div class="panneau">Trop de champs dans la requête.</div>'),
                400,
            )
            return

        filepath = fields.get("path", [""])[0]
        content = fields.get("content", [""])[0]
        action = fields.get("action", ["write"])[0]

        try:
            if action == "read":
                text = notebook_read(filepath)
                message = "Lecture effectuée."
            elif action == "write":
                written = notebook_write(filepath, content)
                text = content
                message = f"Enregistrement terminé : {written} octet(s) écrit(s)."
            else:
                raise NotebookError("Opération inconnue.")

            self.render_notebook(filepath, text, message)
        except NotebookError as exc:
            self.render_notebook(filepath, content, str(exc), 400)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), JulieHandler)
    print(
        f"[WEB] Intranet RH de Julie disponible sur http://{HOST}:{PORT}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
