# Canli veri tazeleme. Gorev Zamanlayici bunu cagirir.
#   .\tazele.ps1 -Grup sik    -> piyasa + doviz            (15 dk)
#   .\tazele.ps1 -Grup saatlik -> hava + eczane            (60 dk)
#   .\tazele.ps1 -Grup gunluk  -> namaz + puan + vizyon    (gunde 1)
#   .\tazele.ps1 -Grup haber   -> eczane + gunun eczane haberi (gunde 1)
param([ValidateSet("sik","saatlik","gunluk","haber")][string]$Grup = "sik")

$kok = Split-Path -Parent $MyInvocation.MyCommand.Path
$py  = Join-Path (Split-Path -Parent $kok) ".venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"

# Sik grupta SIRA onemli: doviz.py, piyasa.py'nin yazdigi dosyayi okuyor.
$betikler = switch ($Grup) {
  "sik"     { @("piyasa.py", "doviz.py") }
  "saatlik" { @("hava_durumu.py", "nobetci_eczane.py") }
  "gunluk"  { @("namaz_vakitleri.py", "puan_durumu.py", "vizyon_takvimi.py") }
  # "haber" grubunda once liste tazelenir, SONRA haber yazilir; komut
  # asagida ayrica cagriliyor (URUN-PLANI.md 41).
  "haber"   { @("nobetci_eczane.py") }
}

$hata = 0
foreach ($b in $betikler) {
  $yol = Join-Path $kok $b
  if (-not (Test-Path $yol)) { Write-Output "ATLANDI (yok): $b"; continue }
  & $py $yol
  # 2 = kaynak dustu ama onceki dosya korundu; bu bir HATA DEGIL.
  if ($LASTEXITCODE -eq 1) { $hata = 1; Write-Output "HATA: $b veri uretemedi" }
}

# Gunun nobetci eczane haberi. Cekme betikleri siteden bagimsiz calisir
# ama BU adim Django'ya girer: kayit veritabanina yazilir. Sira
# baglayici - liste tazelenmeden haber yazilirsa dunun listesi
# yayimlanir. Komut kendi kapisini da tasiyor: bayat listeyi
# yayimlamiyor, ayni gun iki kez kosarsa ikinci kayit acmiyor.
if ($Grup -eq "haber") {
  $yonet = Join-Path (Split-Path -Parent $kok) "uygulama\manage.py"
  & $py $yonet eczane_haberi
  if ($LASTEXITCODE -ne 0) { $hata = 1; Write-Output "HATA: eczane haberi yayimlanmadi" }
}

exit $hata
