# -*- coding: utf-8 -*-
"""Yapay zekâ taslağının K2 bulgularını kapatan panel ucu — 19 Ekim 2026, Paket M.

`panel.py`'den ayrı tutuldu: o dosya başka işlerle eşzamanlı değişiyor ve
bu uç tek bir fiil. Bulgu listesi taslak ekranında
(`panel/yz_taslak_detay.html`) `haber.yz_koken` üzerinden okunur.

**Tek tek, gerekçeli.** Her bulgu kendi düğmesiyle kapanır; "hepsini kapat"
yok. Kapatan kullanıcı ve zaman bulgunun kaydında ve denetim kaydında
(`yz_bulgu_kapatma`) kalır. Kapatmak "kaynağa baktım, doğru" demektir;
olgu yanlışsa doğrusu haber formunda düzeltilir, bulgu ondan sonra kapanır.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect

from . import denetim_kaydi, yz_koken
from .models import YzBulgu


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def bulgu_kapat(request, kimlik, bulgu):
    """Yalnız POST: karar bağlantıyla verilmez."""
    if request.method != "POST":
        return redirect("panel-yz-taslak", kimlik=kimlik)
    kayit = get_object_or_404(YzBulgu.objects.select_related("koken"),
                              pk=bulgu, koken__haber_id=kimlik)
    if yz_koken.bulgu_kapat(kayit, request.user):
        denetim_kaydi.yaz(request, "yz_bulgu_kapatma", hedef_tur="haber", hedef_id=kimlik,
                          oncesi={"bulgu": kayit.pk, "kapandi": False},
                          sonrasi={"bulgu": kayit.pk, "kapandi": True},
                          gerekce=f"{kayit.kural} {kayit.tur}: {kayit.deger}"[:200])
        kalan = yz_koken.acik_k2_sayisi(kimlik)
        messages.success(request, "Bulgu kapatıldı." + (
            f" {kalan} açık bulgu kaldı." if kalan else
            " Açık bulgu kalmadı; yayın kapısının öteki şartları geçerli."))
    return redirect("panel-yz-taslak", kimlik=kimlik)
