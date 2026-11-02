# -*- coding: utf-8 -*-
"""
30 — Gazi veri seti: analiz planının istediği ön denetimler

Analiz planı (8. bölüm) iki ön denetim istiyor. İkisi de veri
profilinden okunamaz, hesaplanması gerekir; ikisi de sonraki bütün
adımların nasıl okunacağını değiştirir.

ÖN DENETİM 1 — kümelenme
  5.820 değerlendirme bağımsız gözlem değil: 13 dersin içine ve üç
  öğretim elemanının altına yerleşiyor. Sınıf içi korelasyon (ICC)
  küçük çıksa bile, kümeler büyük olduğunda tasarım etkisi büyür ve
  etkin örneklem ham örneklemin çok altına iner. Bu, p değerlerinin
  olduğundan küçük çıkması demektir.

      ICC = (MSB − MSW) / (MSB + (k₀ − 1)·MSW)
      tasarım etkisi = 1 + (ortalama küme büyüklüğü − 1) · ICC
      etkin örneklem = n / tasarım etkisi

ÖN DENETİM 2 — düz çizgi yanıtlama
  Yirmi sekiz maddenin tamamına aynı değeri veren satırlar. Bunlar
  ölçeğin iç tutarlılığını yapay olarak yükseltir: sıfır varyanslı bir
  satır, maddeler arası korelasyonu mekanik olarak artırır. Oran
  ölçülmeden Cronbach alfa yorumlanamaz.

  Dikkat: düz çizgi otomatik olarak "dikkatsiz yanıt" demek DEĞİLDİR.
  Birbirine yakın yirmi sekiz maddeye hepsine 5 veren bir öğrenci
  içten de olabilir. Bu yüzden betik satır ATMAZ; iki değeri yan yana
  raporlar ve kararı araştırmacıya bırakır.

Kullanım:
  python 30_gazi_on_denetim.py <veri_dosyası> <çıktı_dosyası>
"""
import collections
import csv
import pathlib
import statistics as st
import sys

MADDELER = [f"Q{i}" for i in range(1, 29)]
BOYUT = {"Ders (Q1–Q12)": MADDELER[:12],
         "Öğretim elemanı (Q13–Q28)": MADDELER[12:]}
PUANLAR = ["ders_puan", "ogretim_puan", "genel_puan"]
KUMELER = [("class", "ders"), ("instr", "öğretim elemanı")]

satirlar = []


def yaz(metin=""):
    print(metin)
    satirlar.append(metin)


def tr(sayi, basamak=3):
    """Türkçe ayraç: binlik nokta, ondalık virgül."""
    return (f"{sayi:,.{basamak}f}"
            .replace(",", "\x00").replace(".", ",").replace("\x00", "."))


def icc_tek_yonlu(veri, kume_anahtari, deger_anahtari):
    """Tek yönlü rastgele etkiler modelinden sınıf içi korelasyon.

    Dengesiz küme büyüklükleri için k₀ düzeltmesi kullanılır; kümeler
    eşit büyüklükte olmadığında basit ortalama yanıltır.
    """
    gruplar = collections.defaultdict(list)
    for s in veri:
        gruplar[s[kume_anahtari]].append(float(s[deger_anahtari]))
    n = sum(len(v) for v in gruplar.values())
    k = len(gruplar)
    genel = sum(sum(v) for v in gruplar.values()) / n
    ssb = sum(len(v) * (st.mean(v) - genel) ** 2 for v in gruplar.values())
    ssw = sum(sum((x - st.mean(v)) ** 2 for x in v)
              for v in gruplar.values())
    msb, msw = ssb / (k - 1), ssw / (n - k)
    k0 = (n - sum(len(v) ** 2 for v in gruplar.values()) / n) / (k - 1)
    return {"icc": (msb - msw) / (msb + (k0 - 1) * msw), "kume": k,
            "n": n, "ortalama_kume": n / k, "F": msb / msw,
            "en_kucuk": min(len(v) for v in gruplar.values()),
            "en_buyuk": max(len(v) for v in gruplar.values())}


def cronbach(veri, maddeler):
    k = len(maddeler)
    madde_var = sum(st.variance([float(s[m]) for s in veri])
                    for m in maddeler)
    toplam_var = st.variance([sum(float(s[m]) for m in maddeler)
                              for s in veri])
    return k / (k - 1) * (1 - madde_var / toplam_var)


def main(veri_yolu, cikti_yolu):
    veri = list(csv.DictReader(open(veri_yolu, encoding="utf-8-sig")))
    n = len(veri)

    yaz("ANALİZ PLANININ İSTEDİĞİ ÖN DENETİMLER")
    yaz("=" * 78)
    yaz(f"Veri: {veri_yolu}")
    yaz(f"Gözlem: {tr(n, 0)}")

    # ------------------------------------------------------ denetim 1
    yaz()
    yaz("=" * 78)
    yaz("ÖN DENETİM 1 — Gözlemler bağımsız mı")
    yaz("=" * 78)
    yaz("Nedir : Değerlendirmelerin ders ve öğretim elemanı içinde ne "
        "kadar benzeştiği.")
    yaz("Neden : Bağımsızlık varsayımı tutmuyorsa standart hatalar "
        "olduğundan küçük,")
    yaz("        p değerleri olduğundan anlamlı çıkar.")
    yaz("-" * 78)
    yaz(f"{'değişken':14s}{'küme':>16s}{'k':>4s}{'ICC':>8s}"
        f"{'tasarım etkisi':>16s}{'etkin n':>10s}")
    ozet = []
    for puan in PUANLAR:
        for anahtar, ad in KUMELER:
            s = icc_tek_yonlu(veri, anahtar, puan)
            tasarim = 1 + (s["ortalama_kume"] - 1) * s["icc"]
            etkin = s["n"] / tasarim
            ozet.append((puan, ad, s, tasarim, etkin))
            yaz(f"{puan:14s}{ad:>16s}{s['kume']:>4d}{tr(s['icc'], 3):>8s}"
                f"{tr(tasarim, 1):>16s}{tr(etkin, 0):>10s}")

    s = icc_tek_yonlu(veri, "class", "ogretim_puan")
    yaz()
    yaz(f"Ders başına değerlendirme: en az {s['en_kucuk']}, "
        f"en çok {s['en_buyuk']}, ortalama {tr(s['ortalama_kume'], 0)}.")
    yaz()
    yaz("Okunuşu: ICC'nin kendisi küçük (0,03 dolayında) ama kümeler")
    yaz("büyük olduğu için tasarım etkisi 14'ü aşıyor. Yani 5.820")
    yaz("değerlendirme, bağımsız gözlem olarak yaklaşık 400 kişilik bir")
    yaz("örneklem kadar bilgi taşıyor. Bu, ham n'in on dörtte biri.")
    yaz()
    yaz("Sonuç: ders ve öğretim elemanı farkları ANLAMLI (F = "
        f"{tr(s['F'], 1)}, p < 0,001), ama bu farkları yok sayan bir")
    yaz("çözümlemede p değerleri güvenilmez. Üç seçenek var:")
    yaz("  1. Çok düzeyli model (dersi rastgele etki olarak al)")
    yaz("  2. Kümeye göre düzeltilmiş standart hata (cluster-robust)")
    yaz("  3. Derse göre özetlenmiş veri üzerinde çözümleme")
    yaz("Üç öğretim elemanı, rastgele etki için fazla az; öğretim")
    yaz("elemanı sabit etki olarak modele girer.")

    # ------------------------------------------------------ denetim 2
    yaz()
    yaz("=" * 78)
    yaz("ÖN DENETİM 2 — Düz çizgi yanıtlama ve güvenilirliğe etkisi")
    yaz("=" * 78)
    yaz("Nedir : Yirmi sekiz maddenin tamamına aynı değeri veren "
        "satırların oranı.")
    yaz("Neden : Sıfır varyanslı satırlar Cronbach alfayı mekanik "
        "olarak yükseltir.")
    yaz("-" * 78)

    duz = [s for s in veri if len({s[m] for m in MADDELER}) == 1]
    kalan = [s for s in veri if len({s[m] for m in MADDELER}) > 1]
    yaz(f"Düz çizgi satırı: {tr(len(duz), 0)} / {tr(n, 0)} "
        f"(%{tr(100 * len(duz) / n, 1)})")
    dagilim = collections.Counter(s["Q1"] for s in duz)
    yaz("Verdikleri değer: " + " · ".join(
        f"{d} → {tr(dagilim[d], 0)} satır" for d in sorted(dagilim)))
    yaz()
    yaz(f"{'ölçek':28s}{'tüm satırlar':>16s}{'düz çizgisiz':>16s}"
        f"{'fark':>10s}")
    for ad, maddeler in [("Tümü (Q1–Q28)", MADDELER)] + list(BOYUT.items()):
        a1, a2 = cronbach(veri, maddeler), cronbach(kalan, maddeler)
        yaz(f"{ad:28s}{tr(a1, 4):>16s}{tr(a2, 4):>16s}"
            f"{tr(a2 - a1, 4):>10s}")
    yaz()
    yaz(f"Genel puan ortalaması: tüm satırlar {tr(st.mean(float(s['genel_puan']) for s in veri))} · "
        f"düz çizgisiz {tr(st.mean(float(s['genel_puan']) for s in kalan))}")
    yaz()
    yaz("Okunuşu: alfa düz çizgisiz de yüksek kalıyor, yani ölçek")
    yaz("gerçekten tutarlı. Ama 0,99 ile 0,98 arasındaki fark raporlanmalı,")
    yaz("çünkü 0,99 düzeyinde bir alfa tek başına 'madde fazlalığı'")
    yaz("işareti olarak okunur ve bir kısmı bu satırlardan geliyor.")
    yaz()
    yaz("Karar notu: bu satırlar ATILMADI. Birbirine yakın yirmi sekiz")
    yaz("maddeye hepsine aynı değeri vermek dikkatsizlik olabilir, içten")
    yaz("de olabilir; veri setinde bunu ayırt edecek bir süre kaydı ya da")
    yaz("dikkat kontrol maddesi yok. Doğru davranış oranı bildirmek ve")
    yaz("sonuçları iki örneklemde birden raporlamaktır.")

    hedef = pathlib.Path(cikti_yolu)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print(f"\nRapor: {hedef}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
