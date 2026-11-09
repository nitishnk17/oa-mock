# One-line install for Windows 10/11 (PowerShell):
#   irm https://raw.githubusercontent.com/rgabhi/oa-mock/main/scripts/install.ps1 | iex
# Makes a slim clone in .\oa-mock (the app + Flipkart's questions, ~4 MB; download more companies on the
# home page), then runs scripts\setup.ps1. $env:OA_DIR changes the folder; $env:OA_FULL = "1" clones every company.
$ErrorActionPreference = "Stop"
$Repo = if ($env:OA_REPO) { $env:OA_REPO } else { "https://github.com/rgabhi/oa-mock.git" }
$Dir = if ($env:OA_DIR) { $env:OA_DIR } else { "oa-mock" }
$Sample = "flipkart"
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

if (-not (Have "git")) {
  Write-Host "git is needed. Installing it..." -ForegroundColor White
  if (Have "winget") {
    winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
  }
  if (-not (Have "git")) { Write-Host "Couldn't install git. Get it from https://git-scm.com/download/win and run this again." -ForegroundColor Yellow; return }
}

$v = [regex]::Match((git --version), "(\d+)\.(\d+)")
$slim = ([int]$v.Groups[1].Value -gt 2) -or ([int]$v.Groups[1].Value -eq 2 -and [int]$v.Groups[2].Value -ge 27)
if ($env:OA_FULL -eq "1") { $slim = $false }

if (Test-Path (Join-Path $Dir ".git")) {
  Write-Host "$Dir already exists: updating it" -ForegroundColor White
  git -C $Dir pull --ff-only
} elseif (Test-Path $Dir) {
  Write-Host "$Dir exists and isn't an OA Mock clone. Set `$env:OA_DIR to another folder." -ForegroundColor Yellow; return
} elseif ($slim) {
  Write-Host "Downloading OA Mock (slim: the app + $Sample)" -ForegroundColor White
  git clone --filter=blob:none --sparse $Repo $Dir
  $dirs = git -C $Dir ls-tree -d --name-only HEAD | Where-Object { $_ -ne "data" }
  git -C $Dir sparse-checkout set --cone @dirs "data/$Sample"
} else {
  Write-Host "Downloading OA Mock (every company)" -ForegroundColor White
  git clone $Repo $Dir
}

Set-Location $Dir
Write-Host "Setting up in $(Get-Location)" -ForegroundColor White
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path (Get-Location) "scripts\setup.ps1")
