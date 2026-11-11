<?php
/** Sign-in page. */

require_once __DIR__ . '/session.php';
require_once __DIR__ . '/layout.php';

$sid   = session_boot();
$user  = current_user($sid);
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    $query = db()->prepare('SELECT * FROM users WHERE username = ?');
    $query->execute([$username]);
    $found = $query->fetch();

    if ($found && password_verify($password, $found['password_hash'])) {
        log_in($sid, $found['username']);
        header('Location: index.php');
        exit;
    }

    $error = 'Wrong username or password.';
}

page_top('Sign in', $user);
?>

<div class="row justify-content-center">
  <div class="col-md-6 col-lg-5">
    <h1 class="h3 mb-3">Sign in</h1>

    <?php notice($error, 'danger'); ?>

    <form method="post" class="card card-body">
      <div class="mb-3">
        <label class="form-label" for="username">Username</label>
        <input class="form-control" type="text" id="username" name="username"
               autocomplete="username" required autofocus>
      </div>
      <div class="mb-3">
        <label class="form-label" for="password">Password</label>
        <input class="form-control" type="password" id="password" name="password"
               autocomplete="current-password" required>
      </div>
      <button class="btn btn-primary" type="submit">Sign in</button>
    </form>

    <p class="mt-3 mb-0"><a href="forgot.php">Forgot your password?</a></p>
  </div>
</div>

<?php
page_bottom();
