# OA Mock setup for Windows 10/11 (PowerShell).
#   Double-click scripts\setup.bat, or run:  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
#   -NoJava   skip the JDK
#   -NoStart  set up only, don't start the runner
#   -NoCommand  don't add the oa-mock command
#   -Only cpp set up just one language (python, cpp or java); implies -NoStart
#             (the app runs this when you install a language from the language menu; Windows shows UAC if an installer needs it)
param([switch]$NoJava, [switch]$NoStart, [switch]$NoCommand, [string]$Only = "")
if ($Only -and @("python", "cpp", "java") -notcontains $Only) { Write-Host "-Only needs python, cpp or java"; exit 2 }
if ($Only) { $NoStart = $true }
function Want($l) { return (-not $Only) -or ($Only -eq $l) }
$result = 0
$ErrorActionPreference = "Continue"
$AppDir = Split-Path -Parent $PSScriptRoot   # the app's folder (this script is in scripts\)
Set-Location -Path $AppDir

function Ok($m)   { Write-Host "  [ok] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  [!]  $m" -ForegroundColor Yellow }
function Step($m) { Write-Host "`n$m" -ForegroundColor White }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
  $links = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
  if (Test-Path $links) { $env:Path += ";$links" }
}
function Winget-Install($id) {
  if (-not (Have "winget")) { return $false }
  winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements
  Refresh-Path
  return $true
}
function Find-Python {
  foreach ($c in @("py", "python", "python3")) {
    if (Have $c) {
      $args0 = @(); if ($c -eq "py") { $args0 = @("-3") }
      try {
        & $c @args0 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return ,(@($c) + $args0) }
      } catch {}
    }
  }
  return $null
}

Write-Host "OA Mock setup (Windows)"
if (-not (Have "winget")) { Warn "winget isn't available, so missing tools can't be installed automatically. Install 'App Installer' from the Microsoft Store to get it." }

# ---------- Python ----------
if ((Want "python") -or (-not $NoStart)) {
Step "1/3 Python 3.8+"
$py = Find-Python
if (-not $py) {
  Warn "Python 3.8+ not found. Installing with winget..."
  Winget-Install "Python.Python.3.12" | Out-Null
  $py = Find-Python
}
if (-not $py) { Warn "Install Python from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run setup again."; Read-Host "Press Enter to exit"; exit 1 }
$pyExe = $py[0]; $pyArgs = @(); if ($py.Count -gt 1) { $pyArgs = $py[1..($py.Count - 1)] }
Ok ((& $pyExe @pyArgs --version 2>&1) | Out-String).Trim()
}

# ---------- C++ ----------
if (Want "cpp") {
Step "2/3 C++ compiler (g++ for C++17 answers)"
function Gcc-Major {
  if (-not (Have "g++")) { return 0 }
  try { $v = (& g++ -dumpversion 2>$null | Out-String).Trim(); return [int]($v.Split(".")[0]) } catch { return 0 }
}
$gccMajor = Gcc-Major
if ($gccMajor -eq 0) {
  Warn "g++ not found. Installing MinGW-w64 GCC (WinLibs) with winget..."
  Winget-Install "BrechtSanders.WinLibs.POSIX.UCRT" | Out-Null
} elseif ($gccMajor -lt 10) {
  Warn "Found an old g++ (GCC $gccMajor, often the 2018 MinGW 8.1 installer). Its C++17 headers are buggy. Installing a current GCC (WinLibs) alongside it..."
  Winget-Install "BrechtSanders.WinLibs.POSIX.UCRT" | Out-Null
  Ok "The mock picks the newest GCC automatically, even if the old one comes first on PATH."
}
if (Have "g++") { Ok ((& g++ --version | Select-Object -First 1) | Out-String).Trim() }
else { Warn "No g++. Install MinGW-w64 (https://winlibs.com) and add its bin folder to PATH. Python and JavaScript answers still work."; $result = 1 }
}

# ---------- Java ----------
if (Want "java") {
Step "3/3 Java JDK (for Java answers)"
if (Have "javac") { Ok ((& javac -version 2>&1 | Select-Object -Last 1) | Out-String).Trim() }
elseif ($NoJava) { Warn "Skipped (-NoJava). C++, Python and JavaScript still work." }
else {
  Warn "No JDK found. Installing Temurin 21 with winget..."
  Winget-Install "EclipseAdoptium.Temurin.21.JDK" | Out-Null
  if (Have "javac") { Ok ((& javac -version 2>&1 | Select-Object -Last 1) | Out-String).Trim() }
  else { Warn "No JDK yet. If it just installed, open a new window and run setup again. Everything else works."; $result = 1 }
}
}
if ($Only) { exit $result }

# ---------- the oa-mock command ----------
# WindowsApps is on every user's PATH, so a small .cmd there works from any folder (in new windows).
if (-not $NoCommand) {
  Step "The oa-mock command"
  $apps = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
  try {
    $cmd = "@echo off`r`nrem Starts OA Mock from any folder. Made by scripts\setup.ps1; run it again if you move the app.`r`n" +
           "if not exist `"$AppDir\start.bat`" (echo OA Mock isn't in $AppDir any more. Run scripts\setup.bat in its new folder.& exit /b 1)`r`n" +
           "call `"$AppDir\start.bat`" %*`r`n"
    Set-Content -Path (Join-Path $apps "oa-mock.cmd") -Value $cmd -Encoding ASCII -NoNewline -ErrorAction Stop
    Ok "Type oa-mock in a new terminal window to start the mock."
  } catch { Warn "Couldn't add the oa-mock command. Double-click start.bat instead." }
}

Step "Done"
Ok "Start the mock any time: double-click start.bat, or type oa-mock in a new terminal (stop it with Ctrl+C)."
Ok "If a compiler was just installed and isn't detected, close this window and open a new one."

if (-not $NoStart) {
  Write-Host ""
  & $pyExe @pyArgs (Join-Path "app" "run.py")
}
