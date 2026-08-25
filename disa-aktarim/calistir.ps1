<#
    bursahakimiyet.com.tr arsiv taramasini baslatir.

    Tarama 500 binin uzerinde haber ve ~112 GB gorsel indirdigi icin saatlerce
    surer; bu sarmal uc isi ustlenir:
      1. makineyi uyanik tutar (uyuyan laptop taramayi durduruyordu),
      2. hedef surucude yeterli yer var mi bakar,
      3. kosu duserse kaldigi yerden yeniden baslatir.

    Kullanim:
        .\calistir.ps1                       # kok: D:\bursa-hakimiyet-arsiv
        .\calistir.ps1 -Kok E:\arsiv
        .\calistir.ps1 -UykuAyariniYap       # guc planini da kalici olarak degistirir
        .\calistir.ps1 -GerekliGB 60         # disk esigini gevsetir

    Ctrl+C ile durdurulabilir; tekrar calistirinca kaldigi yerden devam eder.
#>
[CmdletBinding()]
param(
    [string]$Kok,
    [int]$GerekliGB = 130,
    [int]$EnFazlaYenidenBaslatma = 20,
    [switch]$UykuAyariniYap
)

$ErrorActionPreference = 'Stop'
$betik = Join-Path $PSScriptRoot 'site_arsivleyici.py'

function Yaz($mesaj, $renk = 'Gray') { Write-Host "  $mesaj" -ForegroundColor $renk }

Write-Host ''
Write-Host 'Bursa Hakimiyet - arsiv taramasi' -ForegroundColor Cyan
Write-Host ''

# -- 1. cikti koku ---------------------------------------------------------
if (-not $Kok) { $Kok = $env:BH_ARSIV_KOK }
if (-not $Kok) { $Kok = 'D:\bursa-hakimiyet-arsiv' }
Yaz "Cikti koku : $Kok"

# -- 2. python -------------------------------------------------------------
$py = $null
foreach ($aday in @('python', 'py')) {
    $bulunan = Get-Command $aday -ErrorAction SilentlyContinue
    if ($bulunan) { $py = $bulunan.Source; break }
}
if (-not $py) {
    Write-Host 'HATA: Python bulunamadi. python.org/downloads adresinden 3.10+ kurun' -ForegroundColor Red
    Write-Host '      ve kurulumda "Add python.exe to PATH" secenegini isaretleyin.' -ForegroundColor Red
    exit 1
}
$surum = & $py -c "import sys; print('%d.%d' % sys.version_info[:2])"
$parca = $surum.Split('.')
if ([int]$parca[0] -lt 3 -or ([int]$parca[0] -eq 3 -and [int]$parca[1] -lt 10)) {
    Write-Host "HATA: Python $surum bulundu, en az 3.10 gerekiyor." -ForegroundColor Red
    exit 1
}
Yaz "Python     : $surum ($py)"

if (-not (Test-Path $betik)) {
    Write-Host "HATA: site_arsivleyici.py bulunamadi ($betik)" -ForegroundColor Red
    Write-Host '      Depoyu eksiksiz klonlayin; betik arac\ayiklayici.py dosyasina da ihtiyac duyar.' -ForegroundColor Red
    exit 1
}

# -- 3. disk ---------------------------------------------------------------
try {
    $harf = (Split-Path -Qualifier $Kok).TrimEnd(':')
    $bosGB = [math]::Round((Get-PSDrive -Name $harf).Free / 1GB, 1)
    if ($bosGB -lt $GerekliGB) {
        Yaz "Disk       : ${harf}: surucusunde $bosGB GB bos - $GerekliGB GB onerilir" 'Yellow'
        Write-Host ''
        Write-Host "  UYARI: Gorsellerle birlikte arsiv ~115 GB tutuyor. Betik, surucude" -ForegroundColor Yellow
        Write-Host "         10 GB kalinca kendini durdurur; yer acin ya da -Kok ile baska" -ForegroundColor Yellow
        Write-Host "         bir surucu verin." -ForegroundColor Yellow
        Write-Host ''
        $yanit = Read-Host '  Yine de devam edilsin mi? (e/H)'
        if ($yanit -ne 'e') { exit 1 }
    }
    else {
        Yaz "Disk       : ${harf}: surucusunde $bosGB GB bos" 'Green'
    }
}
catch {
    Yaz "Disk       : olculemedi ($Kok) - atlaniyor" 'Yellow'
}

# -- 4. uyku ---------------------------------------------------------------
if ($UykuAyariniYap) {
    try {
        powercfg /change standby-timeout-ac 0
        powercfg /change hibernate-timeout-ac 0
        powercfg /change monitor-timeout-ac 15
        Yaz 'Guc plani  : uyku kapatildi (fise takiliyken)' 'Green'
    }
    catch {
        Yaz 'Guc plani  : degistirilemedi - PowerShell.i yonetici olarak calistirin' 'Yellow'
    }
}

$imza = @'
[DllImport("kernel32.dll", SetLastError = true)]
public static extern uint SetThreadExecutionState(uint esFlags);
'@
$uyanik = $false
try {
    $Uyku = Add-Type -MemberDefinition $imza -Name 'Uyku' -Namespace 'BH' -PassThru
    # ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001)
    [void]$Uyku::SetThreadExecutionState([uint32]2147483649)
    $uyanik = $true
    Yaz 'Uyku       : bu pencere acikken sistem uyumayacak' 'Green'
}
catch {
    Yaz 'Uyku       : engellenemedi - guc ayarlarini elle yapin' 'Yellow'
}

Write-Host ''
Write-Host '  NOT: Kapak kapandiginda laptop yine uyuyabilir. Denetim Masasi >' -ForegroundColor DarkGray
Write-Host '       Guc Secenekleri > "Kapagi kapatmanin yapacagi islem" > "Hicbir sey".' -ForegroundColor DarkGray
Write-Host ''
Write-Host '  Tarama basliyor. Durdurmak icin Ctrl+C - ilerleme kaybolmaz.' -ForegroundColor Cyan
Write-Host ''

# -- 5. kosu + dustugunde yeniden baslatma ------------------------------------
$deneme = 0
$hizliDusus = 0
$baslangic = Get-Date
try {
    while ($true) {
        $turBasi = Get-Date
        & $py $betik --kok $Kok
        $kod = $LASTEXITCODE
        $surdu = ((Get-Date) - $turBasi).TotalSeconds

        if ($kod -eq 0) {
            Write-Host ''
            Write-Host '  Kosu normal sonlandi.' -ForegroundColor Green
            break
        }

        # Saniyeler icinde dusuyorsa sorun geciciligi degil kurulumu ilgilendirir
        # (eksik dosya, bozuk adres listesi, yol hatasi); 20 kez denemenin anlami yok.
        if ($surdu -lt 30) {
            $hizliDusus++
            if ($hizliDusus -ge 3) {
                Write-Host ''
                Write-Host "  Kosu $hizliDusus kez aciliste dustu (cikis kodu: $kod)." -ForegroundColor Red
                Write-Host '  Bu gecici bir ag hatasi degil; yukaridaki Python hatasini okuyun.' -ForegroundColor Red
                break
            }
        }
        else {
            $hizliDusus = 0
        }

        $deneme++
        if ($deneme -ge $EnFazlaYenidenBaslatma) {
            Write-Host ''
            Write-Host "  $deneme kez yeniden baslatildi, hala dusuyor (son cikis kodu: $kod)." -ForegroundColor Red
            Write-Host "  $Kok\log.txt ve basarisiz.txt dosyalarina bakin." -ForegroundColor Red
            break
        }

        Write-Host ''
        Write-Host "  Kosu dustu (cikis kodu: $kod). 60 sn sonra $deneme. kez yeniden baslatiliyor..." -ForegroundColor Yellow
        Write-Host ''
        Start-Sleep -Seconds 60
    }
}
finally {
    if ($uyanik) {
        # ES_CONTINUOUS: uyku engelini birak
        [void]$Uyku::SetThreadExecutionState([uint32]2147483648)
    }
}

# -- 6. ozet ---------------------------------------------------------------
$ilerlemeDosya = Join-Path $Kok 'ilerleme.json'
if (Test-Path $ilerlemeDosya) {
    $i = Get-Content $ilerlemeDosya -Raw -Encoding UTF8 | ConvertFrom-Json
    $yuzde = [math]::Round(100 * $i.tamamlanan / [math]::Max(1, $i.toplam_url), 1)
    Write-Host ''
    Write-Host '  Son durum' -ForegroundColor Cyan
    Yaz "tamamlanan : $($i.tamamlanan) / $($i.toplam_url)  (%$yuzde)"
    Yaz "basarisiz  : $($i.basarisiz)"
    Yaz "yeniden baslatma sayisi: $deneme"
    Yaz "gecen sure : $([math]::Round(((Get-Date) - $baslangic).TotalHours, 1)) saat (bu oturum)"
}
Write-Host ''
