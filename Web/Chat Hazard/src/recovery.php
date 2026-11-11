<?php
/** Choose a new password, using the token from the recovery link. */

require_once __DIR__ . '/session.php';
require_once __DIR__ . '/mail.php';
require_once __DIR__ . '/layout.php';

$sid   = session_boot();
$user  = current_user($sid);
$token = $_REQUEST['token'] ?? '';
$owner = user_for_token($token);
$error = null;
$done  = false;

if ($owner && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $password = $_POST['password'] ?? '';

    if (strlen($password) < 4) {
        $error = 'Pick a password of at least 4 characters.';
    } else {
        reset_password($owner['username'], $password);
        $done = true;
    }
}

page_top('Choose a new password', $user);
?>

<div class="row justify-content-center">
  <div class="col-md-6 col-lg-5">
    <h1 class="h3 mb-3">Choose a new password</h1>

<?php if ($done): ?>
    <div class="alert alert-success">
      Password updated. You can <a href="login.php" class="alert-link">sign in</a> now.
    </div>
<?php elseif (!$owner): ?>
    <div class="alert alert-danger">That recovery link is unknown or has expired.</div>
    <p class="mb-0"><a href="forgot.php">Ask for a new one</a></p>
<?php else: ?>
    <?php notice($error, 'danger'); ?>
    <p>Setting a new password for <strong><?= h($owner['username']) ?></strong>.</p>
    <form method="post" class="card card-body">
      <input type="hidden" name="token" value="<?= h($token) ?>">
      <div class="mb-3">
        <label class="form-label" for="password">New password</label>
        <input class="form-control" type="password" id="password" name="password"
               autocomplete="new-password" required autofocus>
      </div>
      <button class="btn btn-primary" type="submit">Save</button>
    </form>
<?php endif; ?>
  </div>
</div>

<?php
page_bottom();
