# Gelistirme sunucusu - Bursa Hakimiyet (19 Ekim 2026)
#
# Ayarlar artik fail-closed: BH_ORTAM verilmezse uygulama URETIM sayilir ve
# BH_GIZLI_ANAHTAR olmadan acilmaz. Bu betik gelistirme ortamini kurar ve
# sunucuyu baslatir:
#
#   .\gelistir.ps1                      # 8731'de runserver --noreload
#   .\gelistir.ps1 -Port 8743
#   .\gelistir.ps1 -Komut test          # manage.py test
#   .\gelistir.ps1 -Komut "check --deploy"
#   .\gelistir.ps1 -SaltOkunur          # veritabani salt okunur (olcum icin)
#
# Yerel ayar dosyasi: depo kokunde `.env` varsa (git'e GIRMEZ) icindeki
# BH_* satirlari once okunur; ortamda zaten tanimli degisken ezilmez.
# Ornek: dagitim/.env.ornek
#
# Gizli anahtar: verilmezse uygulama `uygulama/.yerel-gizli-anahtar`
# dosyasini bir kez uretir ve hep onu kullanir (git'e girmez).
param(
  [int]$Port = 8731,
  [string]$Komut = "",
  [switch]$SaltOkunur
)

$kok = Split-Path -Parent $MyInvocation.MyCommand.Path
$uygulama = Join-Path $kok "uygulama"

# Ana depo koku: git worktree'de .venv, veritabani ve canli veri oradadir.
# git yoksa ya da depo degilse sessizce gecilir (Stop'tan ONCE: Windows
# PowerShell 5.1 yerel komutun stderr'ini hata kaydina cevirir).
$ana = $null
try {
  $ortakGit = (& git -C $kok rev-parse --path-format=absolute --git-common-dir 2>$null)
  if ($LASTEXITCODE -eq 0 -and $ortakGit) { $ana = Split-Path -Parent $ortakGit }
} catch { $ana = $null }

$ErrorActionPreference = "Stop"

# Python: once bu depodaki .venv, yoksa ana deponunki.
$py = Join-Path $kok ".venv\Scripts\python.exe"
if (-not (Test-Path $py) -and $ana) { $py = Join-Path $ana ".venv\Scripts\python.exe" }
if (-not (Test-Path $py)) { throw "Python bulunamadi: once 'python -m venv .venv' ve 'pip install -r requirements-gelistirme.txt'" }

# .env (yerel, izlenmeyen) -> ortam
$envDosya = Join-Path $kok ".env"
if (Test-Path $envDosya) {
  foreach ($satir in Get-Content $envDosya -Encoding UTF8) {
    $s = $satir.Trim()
    if (-not $s -or $s.StartsWith("#") -or -not $s.Contains("=")) { continue }
    $ad, $deger = $s -split "=", 2
    $ad = $ad.Trim(); $deger = $deger.Trim().Trim('"').Trim("'")
    if ($ad -notlike "BH_*") { continue }
    if (-not [Environment]::GetEnvironmentVariable($ad)) {
      [Environment]::SetEnvironmentVariable($ad, $deger, "Process")
    }
  }
}

$env:BH_ORTAM = "gelistirme"
$env:PYTHONIOENCODING = "utf-8"
if (-not $env:BH_HATA_AYIKLA) { $env:BH_HATA_AYIKLA = "1" }

# Worktree'de veritabani ve canli veri ana depoda durur.
if (-not $env:BH_SQLITE_YOLU -and -not $env:BH_VERITABANI) {
  $vt = Join-Path $uygulama "db.sqlite3"
  if (-not (Test-Path $vt) -and $ana) { $vt = Join-Path $ana "uygulama\db.sqlite3" }
  $vt = $vt -replace "\\", "/"
  if ($SaltOkunur) { $env:BH_SQLITE_YOLU = "file:${vt}?mode=ro" } else { $env:BH_SQLITE_YOLU = $vt }
}
if (-not $env:BH_CANLI_VERI_KOK -and $ana -and -not (Test-Path (Join-Path $kok "canli-veri\veri"))) {
  $cv = Join-Path $ana "canli-veri\veri"
  if (Test-Path $cv) { $env:BH_CANLI_VERI_KOK = $cv }
}

Push-Location $uygulama
try {
  if ($Komut) {
    & $py manage.py @($Komut -split " ")
    exit $LASTEXITCODE
  }
  # Port dolu mu? (EKIP.md: acmadan once port kontrolu)
  $dolu = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if ($dolu) { throw "Port $Port dolu (PID $($dolu[0].OwningProcess)). Baska port: -Port 8743" }
  Write-Output "BH_ORTAM=gelistirme  http://127.0.0.1:$Port/  (Ctrl+C ile durdur)"
  & $py manage.py runserver "127.0.0.1:$Port" --noreload
  exit $LASTEXITCODE
} finally {
  Pop-Location
}
