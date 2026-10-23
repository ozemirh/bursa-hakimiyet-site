"""Beş rol ve on dört yetkilik rol matrisi.

Kaynak: `PANEL-NOTLARI.md` §11. Matris gazete masasının gerçek iş
bölümünden çıkarıldı; dökümdeki kanıt manşet kayıtlarının ve resmî
ilanların neredeyse tamamının iki kişide toplanmış olmasıydı.

Yetkiler Django'nun kendi izin düzeneğine bağlanır: her rol bir `Group`,
her yetkilik bir `Permission`. Böylece hem panelde hem yönetim arayüzünde
aynı kural işler, ikinci bir yetki sistemi yazılmaz.

**Bu dosya matrisin tek kaynağıdır.** Değişiklik gerekiyorsa önce
`PANEL-NOTLARI.md` §11 güncellenir, sonra burası.
"""

# Django'nun kendi ekle/degistir/sil izinleri yetmiyor: "kendi haberini
# yayınlama" ile "başkasınınkini yayınlama" ayrı kararlar ve ikisi de
# "change_haber" degil. Bu yuzden ozel izinler tanimlaniyor.
OZEL_IZINLER = [
    ("haber_girme", "Haber girme (taslak)"),
    ("kendi_haberini_yayinlama", "Kendi haberini yayınlama"),
    ("baskasinin_haberini_yayinlama", "Başkasının haberini yayınlama"),
    ("haberi_arsivleme", "Haberi arşive alma"),
    ("mansete_alma", "Manşete alma"),
    ("sayfa_duzeni", "Sayfa düzeni ve reklam alanları"),
    ("resmi_ilan_girme", "Resmî ilan girme"),
    ("reklam_kampanyasi", "Reklam kampanyası"),
    ("yorum_onaylama", "Yorum onaylama"),
    ("kose_yonetimi", "Köşe yazısı ve yazar yönetimi"),
    ("konu_yonetimi", "Konu açma ve bağlama"),
    ("taksonomi_duzenleme", "Taksonomi düzenleme"),
    ("kullanici_yonetimi", "Kullanıcı ve rol yönetimi"),
    ("log_goruntuleme", "Log kayıtları"),
]

MUHABIR = "Muhabir"
EDITOR = "Editör"
SAYFA_SEKRETERI = "Sayfa Sekreteri"
ILAN_SORUMLUSU = "İlan Sorumlusu"
YAYIN_YONETMENI = "Yayın Yönetmeni"

ROLLER = [MUHABIR, EDITOR, SAYFA_SEKRETERI, ILAN_SORUMLUSU, YAYIN_YONETMENI]

# PANEL-NOTLARI.md §11'deki tablonun birebir karşılığı.
MATRIS = {
    "haber_girme":                   [MUHABIR, EDITOR, SAYFA_SEKRETERI, YAYIN_YONETMENI],
    "kendi_haberini_yayinlama":      [EDITOR, SAYFA_SEKRETERI, YAYIN_YONETMENI],
    "baskasinin_haberini_yayinlama": [EDITOR, SAYFA_SEKRETERI, YAYIN_YONETMENI],
    "haberi_arsivleme":              [EDITOR, SAYFA_SEKRETERI, YAYIN_YONETMENI],
    "mansete_alma":                  [SAYFA_SEKRETERI, YAYIN_YONETMENI],
    "sayfa_duzeni":                  [SAYFA_SEKRETERI, YAYIN_YONETMENI],
    "resmi_ilan_girme":              [ILAN_SORUMLUSU, YAYIN_YONETMENI],
    "reklam_kampanyasi":             [ILAN_SORUMLUSU, YAYIN_YONETMENI],
    "yorum_onaylama":                [EDITOR, YAYIN_YONETMENI],
    "kose_yonetimi":                 [EDITOR, YAYIN_YONETMENI],
    "konu_yonetimi":                 [EDITOR, YAYIN_YONETMENI],
    "taksonomi_duzenleme":           [YAYIN_YONETMENI],
    "kullanici_yonetimi":            [YAYIN_YONETMENI],
    "log_goruntuleme":               [YAYIN_YONETMENI],
}

# §11 önerisi: yayınlama, manşet ve resmî ilan yetkisi olan rollerde 2FA
# zorunlu olsun. Altyapı mevcut sistemde hazır, şu an isteğe bağlı.
IKI_ADIMLI_ZORUNLU = {EDITOR, SAYFA_SEKRETERI, ILAN_SORUMLUSU, YAYIN_YONETMENI}


def rolun_yetkileri(rol: str) -> list[str]:
    return [kod for kod, roller in MATRIS.items() if rol in roller]
