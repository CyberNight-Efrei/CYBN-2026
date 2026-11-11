<?php
/**
 * Sessions.
 *
 * Every visitor without a valid session gets a new one, and its id is handed
 * back in the `sid` cookie.
 */

require_once __DIR__ . '/db.php';

const SESSION_COOKIE = 'sid';
const SESSION_TTL    = 3600;

/**
 * Resume the session named by the cookie, or open a new one.
 * Must be called before any output, because it may set a cookie.
 */
function session_boot(): string
{
    $cookie = $_COOKIE[SESSION_COOKIE] ?? '';

    if (ctype_digit($cookie)) {
        $found = db()->prepare('SELECT id FROM sessions WHERE id = ? AND created > ?');
        $found->execute([$cookie, time() - SESSION_TTL]);
        if ($found->fetch()) {
            return $cookie;
        }
    }

    // seed the random number generator
    mt_srand((int) ((float) microtime() * 1000000));

    $id = (string) mt_rand(1000000000, 9999999999);

    db()->prepare('INSERT INTO sessions (id, username, created) VALUES (?, NULL, ?)')
        ->execute([$id, time()]);

    setcookie(SESSION_COOKIE, $id, ['path' => '/', 'httponly' => true, 'samesite' => 'Lax']);

    return $id;
}

function current_user(string $sid): ?array
{
    $query = db()->prepare(
        'SELECT users.* FROM sessions
         JOIN users ON users.username = sessions.username
         WHERE sessions.id = ?'
    );
    $query->execute([$sid]);

    return $query->fetch() ?: null;
}

function log_in(string $sid, string $username): void
{
    db()->prepare('UPDATE sessions SET username = ? WHERE id = ?')->execute([$username, $sid]);
}

function log_out(string $sid): void
{
    db()->prepare('DELETE FROM sessions WHERE id = ?')->execute([$sid]);
}
