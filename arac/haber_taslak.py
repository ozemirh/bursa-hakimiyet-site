"""Yapay zeka editor: haber adresinden yayina hazir taslak uretir.

Kullanim:
    python arac/haber_taslak.py <adres>                    # kural motoru (varsayilan)
    python arac/haber_taslak.py <adres> --saglayici claude # Claude ile tam taslak (anahtar ister)
    python arac/haber_taslak.py <adres> --saglayici cli    # tam taslak, anahtarsiz (claude CLI)
    python arac/haber_taslak.py <adres> --saglayici skill  # cli + denetim + duzeltme turu
    python arac/haber_taslak.py <adres> --yalniz-ayikla    # yalnizca kaynagi ayiklar
    python arac/haber_taslak.py --kaynak-json <dosya>      # aga cikmadan yeniden uretir

Cikti: <cikti>/<slug>.json  — hem kaynak ayiklamasi hem uretilen taslak.
Bu JSON dosyasi `yapay-zeka-editor.html` sayfasina surukle-birak ile yuklenir.

Uc saglayici var:
  kural  — model kullanmaz, API anahtari istemez, ucretsiz ve deterministiktir.
           Alanlari sozlukle doldurur, GOVDEYI YAZMAZ; kaynagin cumlelerini
           "ham malzeme" olarak tezgaha koyar, editor haberi kendi yazar.
  claude — `claude-opus-5` ile tam taslak uretir, ANTHROPIC_API_KEY ister.
  cli    — ayni isi anahtarsiz yapar: makinede kurulu `claude` komutunu (Claude
           Code) cagirir, kullanicinin kendi oturumunu kullanir. Bkz. yz_cli.py.
  skill  — cli yolunu calistirir, ciktisini `denetim.py` ile denetler ve bulgu
           varsa modele geri verip duzelttirir (taslak-denetimi Mod 1 zinciri).
           Yavas ama yayina en yakin sonucu verir. Bkz. yz_skill.py.

Onemli: Bu arac kaynagin metnini kopyalamaz. Cikan sey bir TASLAKTIR; editor
onayi olmadan yayina girmez. Konu baglantisi da onaysiz kurulmaz.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ayiklayici import coz  # noqa: E402
from kural_motoru import slugla, taslak_uret_kural  # noqa: E402
import konu_eslestirme as ke  # noqa: E402

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
3. Kaynak her zaman belirtilir, ama GOVDEYE atif cumlesi koymak zorunda
   degilsin: yayinlanan sayfada ayri bir "Kaynak" bolmesi var ve `kaynak_atfi`
   alani oraya basiliyor. Kaynak sayfa kendi kaynagini belirtmisse (AA, DHA,
   Reuters gibi) o da anilir. Haberi kendi cumlelerinle bastan yaz.
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
- `etiketler`: 3-8 adet, kucuk harf, ozel isimler haric.
- `seo_baslik`: en fazla 60 karakter. `seo_aciklama`: en fazla 155 karakter.
- `url_slug`: kucuk harf, Turkce karakter yok, kelimeler tire ile ayrilmis.
- `kategori`: yalnizca su listeden: {", ".join(KATEGORILER)}
- `ilce`: yalnizca su listeden: {", ".join(ILCELER)}
- `onem`: manset / one_cikan / normal
- `onerilen_baslik_indeksi`: `baslik_secenekleri` icinden onerdigin secenegin
  sirasi (0-2). Gerekcesi o secenegin `gerekce` alaninda yazili olsun.
- `kaynak_atfi`: "<yayin> haberine gore" kalibi. Yayinlanan sayfadaki kaynak
  bolmesinde kullanilir; govdede gecmesi SART DEGIL. Bos birakma.
- `gorsel_alt`: gorseldeki sahneyi betimle, en fazla 125 karakter. Erisilebilirlik
  alanidir: haber basligini tekrar etme, "fotograf" diye baslama.
- `gorsel_altyazi`: fotograf alti. Kim/ne, nerede, ne zaman. Kaynak fotografin hak
  durumu dogrulanmadan yayina girmez; bunu `dogrulanmasi_gerekenler` listesine yaz.
- `okuma_suresi_dk`: govdenin kelime sayisi / 200, yukari yuvarla, en az 1.
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


def sema_dogrula(taslak: dict, sema: dict = SEMA) -> list[str]:
    """SEMA'ya karsi hafif dogrulama. Kural motorunun ciktisi da bu kapidan gecer.

    Tam bir JSON Schema uygulamasi degil: eksik alan, yanlis tur, liste uzunlugu
    ve kapali liste (enum) ihlallerini yakalar. Bos metin alanlari kural
    motorunda kasitlidir, hata sayilmaz.
    """
    hatalar: list[str] = []
    ozellikler = sema.get("properties", {})

    for alan in sema.get("required", []):
        if alan not in taslak:
            hatalar.append(f"eksik alan: {alan}")

    for alan, deger in taslak.items():
        kural = ozellikler.get(alan)
        if not kural:
            continue
        tur = kural.get("type")
        if tur == "array":
            if not isinstance(deger, list):
                hatalar.append(f"{alan}: liste bekleniyordu")
                continue
            if "minItems" in kural and len(deger) < kural["minItems"]:
                hatalar.append(f"{alan}: en az {kural['minItems']} öğe gerekli, {len(deger)} var")
            if "maxItems" in kural and len(deger) > kural["maxItems"]:
                hatalar.append(f"{alan}: en fazla {kural['maxItems']} öğe olmalı, {len(deger)} var")
            ic = kural.get("items", {})
            if ic.get("type") == "object":
                for i, oge in enumerate(deger):
                    if not isinstance(oge, dict):
                        hatalar.append(f"{alan}[{i}]: nesne bekleniyordu")
                        continue
                    for gerekli in ic.get("required", []):
                        if gerekli not in oge:
                            hatalar.append(f"{alan}[{i}]: eksik alan {gerekli}")
                    icsel = ic.get("properties", {})
                    for ad, d in oge.items():
                        secenek = icsel.get(ad, {}).get("enum")
                        if secenek and d not in secenek:
                            hatalar.append(f"{alan}[{i}].{ad}: “{d}” kapalı listede yok")
        elif tur == "integer" and not isinstance(deger, int):
            hatalar.append(f"{alan}: tam sayı bekleniyordu")
        elif tur == "string" and not isinstance(deger, str):
            hatalar.append(f"{alan}: metin bekleniyordu")
        elif tur == "object" and isinstance(deger, dict):
            for gerekli in kural.get("required", []):
                if gerekli not in deger:
                    hatalar.append(f"{alan}: eksik alan {gerekli}")

        if kural.get("enum") and deger not in kural["enum"]:
            hatalar.append(f"{alan}: “{deger}” kapalı listede yok")

    return hatalar


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
    ayrist.add_argument("adres", nargs="?", help="Haberin tam adresi")
    ayrist.add_argument("--kaynak-json", help="Aga cikmadan, mevcut bir cikti dosyasindaki "
                                              "`kaynak` nesnesiyle yeniden uretir")
    ayrist.add_argument("--saglayici", default="kural",
                        choices=["kural", "claude", "cli", "skill"],
                        help="Taslagi kim uretsin (varsayilan: kural — model kullanmaz; "
                             "cli: anahtarsiz yerel claude; skill: cli + denetim zinciri)")
    ayrist.add_argument("--cikti", default="arac/cikti", help="Cikti klasoru")
    ayrist.add_argument("--model", default=MODEL, help=f"Model kimligi (varsayilan {MODEL})")
    ayrist.add_argument("--efor", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    ayrist.add_argument("--yalniz-ayikla", action="store_true",
                        help="Sadece kaynagi ayiklar, taslak uretmez")
    ayrist.add_argument("--konu", help="Taslagi bu konu kimligine bagla (acik onay)")
    ayrist.add_argument("--konu-yok", action="store_true", help="Konu aramasini atla")
    a = ayrist.parse_args()

    if not a.adres and not a.kaynak_json:
        ayrist.error("adres ya da --kaynak-json vermelisiniz")

    # [1] kaynak
    if a.kaynak_json:
        print(f"[1/4] Kaynak dosyadan okunuyor: {a.kaynak_json}")
        try:
            kaynak = json.loads(Path(a.kaynak_json).read_text(encoding="utf-8"))["kaynak"]
        except Exception as e:
            print(f"  HATA: {e}", file=sys.stderr)
            return 1
    else:
        print(f"[1/4] Kaynak indiriliyor: {a.adres}")
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

    # [2] taslak
    if a.yalniz_ayikla:
        print("[2/4] Atlandi (--yalniz-ayikla)")
    elif a.saglayici == "skill":
        print("[2/4] Skill zinciri: uret -> denetle -> duzelt (anahtarsiz)...")
        try:
            import yz_skill
            paket.update(yz_skill.taslak_uret_skill(kaynak))
            for t in paket["uretim"]["turlar"]:
                print(f"      tur {t['tur']}: {t['bulgu_sayisi']} bulgu")
        except Exception as e:
            print(f"  HATA: {e}", file=sys.stderr)
            return 3
    elif a.saglayici == "cli":
        print("[2/4] Taslak uretiliyor (yerel claude CLI — anahtar kullanilmiyor)...")
        try:
            import yz_cli
            paket.update(yz_cli.taslak_uret_cli(kaynak))
        except Exception as e:
            print(f"  HATA: {e}", file=sys.stderr)
            return 3
    elif a.saglayici == "kural":
        print("[2/4] Taslak kuruluyor (kural motoru — model kullanilmiyor)...")
        paket.update(taslak_uret_kural(kaynak))
    else:
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            print("  HATA: ANTHROPIC_API_KEY tanimli degil.\n"
                  "        setx ANTHROPIC_API_KEY \"sk-ant-...\" ile tanimlayip "
                  "yeni bir terminal acin.\n"
                  "        Anahtarsiz calismak icin: --saglayici kural", file=sys.stderr)
            return 2
        print(f"[2/4] Taslak uretiliyor ({a.model}, efor={a.efor})...")
        try:
            paket.update(taslak_uret(kaynak, a.model, a.efor))
        except Exception as e:
            print(f"  HATA: {e}", file=sys.stderr)
            return 3

    t = paket.get("taslak")
    if t:
        hatalar = sema_dogrula(t)
        if hatalar:
            print("      SEMA UYARISI: " + "; ".join(hatalar[:5]))

    # [3] konu adaylari — baglama yalnizca --konu ile, acik onayla yapilir
    konular = arsiv = None
    if t and not a.konu_yok:
        print("[3/4] Ilgili konular araniyor...")
        konular, arsiv = ke.veri_yukle()
        parmak = ke.parmak_izi(t, kaynak)
        adaylar = ke.ilgili_bul(parmak, konular, arsiv)
        paket["konu_adaylari"] = adaylar
        if not adaylar:
            paket["konu_onerisi"] = ke.konu_onerisi(parmak, t)
            print("      Aday yok. Yeni dosya onerisi hazirlandi "
                  f"(“{paket['konu_onerisi']['ad']}”).")
        for ad in adaylar:
            isaret = "GUCLU" if ad["guclu"] else "olasi"
            print(f"      [{ad['skor']:3d}] {isaret:5s} {ad['tur']:5s} {ad['ad']}")
            for g in ad["gerekceler"]:
                print(f"              - {g}")
        if adaylar and not a.konu:
            print("      Baglanmadi. Baglamak icin: --konu <id>  "
                  "(karar editorundur, arac kendiliginden baglamaz)")
    else:
        print("[3/4] Atlandi")

    if a.konu and t:
        if konular is None:
            konular, arsiv = ke.veri_yukle()
        konu = next((k for k in konular if k["id"] == a.konu), None)
        if not konu:
            print(f"  HATA: “{a.konu}” kimlikli konu yok.", file=sys.stderr)
            return 4
        madde = ke.konuya_bagla(konu, t, kaynak, arsiv)
        ke.veri_yaz(konular, arsiv)
        print(f"      Baglandi: {konu['ad']} · {madde['tarih']} "
              f"({len(konu['maddeler'])} madde)")
        if konu.get("hassas", {}).get("var_mi"):
            print(f"      HASSAS DOSYA: {konu['hassas']['turu']} — {konu['hassas']['uyari']}")

    # [4] yaz
    klasor = Path(a.cikti)
    klasor.mkdir(parents=True, exist_ok=True)
    ad = slugla(
        (t or {}).get("url_slug") or kaynak["orijinal_baslik"] or "taslak"
    )
    yol = klasor / f"{ad}.json"
    yol.write_text(json.dumps(paket, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[4/4] Yazildi: {yol}")
    if t:
        secilen = t["baslik_secenekleri"][t["onerilen_baslik_indeksi"]]["metin"]
        print(f"\n  Onerilen baslik : {secilen or '(kural motoru baslik yazmaz — editor yazacak)'}")
        print(f"  Kategori / ilce : {t['kategori']} / {t['ilce']}")
        print(f"  Onem            : {t['onem']}")
        print(f"  Etiketler       : {', '.join(t['etiketler'])}")
        if t["dogrulanmasi_gerekenler"]:
            print(f"  Dogrulanacak    : {len(t['dogrulanmasi_gerekenler'])} madde")
        if t["hassas_konu"]["var_mi"]:
            print(f"  HASSAS KONU     : {t['hassas_konu']['turu']}")
        if paket.get("tezgah"):
            print(f"  Tezgah          : {len(paket['tezgah'])} ham malzeme cumlesi "
                  "(govde bos birakildi, editor yazacak)")
    print("\n  Bu JSON dosyasini yapay-zeka-editor.html sayfasina surukleyip birakin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
