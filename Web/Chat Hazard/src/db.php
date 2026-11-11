<?php
/**
 * SQLite storage. The database file is created and seeded on first use, so the
 * app runs straight out of the box with `php -S`.
 */

function db(): PDO
{
    static $pdo = null;
    if ($pdo !== null) {
        return $pdo;
    }

    $path = getenv('DB_PATH') ?: sys_get_temp_dir() . '/chathazard.db';

    $pdo = new PDO('sqlite:' . $path);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    $pdo->exec('PRAGMA journal_mode = WAL');
    $pdo->exec('PRAGMA busy_timeout = 5000');

    install($pdo);
    return $pdo;
}

function install(PDO $pdo): void
{
    $pdo->exec('
        CREATE TABLE IF NOT EXISTS users (
            username      TEXT PRIMARY KEY,
            email         TEXT NOT NULL,
            display_name  TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            reset_token   TEXT,
            reset_expires INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id       TEXT PRIMARY KEY,
            username TEXT,
            created  INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cats (
            slug  TEXT PRIMARY KEY,
            name  TEXT NOT NULL,
            image TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
            username TEXT NOT NULL,
            cat      TEXT NOT NULL,
            body     TEXT NOT NULL,
            PRIMARY KEY (username, cat)
        );
    ');

    if ($pdo->query('SELECT COUNT(*) AS n FROM cats')->fetch()['n'] == 0) {
        seed($pdo);
    }
}

function seed(PDO $pdo): void
{
    $cats = [
        ['neo',    'Neo',    'img/neo.jpg'],
        ['millie', 'Millie', 'img/millie.jpg'],
        ['bella',  'Bella',  'img/bella.jpg'],
        ['poppy',  'Poppy',  'img/poppy.jpg'],
        ['louie',  'Louie',  'img/louie.jpg'],
        ['smokey', 'Smokey', 'img/smokey.jpg'],
    ];
    $insert = $pdo->prepare('INSERT INTO cats (slug, name, image) VALUES (?, ?, ?)');
    foreach ($cats as $cat) {
        $insert->execute($cat);
    }

    // The admin password is drawn at random on every install: it is written
    // nowhere, and no one is meant to log in with it.
    $users = [
        ['admin', 'admin@chathazard.cat', 'Site admin', bin2hex(random_bytes(32))],
        ['leo',   'leo@example.com',      'Leo',        'kibble'],
        ['sam',   'sam@example.com',      'Sam',        'purr2026'],
    ];
    $insert = $pdo->prepare(
        'INSERT INTO users (username, email, display_name, password_hash) VALUES (?, ?, ?, ?)'
    );
    foreach ($users as [$username, $email, $display, $password]) {
        $insert->execute([$username, $email, $display, password_hash($password, PASSWORD_DEFAULT)]);
    }

    $flag = getenv('FLAG') ?: 'CYBN{test_flag}';
    $notes = [
        ['admin', 'poppy',  'Poppy knocked the router off the shelf again.'],
        ['admin', 'smokey', 'Smokey guards the server room door code: ' . $flag],
        ['admin', 'neo',    'Neo only accepts the blue blanket. Noted.'],
        ['leo',   'louie',  'Louie stares at me while I eat. Every single time.'],
        ['sam',   'bella',  'Bella sleeps eighteen hours a day. A role model.'],
    ];
    $insert = $pdo->prepare('INSERT INTO notes (username, cat, body) VALUES (?, ?, ?)');
    foreach ($notes as $note) {
        $insert->execute($note);
    }
}
