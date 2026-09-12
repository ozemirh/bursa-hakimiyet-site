"""YouTube — **otomatik akışa girmez.**

Gazete YouTube'da haber paylaşmıyor; orada ayrıca çekilmiş **özel videolar**
yayımlanıyor (kullanıcı kararı, 5 Eylül 2026). Bu yüzden YouTube hesabı
X · Facebook · Instagram ile aynı kefeye konmadı:

* haber formundaki otomatik paylaşım kutularında **görünmez**;
* kuyruğa yalnız editörün açtığı "video yüklenecek" satırı olarak düşer ve
  o satır her zaman ELLE durumundadır;
* panel, video açıklamasında kullanılacak metni hazırlar — yükleme
  YouTube'da elle yapılır, editör dönüp video adresini satıra yazar.

Video yükleme ucu (Data API v3 `videos.insert`) bilerek yazılmadı: dosya
yüklemek panelin bugün yaptığı iş değil ve yarım bir yükleyici, olmayan
yükleyiciden kötüdür. Karar değişirse buraya `gonder` eklenir; sözleşmenin
geri kalanı hazır.
"""

from .taban import Saglayici, Sonuc


class YouTubeSaglayici(Saglayici):
    kod = "youtube"
    ad = "YouTube (özel video)"
    otomatik_olur = False
    gerekli = ()          # anahtar istemez: gönderim elle yapılıyor
    yardim = ("Bu hesap otomatik paylaşıma girmez. Kuyruktaki satır, "
              "yüklenecek videonun başlık ve açıklama metnini taşır; "
              "video YouTube'da elle yüklenir ve adresi satıra yazılır.")

    def gonder(self, hesap, gonderi) -> Sonuc:
        return Sonuc(False, hata=(
            "YouTube'a panelden video yüklenmiyor. Videoyu yükledikten "
            "sonra adresini bu satıra yazıp “Paylaşıldı” işaretleyin."))
