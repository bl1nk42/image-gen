param([string]$Home = "$env:USERPROFILE\.hermes", [switch]$Claude)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$args = @("$root\install.py", "--home", $Home)
if ($Claude) { $args += "--claude" }
py @args
