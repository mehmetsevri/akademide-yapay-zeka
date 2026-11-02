# -*- coding: utf-8 -*-
"""
31 — Üç sayıyı ikinci bir yoldan hesaplama

"Yapay zekânın yazdığı kod doğru mu" sorusunun en ucuz yanıtı: aynı
sayıyı başka bir araçla bir kez daha hesaplamak. SPSS ya da jamovi
elinizdeyse orada koşturun. Yoksa bu betik işi görür.

Betiğin tek özelliği, 05_analiz_sosyal.py ile HİÇBİR ŞEY paylaşmaması.
O betik pandas, numpy, scipy ve statsmodels kullanıyor. Bu betik
yalnız Python'un kendi kütüphanelerini kullanıyor: csv, statistics,
math. Ortak bir kütüphanede hata varsa iki betik de aynı yanlışı
verirdi; paylaşmadıkları için vermezler.

Üç sayı seçildi, çünkü üçü üç ayrı aileden:
  Cronbach alfa   — varyans toplamları
  ANOVA F         — kareler toplamı ayrıştırması
  Pearson r       — çapraz çarpımlar

Kurulum gerekmez; herhangi bir Python 3 ile çalışır.

Kullanım:
  python 31_bagimsiz_dogrulama.py <veri_dosyası> <çıktı_dosyası>
"""
import collections
import csv
import math
import pathlib
import statistics as st
import sys

# 05_analiz_sosyal.py'nin bildirdiği değerler. Elle buraya yazıldı.
#
# Bu listenin ELLE yazılmış olması bir kusur değil, denetimin bir
# parçası: aktarma da hata yapılabilecek bir adımdır ve bu betik ilk
# koşumunda tam olarak onu yakaladı. Pearson r için 0,1818 yazılmıştı;
# ana rapordaki değer 0,200. Betik "AYRIŞIYOR" dedi, kaynağa bakıldı,
# hatanın hesapta değil aktarmada olduğu görüldü.
#
# Ayrışma gördüğünüzde bakılacak sıra budur: önce aktarma, sonra
# hangi satırların kullanıldığı, en son hesabın kendisi.
BEKLENEN = {
    "alfa_ders": 0.9828,
    "alfa_ogretim": 0.9909,
    "alfa_tum": 0.9920,
    "anova_F": 57.797,
    "anova_sd1": 4,
    "anova_sd2": 5815,
    "r_katilim_ogretim": 0.200,
}

MADDELER = [f"Q{i}" for i in range(1, 29)]
satirlar = []


def yaz(metin=""):
    print(metin)
    satirlar.append(metin)


def tr(sayi, basamak=4):
    return f"{sayi:.{basamak}f}".replace(".", ",")


def cronbach(veri, maddeler):
    """α = k/(k−1) · (1 − Σσ²ᵢ / σ²toplam)"""
    k = len(maddeler)
    madde_var = sum(st.variance([float(s[m]) for s in veri])
                    for m in maddeler)
    toplam_var = st.variance([sum(float(s[m]) for m in maddeler)
                              for s in veri])
    return k / (k - 1) * (1 - madde_var / toplam_var)


def tek_yonlu_anova(veri, grup, deger):
    """F = (SSB/(k−1)) / (SSW/(N−k)); yanında eta kare."""
    g = collections.defaultdict(list)
    for s in veri:
        g[s[grup]].append(float(s[deger]))
    n = sum(len(v) for v in g.values())
    k = len(g)
    genel = sum(sum(v) for v in g.values()) / n
    ssb = sum(len(v) * (st.mean(v) - genel) ** 2 for v in g.values())
    ssw = sum(sum((x - st.mean(v)) ** 2 for x in v) for v in g.values())
    return ((ssb / (k - 1)) / (ssw / (n - k)), k - 1, n - k,
            ssb / (ssb + ssw))


def pearson(veri, a, b):
    x = [float(s[a]) for s in veri]
    y = [float(s[b]) for s in veri]
    mx, my = st.mean(x), st.mean(y)
    pay = sum((u - mx) * (v - my) for u, v in zip(x, y))
    payda = math.sqrt(sum((u - mx) ** 2 for u in x)
                      * sum((v - my) ** 2 for v in y))
    return pay / payda


def kiyas(ad, bulunan, beklenen, basamak=4):
    fark = abs(bulunan - beklenen)
    durum = "UYUYOR" if fark < 5 * 10 ** -basamak else "AYRIŞIYOR"
    yaz(f"  {ad:34s}{tr(bulunan, basamak):>12s}"
        f"{tr(beklenen, basamak):>12s}{tr(fark, basamak):>12s}  {durum}")
    return durum == "UYUYOR"


def main(veri_yolu, cikti_yolu):
    veri = list(csv.DictReader(open(veri_yolu, encoding="utf-8-sig")))
    yaz("BAĞIMSIZ DOĞRULAMA")
    yaz("=" * 78)
    yaz("Bu betik yalnız Python'un standart kütüphanesini kullanır:")
    yaz("csv, statistics, math. pandas, numpy, scipy ve statsmodels")
    yaz("kullanılmadı — 05_analiz_sosyal.py ile ortak bir bağımlılık yok.")
    yaz(f"Gözlem: {len(veri)}")
    yaz()
    yaz(f"  {'ölçüm':34s}{'bu betik':>12s}{'ana betik':>12s}"
        f"{'fark':>12s}")
    yaz("  " + "-" * 74)

    hepsi = []
    hepsi.append(kiyas("Cronbach α — Ders (Q1–Q12)",
                       cronbach(veri, MADDELER[:12]),
                       BEKLENEN["alfa_ders"]))
    hepsi.append(kiyas("Cronbach α — Öğr. elemanı (Q13–Q28)",
                       cronbach(veri, MADDELER[12:]),
                       BEKLENEN["alfa_ogretim"]))
    hepsi.append(kiyas("Cronbach α — tüm ölçek (28 madde)",
                       cronbach(veri, MADDELER), BEKLENEN["alfa_tum"]))

    F, sd1, sd2, eta = tek_yonlu_anova(veri, "difficulty", "ders_puan")
    hepsi.append(kiyas("ANOVA F — ders puanı ~ güçlük", F,
                       BEKLENEN["anova_F"], 3))
    sd_uyum = (sd1 == BEKLENEN["anova_sd1"]
               and sd2 == BEKLENEN["anova_sd2"])
    hepsi.append(sd_uyum)
    yaz(f"  {'  serbestlik derecesi':34s}{str(sd1) + ', ' + str(sd2):>12s}"
        f"{str(BEKLENEN['anova_sd1']) + ', ' + str(BEKLENEN['anova_sd2']):>12s}"
        f"{'':>12s}  {'UYUYOR' if sd_uyum else 'AYRIŞIYOR'}")

    hepsi.append(kiyas("Pearson r — katılım ↔ öğretim puanı",
                       pearson(veri, "attendance", "ogretim_puan"),
                       BEKLENEN["r_katilim_ogretim"], 3))

    yaz()
    yaz(f"Eta kare (ANOVA): {tr(eta)} — ana betikte raporlanan etki "
        f"büyüklüğüyle birlikte okunur.")
    yaz()
    if all(hepsi):
        yaz("SONUÇ: altı ölçümün altısı da uyuyor.")
        yaz()
        yaz("Bu, kodun doğru olduğunu KANITLAMAZ; iki hesabın aynı")
        yaz("sonuca vardığını gösterir. Kanıt için üçüncü bir yol gerekir:")
        yaz("aynı veriyi SPSS ya da jamovi'ye yükleyip oradaki çıktıyla")
        yaz("karşılaştırmak. Ama bu kadarı bile en sık görülen hataları")
        yaz("yakalar: yanlış sütun seçimi, sessizce düşen satırlar,")
        yaz("yanlış serbestlik derecesi.")
    else:
        yaz("SONUÇ: EN AZ BİR ÖLÇÜM AYRIŞIYOR. Önce hangi betiğin")
        yaz("hangi satırları kullandığına bakın; en sık neden budur.")

    yaz()
    yaz("Serbestlik derecesini ayrıca kontrol etmek önemli: iki betik")
    yaz("aynı F'yi verip farklı sd bildiriyorsa biri satır düşürmüştür")
    yaz("ve bu, sayıya bakarak anlaşılmaz.")

    hedef = pathlib.Path(cikti_yolu)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print(f"\nRapor: {hedef}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
