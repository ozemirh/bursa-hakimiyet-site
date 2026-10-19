"""Gunicorn yapılandırması — Bursa Hakimiyet (YALNIZ DOSYA, kurulmadı).

systemd birimi bunu `-c` ile okur (dagitim/systemd/bursahakimiyet.service).

İşçi türü `sync`: sayfa sunucuda çizilir, istek kısa; nginx yanıtı tamponlar
(`proxy_buffering on`) ve yavaş okur işçiyi tutmaz. İşçi sayısı 2×çekirdek+1
(4 vCPU → 9). Uzun süren tek tip istek bugün arama; nginx onu IP başına
sınırlıyor ve `timeout` takılan işçiyi 30 sn'de öldürüp yeniler.
"""

import multiprocessing
import os

# TCP, yalnız yerel arayüz. Unix soketi yerine TCP: Django'nun okunma
# sayacı vekil başlığına yalnız REMOTE_ADDR güvenilir vekilse bakar
# (BH_GUVENILIR_VEKIL=127.0.0.1,::1); unix soketinde REMOTE_ADDR boş gelir.
bind = "127.0.0.1:8001"

workers = int(os.environ.get("BH_ISCI", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
timeout = 30
graceful_timeout = 30
keepalive = 2

# Bellek sızıntısına karşı işçi belirli istek sayısından sonra yenilenir;
# hepsi aynı anda yenilenmesin diye rastgele kayma.
max_requests = 2000
max_requests_jitter = 200

# Kod bir kez yüklenip işçilere çatallanır: açılış hızlı, bellek paylaşılır.
# Veritabanı bağlantısı çatallamadan ÖNCE açılmaz (Django tembel bağlanır).
preload_app = True

# Günlük: journald (stdout/stderr). Erişim günlüğü nginx'te; burada yalnız
# hata. Yavaş sayfa avı gerekirse geçici olarak:
#   accesslog = "-"; access_log_format = '%(r)s %(s)s %(D)sµs'
accesslog = None
errorlog = "-"
loglevel = "info"

# Vekil başlıkları yalnız yerel nginx'ten gelir (unix soketi).
forwarded_allow_ips = "127.0.0.1,::1"

proc_name = "bursahakimiyet"
