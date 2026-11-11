<?php
/** Shared page chrome. Bootstrap 5, served from vendor/. */

function h(?string $text): string
{
    return htmlspecialchars((string) $text, ENT_QUOTES, 'UTF-8');
}

function page_top(string $title, ?array $user): void
{ ?>
    <!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= h($title) ?> &middot; Chat Hazard</title>
    <link rel="stylesheet" href="vendor/bootstrap.min.css">
    </head>
    <body class="bg-body-tertiary">

    <nav class="navbar navbar-expand bg-dark" data-bs-theme="dark">
      <div class="container">
        <a class="navbar-brand" href="index.php">&#128049; Chat Hazard</a>
        <ul class="navbar-nav ms-auto align-items-center">
    <?php if ($user): ?>
          <li class="nav-item navbar-text me-3">Signed in as <strong><?= h($user['display_name']) ?></strong></li>
          <li class="nav-item"><a class="nav-link" href="logout.php">Sign out</a></li>
    <?php else: ?>
          <li class="nav-item"><a class="nav-link" href="login.php">Sign in</a></li>
    <?php endif; ?>
        </ul>
      </div>
    </nav>

    <main class="container py-4">
<?php }

function page_bottom(): void
{ ?>
    </main>

    <footer class="container py-4 text-center text-body-secondary border-top">
      Six cats, no supervision.
    </footer>
    </body>
    </html>
<?php }

function notice(?string $text, string $kind = 'info'): void
{
    if ($text !== null && $text !== '') {
        echo '<div class="alert alert-' . h($kind) . '">' . h($text) . "</div>\n";
    }
}
