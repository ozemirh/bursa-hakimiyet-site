<#
    Yarim kalan arsivi tek dosyaya paketler; tarama baska bir makinede
    kaldigi yerden devam etsin diye.

    92 bin kucuk dosyayi USB'ye tek tek kopyalamak saatler surer, tek paket
    saniyeler. Paket acildiginda tarayici tamamlanmis haberleri atlar.

    Kullanim:
        .\paketle.ps1                                  # D:\bursa-hakimiyet-arsiv -> masaustu
        .\paketle.ps1 -Kok E:\arsiv -Hedef F:\devir.tar.gz

    Karsi makinede:
        tar -xzf devir.tar.gz -C D:\
        .\disa-aktarim\calistir.ps1
#>
[CmdletBinding()]
param(
    [string]$Kok,
    [string]$Hedef
)

$ErrorActionPreference = 'Stop'
function Yaz($mesaj, $renk = 'Gray') { Write-Host "  $mesaj" -ForegroundColor $renk }

Write-Host ''
Write-Host 'Arsiv paketleme - devir icin' -ForegroundColor Cyan
Write-Host ''

if (-not $Kok) { $Kok = $env:BH_ARSIV_KOK }
if (-not $Kok) { $Kok = 'D:\bursa-hakimiyet-arsiv' }
if (-not (Test-Path $Kok)) {
    Write-Host "HATA: arsiv bulunamadi ($Kok)" -ForegroundColor Red
    exit 1
}
$Kok = (Resolve-Path $Kok).Path

if (-not $Hedef) {
    $Hedef = Join-Path ([Environment]::GetFolderPath('Desktop')) 'bursa-arsiv-devir.tar.gz'
}

# -- tarama calisiyorsa paket tutarsiz olur --------------------------------
$calisan = Get-Process python -ErrorAction SilentlyContinue
if ($calisan) {
    Write-Host '  UYARI: Python sureci calisiyor. Tarama surerken paketlerseniz' -ForegroundColor Yellow
    Write-Host '         yarim yazilmis dosyalar pakete girebilir.' -ForegroundColor Yellow
    Write-Host ''
    $yanit = Read-Host '  Once taramayi durdurun. Yine de devam edilsin mi? (e/H)'
    if ($yanit -ne 'e') { exit 1 }
}

# -- ne paketleniyor -------------------------------------------------------
$ilerlemeDosya = Join-Path $Kok 'ilerleme.json'
if (Test-Path $ilerlemeDosya) {
    $i = Get-Content $ilerlemeDosya -Raw -Encoding UTF8 | ConvertFrom-Json
    Yaz "Ilerleme   : $($i.tamamlanan) / $($i.toplam_url) haber"
}
$veriSayi = (Get-ChildItem (Join-Path $Kok 'veri') -Recurse -File -ErrorAction SilentlyContinue).Count
Yaz "Veri       : $veriSayi dosya"
Yaz "Kaynak     : $Kok"
Yaz "Paket      : $Hedef"
Write-Host ''
Write-Host '  Paketleniyor - 92 bin dosya icin birkac dakika surebilir...' -ForegroundColor Cyan

# -- paketle ---------------------------------------------------------------
# tar surucu harfindeki iki noktayi uzak sunucu sanabiliyor; ust klasore gecip
# goreli ad vererek bundan kaciniyoruz.
$ustKlasor = Split-Path -Parent $Kok
$klasorAdi = Split-Path -Leaf $Kok
$tar = Join-Path $env:SystemRoot 'System32\tar.exe'
if (-not (Test-Path $tar)) { $tar = 'tar' }

$hedefKlasor = Split-Path -Parent $Hedef
if ($hedefKlasor -and -not (Test-Path $hedefKlasor)) {
    New-Item -ItemType Directory $hedefKlasor -Force | Out-Null
}

$basla = Get-Date
Push-Location $ustKlasor
try {
    & $tar -czf $Hedef $klasorAdi
    if ($LASTEXITCODE -ne 0) { throw "tar hata verdi (cikis kodu: $LASTEXITCODE)" }
}
finally {
    Pop-Location
}
$sure = [math]::Round(((Get-Date) - $basla).TotalMinutes, 1)

# -- ozet + dogrulama ------------------------------------------------------
$boyutMB = [math]::Round((Get-Item $Hedef).Length / 1MB, 0)
Write-Host ''
Yaz "Paket hazir: $boyutMB MB, $sure dakika" 'Green'

Write-Host ''
Write-Host '  Butunluk damgasi hesaplaniyor...' -ForegroundColor DarkGray
$ozet = (Get-FileHash $Hedef -Algorithm SHA256).Hash
"$ozet  $(Split-Path -Leaf $Hedef)" | Out-File "$Hedef.sha256" -Encoding ascii
Yaz "SHA256     : $($ozet.Substring(0,16))... ($(Split-Path -Leaf $Hedef).sha256 dosyasina yazildi)"

Write-Host ''
Write-Host '  Karsi makinede' -ForegroundColor Cyan
Write-Host "    tar -xzf $(Split-Path -Leaf $Hedef) -C D:\" -ForegroundColor White
Write-Host '    .\disa-aktarim\calistir.ps1' -ForegroundColor White
Write-Host ''
Write-Host '  Ilk turda "atlanan" sayisi yukaridaki haber sayisina esit olmali;' -ForegroundColor DarkGray
Write-Host '  esitse devir tamamdir, tarama kaldigi yerden surer.' -ForegroundColor DarkGray
Write-Host ''
