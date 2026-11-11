<?php
/** Ask for a recovery link. */

require_once __DIR__ . '/session.php';
require_once __DIR__ . '/mail.php';
require_once __DIR__ . '/layout.php';

$sid   = session_boot();
$user  = current_user($sid);
$sent  = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $who = trim($_POST['account'] ?? '');

    $query = db()->prepare('SELECT * FROM users WHERE username = ? OR email = ?');
    $query->execute([$who, $who]);
    $found = $query->fetch();

    if ($found) {
        send_recovery_email($found);
    }

    $sent = true;
}

page_top('Forgot password', $user);
?>

<div class="row justify-content-center">
  <div class="col-md-6 col-lg-5">
    <h1 class="h3 mb-3">Forgot your password?</h1>

<?php if ($sent): ?>
    <div class="alert alert-info">
      If that account exists, a recovery link is on its way to the address we
      have on file. The link is valid for 15 minutes.
    </div>
    <p class="mb-0">
      <a href="login.php">Back to sign in</a>
    </p>
<?php else: ?>
    <form method="post" class="card card-body">
      <div class="mb-3">
        <label class="form-label" for="account">Username or e-mail</label>
        <input class="form-control" type="text" id="account" name="account" required autofocus>
      </div>
      <button class="btn btn-primary" type="submit">Send the link</button>
    </form>
<?php endif; ?>
  </div>
</div>

<?php
page_bottom();
