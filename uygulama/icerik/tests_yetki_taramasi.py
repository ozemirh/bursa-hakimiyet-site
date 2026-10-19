"""URL çözücüden türetilen yetki taraması — Paket F madde 10.

Tek bir test bütün panel adreslerini URL tablosundan TOPLAR (elle liste
değil) ve her kalıbı 5 rol + anonim × GET ve POST ile dener. Beklenen
yetki aşağıdaki SÖZLEŞME tablosundadır; rolün yetkisi `yetkiler.MATRIS`ten
gelir (PANEL-NOTLARI §11). Böylece:

- tabloya girmemiş YENİ bir panel kalıbı testi düşürür (yetkisi
  düşünülmeden adres açılamaz);
- tablodaki kalıp kaldırılırsa da test düşer (tablo bayatlamaz);
- yetkisiz rol her kalıpta 403 almalı; yetkili rol hiçbir kalıpta 403
  ya da 500 almamalı; anonim her zaman giriş ekranına yönlenmeli.

Ayrıntı kimlikleri BİLEREK var olmayan kayıtlara gider: yetki denetimi
kayıt aranmadan önce yapılmalı, yani yetkisiz rol 404 değil 403 görmeli
(kaydın var olup olmadığı yetkisiz kullanıcıya sızmasın).

Durum değiştiren toplu fiiller ayrıca fiil × rol tablosuyla denenir.
"""

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from .panel import MEDYA_AILELERI, MEDYA_FIIL_SOZLUGU, TOPLU_FIIL_SOZLUGU
from .yetkiler import MATRIS, ROLLER

ACIK = "acik"        # oturumsuz erişilir
GIRIS = "giris"      # yalnız oturum; yetkilik yok (fiil düzeyi ayrıca denenir)

#: Panel adres sözleşmesi: URL adı → gereken yetkilik.
SOZLESME = {
    "panel-giris": ACIK,
    "panel-cikis": ACIK,
    "panel-bugun": GIRIS,
    "panel-akis": GIRIS,
    "panel-okunma": GIRIS,
    "panel-iki-adimli": GIRIS,
    "panel-sifre": GIRIS,
    "panel-toplu": GIRIS,
    "panel-medya-toplu": GIRIS,
    "panel-haber-ekle": "haber_girme",
    "panel-haber-duzenle": "haber_girme",
    "panel-haber-ara": "haber_girme",
    "panel-galeri-ara": "haber_girme",
    "panel-yz-taslak-ekle": "haber_girme",
    "panel-yz-taslak": "haber_girme",
    "panel-yz-gorsel": "haber_girme",
    "panel-yz-bulgu-kapat": "haber_girme",     # Paket M: K2 bulgusu tek tek
    "panel-galeriler": "haber_girme",
    "panel-galeri-duzenle": "haber_girme",
    "panel-videolar": "haber_girme",
    "panel-video-duzenle": "haber_girme",
    "panel-mansetler": "mansete_alma",
    "panel-son-dakika": "mansete_alma",
    "panel-son-dakika-duzenle": "mansete_alma",
    "panel-bildirimler": "mansete_alma",
    "panel-bildirim-duzenle": "mansete_alma",
    "panel-konular": "konu_yonetimi",
    "panel-konu-duzenle": "konu_yonetimi",
    "panel-konu-karar": "konu_yonetimi",
    "panel-konu-haber-cikar": "konu_yonetimi",
    "panel-kose": "kose_yonetimi",
    "panel-kose-duzenle": "kose_yonetimi",
    "panel-yazarlar": "kose_yonetimi",
    "panel-yazar-duzenle": "kose_yonetimi",
    "panel-kategoriler": "taksonomi_duzenleme",
    "panel-kategori-duzenle": "taksonomi_duzenleme",
    "panel-kaynaklar": "taksonomi_duzenleme",
    "panel-kaynak-duzenle": "taksonomi_duzenleme",
    "panel-kullanicilar": "kullanici_yonetimi",
    "panel-kullanici-duzenle": "kullanici_yonetimi",
    "panel-roller": "kullanici_yonetimi",
    "panel-sosyal-hesaplar": "kullanici_yonetimi",
    "panel-sosyal-hesap-ekle": "kullanici_yonetimi",
    "panel-sosyal-hesap": "kullanici_yonetimi",
    "panel-sosyal": "kendi_haberini_yayinlama",
    "panel-sosyal-gonder": "kendi_haberini_yayinlama",
    "panel-sosyal-ekle": "kendi_haberini_yayinlama",
    "panel-sosyal-gonderi": "kendi_haberini_yayinlama",
    "panel-yorumlar": "yorum_onaylama",
    "panel-yorum-duzenle": "yorum_onaylama",
    "panel-ilanlar": "resmi_ilan_girme",
    "panel-ilan-duzenle": "resmi_ilan_girme",
    "panel-gazeteler": "resmi_ilan_girme",
    "panel-gazete-duzenle": "resmi_ilan_girme",
    "panel-yuvalar": "sayfa_duzeni",
    "panel-yuva-duzenle": "sayfa_duzeni",
    "panel-kampanyalar": "reklam_kampanyasi",
    "panel-kampanya-duzenle": "reklam_kampanyasi",
    "panel-log": "log_goruntuleme",
    "panel-log-detay": "log_goruntuleme",
}

#: Toplu fiil sözleşmesi (PANEL-NOTLARI §12; kategori daraltması §12 SAPMA).
TOPLU_FIIL_SOZLESMESI = {
    "yayina_al": "baskasinin_haberini_yayinlama",
    "yayindan_cek": "baskasinin_haberini_yayinlama",
    "arsivle": "haberi_arsivleme",
    "hazirlik": "haber_girme",
    "ilce": "haber_girme",
    "etiket": "haber_girme",
    "mansete_al": "mansete_alma",
    "mansetten_cikar": "mansete_alma",
    "kategori": "taksonomi_duzenleme",
}
MEDYA_FIIL_SOZLESMESI = {
    "yayina_al": "baskasinin_haberini_yayinlama",
    "yayindan_cek": "baskasinin_haberini_yayinlama",
    "arsivle": "haberi_arsivleme",
}
MEDYA_EKRAN_SOZLESMESI = {"kose": "kose_yonetimi", "galeri": "haber_girme",
                          "video": "haber_girme"}

OLMAYAN = 987_654_321
IZINLI_DURUMLAR = {200, 302, 404, 405}


def panel_kaliplari() -> dict:
    """URL tablosundaki `panel/` kalıpları: ad → (kalıp metni, kalıp)."""
    bulunan = {}

    def gez(desenler, onek=""):
        for d in desenler:
            if isinstance(d, URLResolver):
                gez(d.url_patterns, onek + str(d.pattern))
            elif isinstance(d, URLPattern):
                metin = onek + str(d.pattern)
                if metin.lstrip("^").startswith("panel/"):
                    bulunan[d.name or metin] = (metin, d)
    gez(get_resolver().url_patterns)
    return bulunan


def ornek_adres(ad: str, kalip) -> str:
    """Kalıbın dönüştürücülerine göre somut adres (var olmayan kimliklerle)."""
    cevirici = getattr(kalip.pattern, "converters", {}) or {}
    degerler = {}
    for alan, donusturucu in cevirici.items():
        tur = type(donusturucu).__name__
        degerler[alan] = OLMAYAN if tur == "IntConverter" else "kose"
    return reverse(ad, kwargs=degerler) if degerler else reverse(ad)


def rol_yetkili_mi(rol: str, yetki: str) -> bool:
    if yetki in (ACIK, GIRIS):
        return True
    return rol in MATRIS.get(yetki, [])


class YetkiTaramasi(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.roller = {}
        for sira, rol in enumerate(ROLLER):
            u = User.objects.create_user(f"tarama{sira}", first_name="T",
                                         last_name=str(sira))
            u.groups.add(Group.objects.get(name=rol))
            cls.roller[rol] = u

    def setUp(self):
        cache.clear()

    def test_sozlesme_url_tablosuyla_birebir(self):
        """Yeni panel kalıbı ancak yetkisi bu tabloya yazılarak açılır."""
        kaliplar = set(panel_kaliplari())
        self.assertEqual(kaliplar - set(SOZLESME), set(),
                         "Sözleşmede olmayan panel kalıbı: yetkisini tabloya yazın.")
        self.assertEqual(set(SOZLESME) - kaliplar, set(),
                         "Sözleşmede kalan ama URL tablosunda olmayan kalıp.")
        for yetki in set(SOZLESME.values()) - {ACIK, GIRIS}:
            self.assertIn(yetki, MATRIS)

    def _dene(self, istemci, yontem, adres):
        return getattr(istemci, yontem)(adres)

    def test_her_kalip_her_rol_get_ve_post(self):
        kaliplar = panel_kaliplari()
        hatalar = []
        adresler = {ad: ornek_adres(ad, kalip) for ad, (_, kalip) in kaliplar.items()}

        # Anonim: her korunan kalıp giriş ekranına yönlenir.
        for ad, adres in adresler.items():
            if SOZLESME.get(ad) == ACIK:
                continue
            for yontem in ("get", "post"):
                y = self._dene(self.client, yontem, adres)
                if y.status_code != 302 or not y["Location"].startswith("/panel/giris"):
                    hatalar.append(f"anonim {yontem.upper()} {adres}: {y.status_code}")

        for rol, kullanici in self.roller.items():
            self.client.force_login(kullanici)
            for ad, adres in adresler.items():
                if ad in ("panel-cikis", "panel-giris"):
                    continue
                for yontem in ("get", "post"):
                    yetki = SOZLESME.get(ad, "?")
                    if ad == "panel-medya-toplu" and yontem == "post":
                        # Aile adresin parçası; POST'ta ailenin ekran yetkisi
                        # kapıdır (GET herkese listeye yönlenir).
                        yetki = MEDYA_EKRAN_SOZLESMESI["kose"]
                    yetkili = rol_yetkili_mi(rol, yetki)
                    durum = self._dene(self.client, yontem, adres).status_code
                    if yetkili and durum not in IZINLI_DURUMLAR:
                        hatalar.append(f"{rol} {yontem.upper()} {adres}: {durum} (izinli olmalı)")
                    elif not yetkili and durum != 403:
                        hatalar.append(f"{rol} {yontem.upper()} {adres}: {durum} (403 olmalı)")
            self.client.logout()
        self.assertEqual(hatalar, [], "\n".join(hatalar))

    def test_toplu_fiiller_rol_tablosu(self):
        self.assertEqual(set(TOPLU_FIIL_SOZLUGU), set(TOPLU_FIIL_SOZLESMESI),
                         "Yeni toplu fiil: yetkisini sözleşmeye yazın.")
        hatalar = []
        for rol, kullanici in self.roller.items():
            self.client.force_login(kullanici)
            for fiil, yetki in TOPLU_FIIL_SOZLESMESI.items():
                durum = self.client.post("/panel/toplu", {
                    "fiil": fiil, "kimlikler": [OLMAYAN]}).status_code
                beklenen = 302 if rol in MATRIS[yetki] else 403
                if durum != beklenen:
                    hatalar.append(f"{rol} toplu {fiil}: {durum} ≠ {beklenen}")
            self.client.logout()
        self.assertEqual(hatalar, [], "\n".join(hatalar))

    def test_medya_toplu_fiiller_rol_tablosu(self):
        self.assertEqual(set(MEDYA_FIIL_SOZLUGU), set(MEDYA_FIIL_SOZLESMESI))
        self.assertEqual(set(MEDYA_AILELERI), set(MEDYA_EKRAN_SOZLESMESI))
        hatalar = []
        for rol, kullanici in self.roller.items():
            self.client.force_login(kullanici)
            for aile, ekran in MEDYA_EKRAN_SOZLESMESI.items():
                for fiil, yetki in MEDYA_FIIL_SOZLESMESI.items():
                    durum = self.client.post(f"/panel/toplu/{aile}", {
                        "fiil": fiil, "kimlikler": [OLMAYAN]}).status_code
                    izinli = rol in MATRIS[ekran] and rol in MATRIS[yetki]
                    beklenen = 302 if izinli else 403
                    if durum != beklenen:
                        hatalar.append(f"{rol} {aile}/{fiil}: {durum} ≠ {beklenen}")
            self.client.logout()
        self.assertEqual(hatalar, [], "\n".join(hatalar))
