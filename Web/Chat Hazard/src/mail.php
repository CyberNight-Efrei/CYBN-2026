<?php
/**
 * Password recovery e-mails.
 *
 * There is no mail server here, so nothing actually leaves the machine: the
 * token is stored and the message is written to the error log.
 */

require_once __DIR__ . '/db.php';

const TOKEN_TTL = 900;

/**
 * Store a fresh recovery token for a user and return the message body.
 */
function send_recovery_email(array $user): string
{
    $alphabet = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $token = substr(str_shuffle($alphabet), 0, 16);

    db()->prepare('UPDATE users SET reset_token = ?, reset_expires = ? WHERE username = ?')
        ->execute([$token, time() + TOKEN_TTL, $user['username']]);

    $message = "Hi {$user['display_name']},\n\n"
             . "Use this link to choose a new password:\n"
             . "  /recovery.php?token={$token}\n\n"
             . "It expires in 15 minutes.\n";

    error_log("recovery e-mail sent to {$user['email']}");

    return $message;
}

/**
 * Look up a recovery token. Returns the user it belongs to, or null.
 */
function user_for_token(string $token): ?array
{
    if ($token === '') {
        return null;
    }

    $query = db()->prepare('SELECT * FROM users WHERE reset_token = ? AND reset_expires > ?');
    $query->execute([$token, time()]);

    return $query->fetch() ?: null;
}

/**
 * Set a new password and burn the token.
 */
function reset_password(string $username, string $password): void
{
    db()->prepare(
        'UPDATE users SET password_hash = ?, reset_token = NULL, reset_expires = 0
         WHERE username = ?'
    )->execute([password_hash($password, PASSWORD_DEFAULT), $username]);
}
