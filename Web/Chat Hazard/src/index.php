<?php
/** Home page: the cat gallery, plus your own private notes when signed in. */

require_once __DIR__ . '/session.php';
require_once __DIR__ . '/layout.php';

$sid  = session_boot();
$user = current_user($sid);

// Saving a note.
if ($user && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $cat  = $_POST['cat'] ?? '';
    $body = trim($_POST['note'] ?? '');

    if ($body === '') {
        db()->prepare('DELETE FROM notes WHERE username = ? AND cat = ?')
            ->execute([$user['username'], $cat]);
    } else {
        db()->prepare(
            'INSERT INTO notes (username, cat, body) VALUES (?, ?, ?)
             ON CONFLICT (username, cat) DO UPDATE SET body = excluded.body'
        )->execute([$user['username'], $cat, mb_substr($body, 0, 300)]);
    }

    header('Location: index.php');
    exit;
}

$cats = db()->query('SELECT * FROM cats ORDER BY name')->fetchAll();

$notes = [];
if ($user) {
    $query = db()->prepare('SELECT cat, body FROM notes WHERE username = ?');
    $query->execute([$user['username']]);
    foreach ($query->fetchAll() as $row) {
        $notes[$row['cat']] = $row['body'];
    }
}

page_top('The cats', $user);
?>

<h1 class="h3 mb-3">The cats</h1>

<?php if (!$user): ?>
  <p class="text-body-secondary">
    <a href="login.php">Sign in</a> to keep private notes on them.
    Notes are only ever shown to the account that wrote them.
  </p>
<?php else: ?>
  <p class="text-body-secondary">Your notes are private. Nobody else can read them.</p>
<?php endif; ?>

<div class="row row-cols-1 row-cols-sm-2 row-cols-lg-3 g-4">
<?php foreach ($cats as $cat): ?>
  <div class="col">
    <div class="card h-100">
      <img src="<?= h($cat['image']) ?>" class="card-img-top" alt="<?= h($cat['name']) ?>">
      <div class="card-body">
        <h2 class="h5 card-title"><?= h($cat['name']) ?></h2>
<?php if ($user): ?>
        <form method="post" class="input-group input-group-sm">
          <input type="hidden" name="cat" value="<?= h($cat['slug']) ?>">
          <input type="text" class="form-control" name="note" maxlength="300"
                 placeholder="Private note" value="<?= h($notes[$cat['slug']] ?? '') ?>">
          <button class="btn btn-outline-secondary" type="submit">Save</button>
        </form>
<?php endif; ?>
      </div>
    </div>
  </div>
<?php endforeach; ?>
</div>

<?php
page_bottom();
