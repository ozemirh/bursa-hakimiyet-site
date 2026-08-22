"""Yapay zeka editor: haber adresinden yayina hazir taslak uretir.

Kullanim:
    python arac/haber_taslak.py <adres>
    python arac/haber_taslak.py <adres> --yalniz-ayikla     # API cagrisi yapmaz
    python arac/haber_taslak.py <adres> --cikti arac/cikti

Cikti: <cikti>/<slug>.json  — hem kaynak ayiklamasi hem uretilen taslak.
Bu JSON dosyasi `yapay-zeka-editor.html` sayfasina surukle-birak ile yuklenir.

Onemli: Bu arac kaynagin metnini kopyalamaz. Olgu cikarimi yapip haberi
kaynak gostererek yeniden yazar ve dogrulanmasi gereken noktalari isaretler.
Cikan sey bir TASLAKTIR; editor onayi olmadan yayina girmez.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayiklayici import coz  # noqa: E402

MODEL = "claude-opus-5"

KATEGORILER = [
    "Gündem", "Siyaset", "Ekonomi", "Asayiş", "Yargı", "Sağlık", "Eğitim",
    "Çevre ve su", "Ulaşım", "Spor", "Kültür", "Yaşam", "Teknoloji", "Tarım",
]

ILCELER = [
    "Bursa geneli", "Osmangazi", "Nilüfer", "Yıldırım", "İnegöl", "Gemlik",
    "Mudanya", "Mustafakemalpaşa", "Karacabey", "İznik", "Orhangazi", "Kestel",
    "Gürsu", "Yenişehir", "Orhaneli", "Keles", "Büyükorhan", "Harmancık",
    "Bursa dışı",
]

SISTEM = f"""Sen Bursa Hakimiyet gazetesinin dijital haber masasinda calisan kidemli bir
editorsun. Sana baska bir yayindan alinmis bir haberin ayiklanmis icerigi verilir.
Gorevin, bu icerikten gazetenin yayin sistemine girilecek bir TASLAK uretmek.

MUTLAK KURALLAR

1. Kaynagin cumlelerini kopyalama. Haberi bastan, kendi cumlelerinle yaz.
   Yalnizca dogrudan alinti yapiyorsan tirnak icinde ver ve kime ait oldugunu belirt.
2. Kaynakta olmayan hicbir olguyu uydurma. Isim, rakam, tarih, kurum, unvan,
   olu/yarali sayisi icat etme. Kaynakta belirsiz olan seyi belirsiz birak ve
   `dogrulanmasi_gerekenler` listesine yaz.
3. Habere mutlaka kaynak atfi koy ("... {{kaynak}}'in haberine gore ...").
   Atfi gövdenin ilk iki paragrafindan birine yerlestir.
4. Devam eden yargi sureci varsa masumiyet karinesini koru: "iddia ediliyor",
   "sucglamalari reddediyor", "yargilama suruyor" kaliplarini kullan, kesin
   hukum diliyle yazma. Bunu `hassas_konu` alaninda isaretle.
5. Cocuk, magdur, saglik verisi, intihar, cinsel suc gibi hassas basliklarda
   kimlik bilgisi verme ve `hassas_konu` alaninda uyari yaz.
6. Uslup: Turkce haber dili, sade, kisa cumleler, edilgen yapidan kacin.
   Baslikta tiklama tuzagi ("inanamayacaksiniz", "iste o an") kullanma.
7. Kaynak Bursa ile ilgili degilse bunu `bursa_ilgisi` alaninda durustce belirt;
   haberi zorla yerellestirme.

ALAN KURALLARI
- `baslik_secenekleri`: tam 3 secenek. Biri duz haber basligi, biri sonuc/etki
  odakli, biri kisa ve vurucu olsun. Her birinin gerekcesini yaz. En fazla 70 karakter.
- `spot`: 1-2 cumle, 160-260 karakter. Basligi tekrar etme, bilgi ekle.
- `uc_madde`: "3 maddede ne oldu" kutusu icin uc kisa madde.
- `govde`: en az 5 blok. Ilk blok paragraf olmali. Uzun haberlerde ara_baslik kullan.
- `etiketler`: 4-7 adet, kucuk harf, ozel isimler haric.
- `seo_baslik`: en fazla 60 karakter. `seo_aciklama`: en fazla 155 karakter.
- `url_slug`: kucuk harf, Turkce karakter yok, kelimeler tire ile ayrilmis.
- `kategori`: yalnizca su listeden: {", ".join(KATEGORILER)}
- `ilce`: yalnizca su listeden: {", ".join(ILCELER)}
- `onem`: manset / one_cikan / normal
- `editor_notu`: masaya not. Neyi degistirdigini, neye dikkat edilmesi gerektigini yaz.
"""

SEMA = {
    "type": "object",
    "properties": {
        "baslik_secenekleri": {
            "type": "array", "minItems": 3, "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "metin": {"type": "string"},
                    "gerekce": {"type": "string"},
                },
                "required": ["metin", "gerekce"],
                "additionalProperties": False,
            },
        },
        "onerilen_baslik_indeksi": {"type": "integer", "minimum": 0, "maximum": 2},
        "spot": {"type": "string"},
        "uc_madde": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "string"}},
        "govde": {
            "type": "array", "minItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "tur": {"type": "string", "enum": ["paragraf", "ara_baslik", "alinti"]},
                    "metin": {"type": "string"},
                },
                "required": ["tur", "metin"],
                "additionalProperties": False,
            },
        },
        "kategori": {"type": "string", "enum": KATEGORILER},
        "ilce": {"type": "string", "enum": ILCELER},
        "etiketler": {"type": "array", "minItems": 3, "maxItems": 8, "items": {"type": "string"}},
        "seo_baslik": {"type": "string"},
        "seo_aciklama": {"type": "string"},
        "url_slug": {"type": "string"},
        "gorsel_alt": {"type": "string"},
        "gorsel_altyazi": {"type": "string"},
        "okuma_suresi_dk": {"type": "integer", "minimum": 1},
        "onem": {"type": "string", "enum": ["manset", "one_cikan", "normal"]},
        "kaynak_atfi": {"type": "string"},
        "dogrulanmasi_gerekenler": {"type": "array", "items": {"type": "string"}},
        "hassas_konu": {
            "type": "object",
            "properties": {
                "var_mi": {"type": "boolean"},
                "turu": {"type": "string"},
                "uyari": {"type": "string"},
            },
            "required": ["var_mi", "turu", "uyari"],
            "additionalProperties": False,
        },
        "bursa_ilgisi": {
            "type": "object",
            "properties": {
                "var_mi": {"type": "boolean"},
                "aciklama": {"type": "string"},
            },
            "required": ["var_mi", "aciklama"],
            "additionalProperties": False,
        },
        "editor_notu": {"type": "string"},
    },
    "required": [
        "baslik_secenekleri", "onerilen_baslik_indeksi", "spot", "uc_madde", "govde",
        "kategori", "ilce", "etiketler", "seo_baslik", "seo_aciklama", "url_slug",
        "gorsel_alt", "gorsel_altyazi", "okuma_suresi_dk", "onem", "kaynak_atfi",
        "dogrulanmasi_gerekenler", "hassas_konu", "bursa_ilgisi", "editor_notu",
    ],
    "additionalProperties": False,
}


def slugla(metin: str, uzunluk: int = 60) -> str:
    """Turkce basligi dosya adina uygun sade bir slug'a cevirir."""
    esle = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    d = metin.translate(esle)
    d = unicodedata.normalize("NFKD", d).encode("ascii", "ignore").decode()
    d = re.sub(r"[^a-zA-Z0-9]+", "-", d).strip("-").lower()
    return (d[:uzunluk].rstrip("-") or "taslak")


def taslak_uret(kaynak: dict, model: str = MODEL, efor: str = "high") -> dict:
    """Ayiklanmis kaynaktan yapilandirilmis taslak uretir."""
    import anthropic

    istem = f"""Asagida baska bir yayindan ayiklanmis bir haber var. Bunu Bursa Hakimiyet
icin yayina hazir bir taslaga cevir.

KAYNAK YAYIN : {kaynak.get('kaynak_adi') or kaynak.get('kaynak_alan')}
ADRES        : {kaynak.get('kaynak_url')}
YAZAR        : {kaynak.get('yazar') or 'belirtilmemis'}
YAYIN TARIHI : {kaynak.get('yayin_tarihi') or 'belirtilmemis'}
AYIKLAMA GUVENI: {kaynak.get('ayiklama_guveni')} ({kaynak.get('kelime_sayisi')} kelime)

ORIJINAL BASLIK
{kaynak.get('orijinal_baslik')}

ORIJINAL SPOT
{kaynak.get('orijinal_spot') or '(yok)'}

ORIJINAL GOVDE
{kaynak.get('orijinal_govde') or '(govde ayiklanamadi)'}
"""

    if kaynak.get("kelime_sayisi", 0) < 60:
        istem += (
            "\nUYARI: Govde cok kisa ayiklandi. Elindeki bilgiyle yetin, eksigi "
            "tamamlamak icin bilgi uydurma; eksikleri `dogrulanmasi_gerekenler` "
            "listesine yaz ve `editor_notu` icinde kaynaga elle bakilmasi "
            "gerektigini belirt.\n"
        )

    istemci = anthropic.Anthropic()
    yanit = istemci.beta.messages.create(
        model=model,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SISTEM,
        thinking={"type": "adaptive"},
        output_config={
            "effort": efor,
            "format": {"type": "json_schema", "schema": SEMA},
        },
        messages=[{"role": "user", "content": istem}],
    )

    if yanit.stop_reason == "refusal":
        ayrinti = getattr(yanit, "stop_details", None)
        raise RuntimeError(
            "Model bu icerigi islemeyi reddetti"
            + (f" ({ayrinti.category})" if ayrinti else "")
        )

    metin = next((b.text for b in yanit.content if b.type == "text"), "")
    if not metin:
        raise RuntimeError("Model metin blogu dondurmedi.")

    return {
        "taslak": json.loads(metin),
        "uretim": {
            "model": yanit.model,
            "girdi_token": yanit.usage.input_tokens,
            "cikti_token": yanit.usage.output_tokens,
            "efor": efor,
            "zaman": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    }


def main() -> int:
    ayrist = argparse.ArgumentParser(
        description="Haber adresinden Bursa Hakimiyet icin yayina hazir taslak uretir."
    )
    ayrist.add_argument("adres", help="Haberin tam adresi")
    ayrist.add_argument("--cikti", default="arac/cikti", help="Cikti klasoru")
    ayrist.add_argument("--model", default=MODEL, help=f"Model kimligi (varsayilan {MODEL})")
    ayrist.add_argument("--efor", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    ayrist.add_argument("--yalniz-ayikla", action="store_true",
                        help="Sadece kaynagi ayiklar, API cagrisi yapmaz")
    a = ayrist.parse_args()

    print(f"[1/3] Kaynak indiriliyor: {a.adres}")
    try:
        kaynak = coz(a.adres)
    except Exception as e:
        print(f"  HATA: {e}", file=sys.stderr)
        return 1

    print(f"      {kaynak['kaynak_adi']} · {kaynak['kelime_sayisi']} kelime "
          f"· guven: {kaynak['ayiklama_guveni']}")
    if kaynak["ayiklama_guveni"] == "dusuk":
        print("      UYARI: Ayiklama zayif. Kaynagi elle kontrol edin.")

    paket = {"kaynak": kaynak}

    if a.yalniz_ayikla:
        print("[2/3] Atlandi (--yalniz-ayikla)")
    else:
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            print("  HATA: ANTHROPIC_API_KEY tanimli degil.\n"
                  "        setx ANTHROPIC_API_KEY \"sk-ant-...\" ile tanimlayip "
                  "yeni bir terminal acin.", file=sys.stderr)
            return 2
        print(f"[2/3] Taslak uretiliyor ({a.model}, efor={a.efor})...")
        try:
            paket.update(taslak_uret(kaynak, a.model, a.efor))
        except Exception as e:
            print(f"  HATA: {e}", file=sys.stderr)
            return 3

    klasor = Path(a.cikti)
    klasor.mkdir(parents=True, exist_ok=True)
    ad = slugla(
        paket.get("taslak", {}).get("url_slug") or kaynak["orijinal_baslik"] or "taslak"
    )
    yol = klasor / f"{ad}.json"
    yol.write_text(json.dumps(paket, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[3/3] Yazildi: {yol}")
    t = paket.get("taslak")
    if t:
        secilen = t["baslik_secenekleri"][t["onerilen_baslik_indeksi"]]["metin"]
        print(f"\n  Onerilen baslik : {secilen}")
        print(f"  Kategori / ilce : {t['kategori']} / {t['ilce']}")
        print(f"  Onem            : {t['onem']}")
        if t["dogrulanmasi_gerekenler"]:
            print(f"  Dogrulanacak    : {len(t['dogrulanmasi_gerekenler'])} madde")
        if t["hassas_konu"]["var_mi"]:
            print(f"  HASSAS KONU     : {t['hassas_konu']['turu']}")
    print("\n  Bu JSON dosyasini yapay-zeka-editor.html sayfasina surukleyip birakin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
