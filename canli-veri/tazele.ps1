# Canli veri tazeleme. Gorev Zamanlayici bunu cagirir.
#   .\tazele.ps1 -Grup sik    -> piyasa + doviz            (15 dk)
#   .\tazele.ps1 -Grup saatlik -> hava + eczane            (60 dk)
#   .\tazele.ps1 -Grup gunluk  -> namaz + puan + vizyon    (gunde 1)
param([ValidateSet("sik","saatlik","gunluk")][string]$Grup = "sik")

$kok = Split-Path -Parent $MyInvocation.MyCommand.Path
$py  = Join-Path (Split-Path -Parent $kok) ".venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"

# Sik grupta SIRA onemli: doviz.py, piyasa.py'nin yazdigi dosyayi okuyor.
$betikler = switch ($Grup) {
  "sik"     { @("piyasa.py", "doviz.py") }
  "saatlik" { @("hava_durumu.py", "nobetci_eczane.py") }
  "gunluk"  { @("namaz_vakitleri.py", "puan_durumu.py", "vizyon_takvimi.py") }
}

$hata = 0
foreach ($b in $betikler) {
  $yol = Join-Path $kok $b
  if (-not (Test-Path $yol)) { Write-Output "ATLANDI (yok): $b"; continue }
  & $py $yol
  # 2 = kaynak dustu ama onceki dosya korundu; bu bir HATA DEGIL.
  if ($LASTEXITCODE -eq 1) { $hata = 1; Write-Output "HATA: $b veri uretemedi" }
}
exit $hata
