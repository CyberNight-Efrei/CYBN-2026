<?php
require_once __DIR__ . '/session.php';

log_out(session_boot());

header('Location: index.php');
