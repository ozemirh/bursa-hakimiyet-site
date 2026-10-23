<#
    Arsiv taramasi bu makinede neden yavas? - olcum betigi.

    Tarama CPU'ya degil ag gecikmesine ve disk yazma hizina bagli calisir:
    on is parcacigi, her sayfa icin yeni bir TCP+TLS baglantisi acar. Yani
    "daha guclu laptop" tek basina hicbir sey hizlandirmaz; asagidaki yedi
    olcumden biri yavasligi acikca gosterir.

    Kullanim:
        .\tani.ps1                    # kok: D:\bursa-hakimiyet-arsiv
        .\tani.ps1 -Kok E:\arsiv
        .\tani.ps1 -OrnekSayisi 40    # ag olcumunde daha cok sayfa dener

    Hicbir seyi degistirmez, taramayi baslatmaz. Sadece olcer ve yazar.
    Iki makinede de calistirip ciktiyi yan yana koyun.
#>
[CmdletBinding()]
param(
    [string]$Kok,
    [int]$OrnekSayisi = 20
)

$ErrorActionPreference = 'Continue'

# Bu depoyu ureten laptopta olculen deger; karsilastirma tabani.
$TABAN_URLS  = 6.2    # url/sn ortalama (93.950 url / 15.115 sn)
$TABAN_GECIK = 1.6    # sn - sayfa basina toplam istek suresi

function Bas($baslik) {
    Write-Host ''
    Write-Host "  $baslik" -ForegroundColor Cyan
    Write-Host ('  ' + ('-' * $baslik.Length)) -ForegroundColor DarkGray
}
function Yaz($etiket, $deger, $renk = 'Gray') {
    Write-Host ("    {0,-22} {1}" -f $etiket, $deger) -ForegroundColor $renk
}

$bulgular = New-Object System.Collections.Generic.List[string]
function Bulgu($metin) { $bulgular.Add($metin) | Out-Null }

if (-not $Kok) { $Kok = $env:BH_ARSIV_KOK }
if (-not $Kok) { $Kok = 'D:\bursa-hakimiyet-arsiv' }

Write-Host ''
Write-Host 'Bursa Hakimiyet - tarama hizi tanisi' -ForegroundColor Cyan
Write-Host "  cikti koku: $Kok" -ForegroundColor DarkGray

# -- 1. gercek hiz (log.txt) ------------------------------------------------
Bas '1. Gercek hiz - log.txt'
$logDosya = Join-Path $Kok 'log.txt'
if (Test-Path $logDosya) {
    $satirlar = @(Get-Content $logDosya -Tail 400 | Where-Object { $_ -match '^\[(.+?)\] \[(\d+)/(\d+)\]' })
    if ($satirlar.Count -ge 2) {
        $ilk = $satirlar[0]; $son = $satirlar[-1]
        $null = $ilk -match '^\[(.+?)\] \[(\d+)/(\d+)\]'
        $t1 = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm:ss', $null); $i1 = [int]$matches[2]
        $null = $son -match '^\[(.+?)\] \[(\d+)/(\d+)\]'
        $t2 = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm:ss', $null); $i2 = [int]$matches[2]; $toplam = [int]$matches[3]
        $sn = ($t2 - $t1).TotalSeconds
        if ($sn -gt 0) {
            $hiz = [math]::Round(($i2 - $i1) / $sn, 2)
            $kalanSaat = [math]::Round(($toplam - $i2) / [math]::Max($hiz, 0.01) / 3600, 1)
            $renk = 'Green'; if ($hiz -lt $TABAN_URLS * 0.6) { $renk = 'Red' }
            Yaz 'son olculen hiz' "$hiz url/sn  (taban: $TABAN_URLS url/sn)" $renk
            Yaz 'ilerleme' "$i2 / $toplam"
            Yaz 'bu hizla kalan sure' "$kalanSaat saat"
            if ($hiz -lt $TABAN_URLS * 0.6) { Bulgu "Hiz tabanin altinda ($hiz vs $TABAN_URLS url/sn) - asagidaki olcumlere bakin." }
        }
    }
    else { Yaz 'log.txt' 'ilerleme satiri yok (tarama daha yeni baslamis olabilir)' 'Yellow' }

    $r429 = @(Select-String -Path $logDosya -Pattern 'HTTP (429|403)' -AllMatches).Count
    $renk = 'Gray'; if ($r429 -gt 20) { $renk = 'Red' }
    Yaz 'HTTP 429/403 (kisitlama)' $r429 $renk
    if ($r429 -gt 20) { Bulgu "Sunucu bu IP'yi kisitliyor ($r429 kez 429/403). Her kisitlama 5-15 sn uyku demek. Baska ag/IP deneyin ya da eszamanliligi dusurun." }
}
else { Yaz 'log.txt' 'bulunamadi - tarama bu kokte hic calismamis' 'Yellow' }

# -- 2. sistem ve guc -------------------------------------------------------
Bas '2. Sistem ve guc'
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
Yaz 'islemci' "$($cpu.Name.Trim())  ($($cpu.NumberOfLogicalProcessors) mantiksal)"
Yaz 'bos RAM' ("{0} GB / {1} GB" -f [math]::Round($os.FreePhysicalMemory/1MB,1), [math]::Round($os.TotalVisibleMemorySize/1MB,1))
$pil = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pil) {
    $fise = ($pil.BatteryStatus -eq 2)
    if ($fise) { Yaz 'guc kaynagi' 'fise takili' 'Green' }
    else {
        Yaz 'guc kaynagi' "PIL ($($pil.EstimatedChargeRemaining)%)" 'Red'
        Bulgu 'Laptop pilde. Windows pilde Wi-Fi ve diski agresif kisiyor - fise takin.'
    }
}
$plan = (powercfg /getactivescheme) -replace '.*\((.+)\).*', '$1'
if ($plan -match 'Tasarruf|Saver|Dengeli|Balanced') {
    Yaz 'guc plani' $plan 'Yellow'
    Bulgu "Guc plani '$plan'. Yuksek Performansa alin: powercfg /setactive SCHEME_MIN"
}
else { Yaz 'guc plani' $plan }

# -- 3. hedef disk ----------------------------------------------------------
Bas '3. Hedef disk'
$harf = ''
try {
    $harf = (Split-Path -Qualifier $Kok).TrimEnd(':')
    $bolum = Get-Partition -DriveLetter $harf -ErrorAction Stop
    $disk = Get-Disk -Number $bolum.DiskNumber
    $fiziksel = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq [string]$bolum.DiskNumber } | Select-Object -First 1
    $ortam = 'bilinmiyor'; if ($fiziksel) { $ortam = $fiziksel.MediaType }
    Yaz 'surucu' "${harf}: -> disk $($bolum.DiskNumber)"
    if ($ortam -eq 'HDD') {
        Yaz 'ortam turu' $ortam 'Red'
        Bulgu 'Hedef surucu HDD (donen disk). 500 bin kucuk dosya HDD uzerinde SSD ye gore 5-20 kat yavas yazilir - en olasi sebep bu.'
    }
    else { Yaz 'ortam turu' $ortam 'Green' }
    if ($disk.BusType -match 'USB') {
        Yaz 'baglanti' $disk.BusType 'Red'
        Bulgu 'Hedef surucu USB uzerinden bagli. Kucuk dosya yaziminda USB dahili SSD ye gore cok yavas - dahili bir surucuye alin.'
    }
    else { Yaz 'baglanti' $disk.BusType }
}
catch { Yaz 'surucu' "olculemedi ($Kok) - ag surucusu ya da eslenmis yol olabilir" 'Yellow' }

if ($harf) {
    $k8 = fsutil 8dot3name query "${harf}:"
    if ($k8 -match 'disabled|devre d') { Yaz '8.3 ad uretimi' 'kapali (iyi)' 'Green' }
    elseif ($k8) { Yaz '8.3 ad uretimi' 'ACIK - kalabalik klasorde dosya yaratmayi yavaslatir' 'Yellow' }
}

# -- 4. guvenlik yazilimi ---------------------------------------------------
Bas '4. Guvenlik yazilimi'
$av = @(Get-CimInstance -Namespace 'root/SecurityCenter2' -ClassName AntiVirusProduct -ErrorAction SilentlyContinue)
foreach ($a in $av) {
    if ($a.displayName -notmatch 'Defender') {
        Yaz 'antivirus' $a.displayName 'Red'
        Bulgu "$($a.displayName) kurulu. Ucuncu parti antivirusler HTTPS trafigini araya girip cozuyor - 500 bin TLS el sikismasinin her birine gecikme ekler. Tarama suresince duraklatin ya da $Kok klasorunu ve python.exe yi disarida birakin."
    }
    else { Yaz 'antivirus' $a.displayName }
}
try {
    $mp = Get-MpComputerStatus -ErrorAction Stop
    if ($mp.RealTimeProtectionEnabled) { Yaz 'Defender gercek zamanli' 'ACIK' 'Yellow' } else { Yaz 'Defender gercek zamanli' 'kapali' 'Green' }
    $kapsiyor = $false
    foreach ($h in (Get-MpPreference).ExclusionPath) { if ($Kok -like "$h*") { $kapsiyor = $true } }
    if ($kapsiyor) { Yaz 'klasor haric tutulmus' 'evet' 'Green' } else { Yaz 'klasor haric tutulmus' 'HAYIR' 'Yellow' }
    if ($mp.RealTimeProtectionEnabled -and -not $kapsiyor) {
        Bulgu "Defender $Kok klasorunu her yazilan dosyada tariyor (milyonlarca kucuk dosya). Yonetici PowerShell'de: Add-MpPreference -ExclusionPath '$Kok'"
    }
}
catch { Yaz 'Defender' 'sorgulanamadi (ucuncu parti AV devralmis olabilir)' 'Yellow' }

# -- 5. ag ------------------------------------------------------------------
Bas '5. Ag baglantisi'
$net = @(Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and -not $_.Virtual })
foreach ($n in $net) {
    if ($n.InterfaceDescription -match 'Wi-?Fi|Wireless|802\.11') { Yaz 'baglanti' "$($n.Name) - $($n.LinkSpeed)" 'Yellow' }
    else { Yaz 'baglanti' "$($n.Name) - $($n.LinkSpeed)" 'Green' }
}
$wifi = @($net | Where-Object { $_.InterfaceDescription -match 'Wi-?Fi|Wireless|802\.11' })
if ($wifi.Count -gt 0) {
    $detay = netsh wlan show interfaces
    foreach ($s in @('Sinyal', 'Signal', 'Radyo', 'Radio type', 'Kanal', 'Channel')) {
        $sat = $detay | Where-Object { $_ -match "^\s*$s.*:" } | Select-Object -First 1
        if ($sat) { Yaz 'wifi' $sat.Trim() }
    }
    Bulgu 'Baglanti Wi-Fi. Mumkunse kabloya (Ethernet) alin: gecikme yariya iner, hiz dogrudan gecikmeye bagli.'
    try {
        $pm = Get-NetAdapterPowerManagement -Name $wifi[0].Name -ErrorAction Stop
        if ($pm.AllowComputerToTurnOffDevice -eq 'Enabled') {
            Yaz 'wifi guc tasarrufu' 'ACIK' 'Red'
            Bulgu 'Wi-Fi adaptorunde "bilgisayarin bu aygiti kapatmasina izin ver" acik - uzun taramalarda hiz dusurur. Aygit Yoneticisi > adaptor > Guc Yonetimi.'
        }
    } catch { }
}
$vpn = @(Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.InterfaceDescription -match 'VPN|TAP-|WireGuard|OpenVPN|Tunnel' })
if ($vpn.Count -gt 0) {
    Yaz 'VPN' ($vpn.Name -join ', ') 'Red'
    Bulgu 'Etkin bir VPN/tunel adaptoru var. Her istek tunelden gecerse gecikme katlanir - tarama suresince kapatin.'
}

# Ilk cozumleme onbellegi doldurur; olculecek olan onbellekli hal (tarama da oyle calisir).
Resolve-DnsName 'www.bursahakimiyet.com.tr' -Type A -ErrorAction SilentlyContinue | Out-Null
$dnsSure = Measure-Command { Resolve-DnsName 'www.bursahakimiyet.com.tr' -Type A -ErrorAction SilentlyContinue | Out-Null }
if ($dnsSure.TotalMilliseconds -gt 300) {
    Yaz 'DNS cozumleme' ("{0} ms" -f [math]::Round($dnsSure.TotalMilliseconds)) 'Red'
    Bulgu 'DNS cozumlemesi yavas. Adaptor DNS ini 1.1.1.1 / 8.8.8.8 yapmayi deneyin.'
}
else { Yaz 'DNS cozumleme' ("{0} ms" -f [math]::Round($dnsSure.TotalMilliseconds)) }
$aaaa = @(Resolve-DnsName 'www.bursahakimiyet.com.tr' -Type AAAA -ErrorAction SilentlyContinue | Where-Object { $_.QueryType -eq 'AAAA' })
if ($aaaa.Count -gt 0) { Yaz 'IPv6 (AAAA) kaydi' 'var' 'Yellow' } else { Yaz 'IPv6 (AAAA) kaydi' 'yok (iyi)' 'Green' }

# -- 6. ag olcumu: gercek sayfa istegi --------------------------------------
Bas "6. Ag olcumu - $OrnekSayisi sayfa"
$py = $null
foreach ($aday in @('python', 'py')) {
    $bulunan = Get-Command $aday -ErrorAction SilentlyContinue
    if ($bulunan) { $py = $bulunan.Source; break }
}
if (-not $py) { Yaz 'python' 'bulunamadi - ag olcumu atlandi' 'Yellow' }
else {
    $urlDosya = Join-Path $env:TEMP 'bh-tani-urller.txt'
    $liste = Join-Path $Kok 'tum-urller.jsonl'
    if (Test-Path $liste) {
        Get-Content $liste -TotalCount ($OrnekSayisi * 40) |
            Where-Object { $_ } |
            ForEach-Object { (ConvertFrom-Json $_).url } |
            Get-Random -Count $OrnekSayisi |
            Set-Content $urlDosya -Encoding UTF8
    }
    else {
        1..$OrnekSayisi | ForEach-Object { 'https://www.bursahakimiyet.com.tr/' } | Set-Content $urlDosya -Encoding UTF8
        Yaz 'not' 'tum-urller.jsonl yok - anasayfa olculuyor' 'Yellow'
    }

    # Sayfa istegi gecikmeye, gorsel indirme bant genisligine bagli. Tarama
    # suresinin buyuk kismi gorsellerde geciyor (~112 GB), o yuzden ikisi de
    # ayri ayri olculuyor.
    $probe = @'
import re, socket, ssl, statistics, sys, time, urllib.request
from urllib.parse import urlparse
urls = [s.strip() for s in open(sys.argv[1], encoding="utf-8-sig") if s.strip()]
dns, tls, tam, boyut = [], [], [], []
gorsel_adaylari = []
basli = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124 Safari/537.36",
         "Accept-Language": "tr,en;q=0.8"}
GORSEL = re.compile(r'https?://[^"\']+/static/\d{4}/\d{2}/\d{2}/[^"\']+?\.(?:jpe?g|png|webp)', re.I)
for u in urls:
    host = urlparse(u).hostname
    try:
        t = time.perf_counter(); socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP); dns.append(time.perf_counter() - t)
        t = time.perf_counter()
        ham = socket.create_connection((host, 443), timeout=30)
        s = ssl.create_default_context().wrap_socket(ham, server_hostname=host)
        tls.append(time.perf_counter() - t); s.close()
        t = time.perf_counter()
        with urllib.request.urlopen(urllib.request.Request(u, headers=basli), timeout=30) as y:
            veri = y.read()
        tam.append(time.perf_counter() - t); boyut.append(len(veri))
        for g in GORSEL.findall(veri.decode("utf-8", "replace")):
            if g not in gorsel_adaylari:
                gorsel_adaylari.append(g)
    except Exception as e:
        print("    HATA %s -> %s" % (u[:60], e))

def orta(x): return statistics.median(x) if x else 0.0
print("OLCUM dns=%.0f tls=%.0f tam=%.2f boyut=%.0f n=%d" % (
    orta(dns) * 1000, orta(tls) * 1000, orta(tam),
    (sum(boyut) / len(boyut) / 1024) if boyut else 0, len(tam)))
if tam:
    print("TAVAN %.1f" % (10.0 / orta(tam)))

g_sure, g_boyut = [], []
for g in gorsel_adaylari[:8]:
    try:
        t = time.perf_counter()
        with urllib.request.urlopen(urllib.request.Request(g, headers=basli), timeout=30) as y:
            b = y.read()
        g_sure.append(time.perf_counter() - t); g_boyut.append(len(b))
    except Exception:
        pass
if g_sure:
    print("GORSEL sure=%.2f ort=%.0f n=%d" % (
        orta(g_sure), sum(g_boyut) / len(g_boyut) / 1024, len(g_sure)))
'@
    $probeDosya = Join-Path $env:TEMP 'bh-tani-probe.py'
    Set-Content -Path $probeDosya -Value $probe -Encoding UTF8
    $cikti = & $py $probeDosya $urlDosya
    foreach ($s in $cikti) {
        if ($s -match '^OLCUM dns=(\S+) tls=(\S+) tam=(\S+) boyut=(\S+) n=(\d+)') {
            $mDns = $matches[1]; $mTls = [double]$matches[2]; $mTam = [double]$matches[3]; $mBoyut = $matches[4]
            $sayfaSure = $mTam
            Yaz 'DNS (ortanca)' "$mDns ms"
            if ($mTls -gt 400) {
                Yaz 'TCP+TLS (ortanca)' "$mTls ms" 'Red'
                Bulgu 'TLS el sikismasi cok uzun suruyor. Genelde ya araya giren antivirus/proxy ya da yuksek ag gecikmesi. Her sayfa yeni baglanti actigi icin dogrudan hiza yansir.'
            }
            else { Yaz 'TCP+TLS (ortanca)' "$mTls ms" 'Green' }
            if ($mTam -gt $TABAN_GECIK * 1.5) {
                Yaz 'sayfa (ortanca)' "$mTam sn  (taban: $TABAN_GECIK sn)" 'Red'
                Bulgu "Sayfa basina sure tabandan yuksek ($mTam sn vs $TABAN_GECIK sn). Darbogaz ag tarafinda - CPU degil."
            }
            else { Yaz 'sayfa (ortanca)' "$mTam sn  (taban: $TABAN_GECIK sn)" 'Green' }
            Yaz 'sayfa boyutu' "$mBoyut KB"
        }
        elseif ($s -match '^TAVAN (\S+)') {
            Yaz 'gorselsiz tavan hiz' "$($matches[1]) url/sn  (10 is parcacigi / sayfa suresi)" 'DarkGray'
        }
        elseif ($s -match '^GORSEL sure=(\S+) ort=(\S+) n=(\d+)') {
            $gSure = [double]$matches[1]
            # Her haberde ortalama ~3 gorsel var; hepsi ayri bir TLS baglantisi aciyor.
            $birUrl = $sayfaSure + $gSure * 3
            $ongoru = [math]::Round(10 / [math]::Max($birUrl, 0.01), 1)
            if ($gSure -gt 0.35) {
                Yaz 'gorsel basina' "$gSure sn (ort. $($matches[2]) KB)" 'Red'
                Bulgu "Gorsel basina $gSure sn. Her gorsel ayri bir TLS baglantisi aciyor; bir haberde ~3 gorsel var, yani sure sayfanin degil gorsellerin. Tek carei baglanti gecikmesini dusurmek (kablo/daha yakin ag) ya da eszamanliligi artirmak."
            }
            else { Yaz 'gorsel basina' "$gSure sn (ort. $($matches[2]) KB)" 'Green' }
            Yaz 'ongorulen toplam hiz' "$ongoru url/sn  (sayfa + ~3 gorsel, 10 is parcacigi)"
        }
        else { Write-Host $s -ForegroundColor DarkGray }
    }
    Remove-Item $urlDosya, $probeDosya -ErrorAction SilentlyContinue
}

# -- 7. disk yazma olcumu ---------------------------------------------------
Bas '7. Disk yazma olcumu'
$testKlasor = Join-Path $Kok '_tani-testi'
try {
    New-Item -ItemType Directory -Path $testKlasor -Force | Out-Null
    $icerik = 'x' * 4096
    $sure = Measure-Command {
        for ($i = 0; $i -lt 300; $i++) {
            [System.IO.File]::WriteAllText((Join-Path $testKlasor "t$i.json"), $icerik)
        }
    }
    $dosyaSn = [math]::Round(300 / $sure.TotalSeconds)
    if ($dosyaSn -lt 300) {
        Yaz '300 kucuk dosya' ("{0} sn  -> {1} dosya/sn" -f [math]::Round($sure.TotalSeconds, 2), $dosyaSn) 'Red'
        Bulgu "Kucuk dosya yazimi cok yavas ($dosyaSn dosya/sn). Sebep genelde HDD ya da antivirusun her dosyayi taramasi. Tarama sayfa basina 1 JSON + 1-5 gorsel yaziyor."
    }
    else { Yaz '300 kucuk dosya' ("{0} sn  -> {1} dosya/sn" -f [math]::Round($sure.TotalSeconds, 2), $dosyaSn) 'Green' }

    $buyuk = New-Object byte[] (20MB)
    $sure2 = Measure-Command { [System.IO.File]::WriteAllBytes((Join-Path $testKlasor 'buyuk.bin'), $buyuk) }
    Yaz '20 MB tek dosya' ("{0} MB/sn" -f [math]::Round(20 / $sure2.TotalSeconds))
    Remove-Item $testKlasor -Recurse -Force -ErrorAction SilentlyContinue
}
catch { Yaz 'yazma testi' "yapilamadi: $($_.Exception.Message)" 'Yellow' }

# -- ozet -------------------------------------------------------------------
Write-Host ''
Write-Host '  Ozet' -ForegroundColor Cyan
Write-Host '  ----' -ForegroundColor DarkGray
if ($bulgular.Count -eq 0) {
    Write-Host '    Belirgin bir darbogaz bulunamadi.' -ForegroundColor Green
    Write-Host '    Hiz yine de dusukse eszamanliligi yukseltmeyi degerlendirin' -ForegroundColor DarkGray
    Write-Host '    (site_arsivleyici.py icinde ESZAMANLILIK).' -ForegroundColor DarkGray
}
else {
    $n = 1
    foreach ($b in $bulgular) {
        Write-Host "    $n. $b" -ForegroundColor Yellow
        $n++
    }
}
Write-Host ''
Write-Host '  Not: bu is CPU ile hizlanmaz. On is parcacigi, her sayfada yeni bir' -ForegroundColor DarkGray
Write-Host '       TLS baglantisi aciyor; hiz = 10 / (sayfa basina saniye).' -ForegroundColor DarkGray
Write-Host ''
