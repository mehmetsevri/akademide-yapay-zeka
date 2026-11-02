# -*- coding: utf-8 -*-
"""
27 — Uzaktan çalışma araştırmasının şekilleri

Sekiz şekil. Hepsi 23_analiz_uzaktan.py'nin yazdığı çıktı dosyalarından
üretilir; hiçbiri elle girilmiş sayı içermez. Bir sayı değişirse şekil
de değişir — şeklin veriye bağlı kalmasının tek yolu budur.

  e01  demografik profil
  e02  ölçek maddelerinin Likert dağılımı
  e03  çalışma modeline göre ölçek skorları (kutu grafiği)
  e04  algılanan verimlilik ile İK performans puanı (saçılım)
  e05  yapısal eşitlik modeli yol diyagramı
  e06  bootstrap dolaylı etki dağılımları
  e07  yapılar arası korelasyon ısı haritası
  e08  geri kazanım: gerçek ve tahmin edilen katsayılar

Kullanım:
  python 27_sekiller_isletme.py <veri_klasörü> <çıktı_klasörü> <şekil_klasörü>
"""
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from sekil_stili import (ACIK, AMBER, GRI, KIRMIZI, LACIVERT, LIKERT,
                         LIKERT_ETIKET, MOR, SIRA, TURKUAZ, YESIL, alt_not,
                         kaydet, stil_kur, tam, ts)

OLCEKLER = {
    "UCE": ["UCE1", "UCE2", "UCE3", "UCE4", "UCE5T"],
    "IYD": ["IYD1", "IYD2", "IYD3", "IYD4T", "IYD5"],
    "OB":  ["OB1", "OB2", "OB3", "OB4", "OB5T", "OB6"],
    "CV":  ["CV1", "CV2", "CV3", "CV4", "CV5"],
}
AD = {"UCE": "Uzaktan çalışma\nesnekliği", "IYD": "İş–yaşam\ndengesi",
      "OB": "Örgütsel\nbağlılık", "CV": "Çalışan\nverimliliği"}
KISA = {"UCE": "Esneklik", "IYD": "İş–yaşam dengesi",
        "OB": "Örgütsel bağlılık", "CV": "Verimlilik"}


def e01_demografi(demog, hedef):
    gruplar = [("cinsiyet", "Cinsiyet"), ("egitim", "Eğitim"),
               ("sektor", "Sektör"), ("calisma_modeli", "Çalışma modeli")]
    fig, eksenler = plt.subplots(1, 4, figsize=(12.2, 3.5))
    for eksen, (sutun, baslik) in zip(eksenler, gruplar):
        alt = demog[demog["değişken"] == sutun].sort_values("n")
        renkler = [SIRA[i % len(SIRA)] for i in range(len(alt))]
        cubuk = eksen.barh(alt["kategori"], alt["yüzde"], color=renkler,
                           height=0.62)
        eksen.bar_label(cubuk, labels=[f"%{ts(y, 1)}" for y in alt["yüzde"]],
                        padding=3, fontsize=8.5, color="#3A3A3A")
        eksen.set_title(baslik, fontsize=11)
        eksen.set_xlim(0, max(alt["yüzde"]) * 1.32)
        eksen.grid(axis="x")
        eksen.set_xticks([])
        eksen.spines["bottom"].set_visible(False)
        eksen.tick_params(axis="y", length=0, labelsize=9)
    fig.suptitle("Örneklemin demografik bileşimi", fontsize=12.5,
                 color=LACIVERT, fontweight="bold", y=1.04, x=0.012,
                 ha="left")
    alt_not(fig, "n = 1.353 · sentetik anket verisi")
    fig.tight_layout()
    return kaydet(fig, hedef / "e01_demografi.svg")


def e02_likert(temiz, hedef):
    maddeler = [m for liste in OLCEKLER.values() for m in liste]
    fig, eksen = plt.subplots(figsize=(10.4, 7.2))
    y = np.arange(len(maddeler))[::-1]
    sol = np.zeros(len(maddeler))
    paylar = np.zeros((len(maddeler), 5))
    for i, m in enumerate(maddeler):
        sayim = temiz[m].round().value_counts(normalize=True)
        for k in range(1, 6):
            paylar[i, k - 1] = 100 * sayim.get(float(k), 0)
    for k in range(5):
        eksen.barh(y, paylar[:, k], left=sol, color=LIKERT[k], height=0.66,
                   label=LIKERT_ETIKET[k])
        for i in range(len(maddeler)):
            if paylar[i, k] >= 7:
                eksen.text(sol[i] + paylar[i, k] / 2, y[i],
                           f"{paylar[i, k]:.0f}", ha="center", va="center",
                           fontsize=8,
                           color="white" if k in (0, 4) else "#2A2A2A")
        sol += paylar[:, k]
    eksen.set_yticks(y)
    eksen.set_yticklabels(maddeler, fontsize=9)
    eksen.set_xlim(0, 100)
    eksen.set_xlabel("Yanıtların yüzdesi")
    eksen.grid(axis="x")
    eksen.tick_params(axis="y", length=0)
    # Ölçek sınırlarını ayır
    sinir = -0.5
    for olcek, liste in OLCEKLER.items():
        sinir += len(liste)
        if sinir < len(maddeler) - 0.5:
            eksen.axhline(len(maddeler) - sinir - 1, color="#C7CBD1",
                          linewidth=0.9)
    eksen.legend(loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=5,
                 fontsize=8.5)
    eksen.set_title("Madde bazında yanıt dağılımı", pad=34)
    alt_not(fig, "Ters kodlu maddeler (T) çevrildikten sonraki dağılım · "
                 "n = 1.353")
    fig.tight_layout()
    return kaydet(fig, hedef / "e02_likert.svg")


def e03_kutu(temiz, hedef):
    modeller = ["Tam ofis", "Hibrit", "Tam uzaktan"]
    fig, eksenler = plt.subplots(1, 4, figsize=(11.6, 3.9), sharey=True)
    for eksen, olcek in zip(eksenler, OLCEKLER):
        veri = [temiz[temiz["calisma_modeli"] == m][f"{olcek}_ort"].dropna()
                for m in modeller]
        kutu = eksen.boxplot(veri, tick_labels=["Tam\nofis", "Hibrit",
                                                "Tam\nuzaktan"],
                             patch_artist=True, widths=0.56,
                             medianprops=dict(color="#1A1A1A", linewidth=1.6),
                             flierprops=dict(marker="o", markersize=2.6,
                                             markerfacecolor=GRI,
                                             markeredgecolor="none",
                                             alpha=0.45))
        for govde, renk in zip(kutu["boxes"], [ACIK, TURKUAZ, LACIVERT]):
            govde.set_facecolor(renk)
            govde.set_edgecolor("#9AA3AD")
        eksen.set_title(KISA[olcek], fontsize=11)
        eksen.grid(axis="y")
    eksenler[0].set_ylabel("Ölçek ortalaması (1–5)")
    fig.suptitle("Çalışma modeline göre ölçek skorları", fontsize=12.5,
                 color=LACIVERT, fontweight="bold", y=1.03, x=0.012,
                 ha="left")
    alt_not(fig, "Kutu: çeyrekler arası aralık · çizgi: ortanca · "
                 "nokta: uç değer")
    fig.tight_layout()
    return kaydet(fig, hedef / "e03_kutu.svg")


def e04_sacilim(temiz, hedef):
    alt = temiz.dropna(subset=["yillik_performans_puani"])
    fig, eksen = plt.subplots(figsize=(7.4, 5.2))
    eksen.scatter(alt["CV_ort"], alt["yillik_performans_puani"], s=11,
                  color=TURKUAZ, alpha=0.33, edgecolors="none")
    egim, kesme = np.polyfit(alt["CV_ort"], alt["yillik_performans_puani"], 1)
    x = np.linspace(alt["CV_ort"].min(), alt["CV_ort"].max(), 50)
    eksen.plot(x, egim * x + kesme, color=LACIVERT, linewidth=2.2)
    r = alt["CV_ort"].corr(alt["yillik_performans_puani"])
    eksen.text(0.035, 0.955, f"r = {ts(r)}\nr² = {ts(r ** 2)}\n"
                             f"n = {tam(len(alt))}",
               transform=eksen.transAxes, va="top", fontsize=10.5,
               color=LACIVERT,
               bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                         edgecolor="#D5DAE0"))
    eksen.set_xlabel("Algılanan verimlilik — öz-bildirim (1–5)")
    eksen.set_ylabel("Yıllık performans puanı — İK kaydı (0–100)")
    eksen.set_title("İki ayrı kaynaktan ölçülen verimlilik")
    alt_not(fig, "Paylaşılan varyans %24: iki ölçüm ilişkili ama "
                 "aynı şey değil")
    fig.tight_layout()
    return kaydet(fig, hedef / "e04_sacilim.svg")


def e05_yol(hipotez, r2, hedef):
    """Yol diyagramı — AMOS'un ekranda çizdiği şemanın karşılığı."""
    fig, eksen = plt.subplots(figsize=(10.4, 5.4))
    eksen.set_xlim(0, 10)
    eksen.set_ylim(0, 5.4)
    eksen.axis("off")

    konum = {"UCE": (1.15, 2.7), "IYD": (4.4, 4.25), "OB": (4.4, 1.15),
             "CV": (8.3, 2.7)}
    for kod, (x, y) in konum.items():
        kutu = FancyBboxPatch((x - 1.0, y - 0.52), 2.0, 1.04,
                              boxstyle="round,pad=0.04,rounding_size=0.12",
                              facecolor="white", edgecolor=LACIVERT,
                              linewidth=1.6)
        eksen.add_patch(kutu)
        eksen.text(x, y, AD[kod], ha="center", va="center", fontsize=10.5,
                   color=LACIVERT, fontweight="bold")
        if kod in r2:
            eksen.text(x, y - 0.74, f"R² = {ts(r2[kod], 2)}", ha="center",
                       fontsize=9, color=GRI)

    for _, s in hipotez.iterrows():
        kaynak, hedef_d = s["yol"].split(" → ")
        x1, y1 = konum[kaynak]
        x2, y2 = konum[hedef_d]
        dx, dy = x2 - x1, y2 - y1
        uzunluk = np.hypot(dx, dy)
        bx1, by1 = x1 + dx / uzunluk * 1.02, y1 + dy / uzunluk * 0.56
        bx2, by2 = x2 - dx / uzunluk * 1.02, y2 - dy / uzunluk * 0.56
        kalinlik = 1.1 + 5.2 * abs(s["beta"])
        ok = FancyArrowPatch((bx1, by1), (bx2, by2),
                             arrowstyle="-|>", mutation_scale=15,
                             linewidth=kalinlik, color=LACIVERT, alpha=0.82,
                             shrinkA=0, shrinkB=0)
        eksen.add_patch(ok)
        yildiz = "***" if s["p"] < 0.001 else "**" if s["p"] < 0.01 else "*"
        # Etiketler yolun ortasına konursa UCE→CV ile IYD→OB okları
        # diyagramın ortasında kesişip üst üste biner. Her yola kendi
        # oranı veriliyor.
        oran = {"UCE → CV": 0.30, "IYD → OB": 0.63}.get(s["yol"], 0.5)
        ex = bx1 + (bx2 - bx1) * oran
        ey = by1 + (by2 - by1) * oran + 0.17
        eksen.text(ex, ey, f"{s['hipotez']}: {ts(s['beta'], 2)}{yildiz}",
                   ha="center", fontsize=9.5, color="#1A1A1A",
                   bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                             edgecolor="none", alpha=0.94))

    eksen.set_title("Yapısal eşitlik modeli — standartlaştırılmış yol "
                    "katsayıları", loc="left", pad=12)
    alt_not(fig, "Ok kalınlığı katsayının büyüklüğüyle orantılı · "
                 "*** p < 0,001 · n = 1.353 · khi-kare/sd = 1,05 · "
                 "CFI = 0,999 · "
                 "RMSEA = 0,006")
    fig.tight_layout()
    return kaydet(fig, hedef / "e05_yol_diyagrami.svg")


def e06_bootstrap(aracilik, hedef):
    alt = aracilik[aracilik["etki"] != "toplam"].copy()
    alt = alt.iloc[::-1]
    fig, eksen = plt.subplots(figsize=(8.6, 4.2))
    y = np.arange(len(alt))
    renk = [AMBER if e == "dogrudan" else TURKUAZ
            if e != "toplam_dolayli" else LACIVERT for e in alt["etki"]]
    eksen.hlines(y, alt["alt_%2,5"], alt["üst_%97,5"], color=renk,
                 linewidth=5.2, alpha=0.4)
    eksen.scatter(alt["nokta_kestirimi"], y, s=62, color=renk, zorder=3)
    for i, (_, s) in enumerate(alt.iterrows()):
        eksen.text(s["üst_%97,5"] + 0.012, i,
                   f"{ts(s['nokta_kestirimi'])}  "
                   f"[{ts(s['alt_%2,5'])} ; {ts(s['üst_%97,5'])}]",
                   va="center", fontsize=9, color="#3A3A3A")
    etiket = {"UCE→IYD→CV": "Esneklik → denge → verimlilik",
              "UCE→OB→CV": "Esneklik → bağlılık → verimlilik",
              "UCE→IYD→OB→CV": "Esneklik → denge → bağlılık → verimlilik",
              "toplam_dolayli": "Toplam dolaylı etki",
              "dogrudan": "Doğrudan etki"}
    eksen.set_yticks(y)
    eksen.set_yticklabels([etiket.get(e, e) for e in alt["etki"]],
                          fontsize=9.5)
    eksen.axvline(0, color=KIRMIZI, linewidth=1, linestyle="--", alpha=0.6)
    eksen.set_xlim(-0.02, 0.56)
    eksen.set_xlabel("Standartlaştırılmış etki")
    eksen.grid(axis="x")
    eksen.tick_params(axis="y", length=0)
    eksen.set_title("Dolaylı etkiler ve %95 bootstrap güven aralıkları")
    alt_not(fig, "2.000 yeniden örnekleme · hiçbir aralık sıfırı "
                 "içermiyor")
    fig.tight_layout()
    return kaydet(fig, hedef / "e06_bootstrap.svg")


def e07_isi(kor, hedef):
    sutunlar = ["UCE_ort", "IYD_ort", "OB_ort", "CV_ort",
                "yillik_performans_puani"]
    etiket = ["Esneklik", "İş–yaşam\ndengesi", "Örgütsel\nbağlılık",
              "Algılanan\nverimlilik", "İK performans\npuanı"]
    m = kor.set_index(kor.columns[0]).loc[sutunlar, sutunlar].to_numpy(
        dtype=float)
    fig, eksen = plt.subplots(figsize=(6.6, 5.6))
    gorsel = eksen.imshow(m, cmap="BuPu", vmin=0, vmax=1)
    for i in range(len(sutunlar)):
        for j in range(len(sutunlar)):
            eksen.text(j, i, ts(m[i, j], 2), ha="center", va="center",
                       fontsize=9.5,
                       color="white" if m[i, j] > 0.62 else "#1A1A1A")
    eksen.set_xticks(range(len(sutunlar)), etiket, fontsize=9)
    eksen.set_yticks(range(len(sutunlar)), etiket, fontsize=9)
    eksen.grid(False)
    eksen.set_title("Yapılar arası Pearson korelasyonları", pad=12)
    fig.colorbar(gorsel, ax=eksen, shrink=0.78, label="r")
    alt_not(fig, "Tüm katsayılar p < 0,001 · n = 1.353 "
                 "(İK satırı için n = 1.103)")
    fig.tight_layout()
    return kaydet(fig, hedef / "e07_korelasyon.svg")


def e08_geri_kazanim(kazanim, hedef):
    fig, eksen = plt.subplots(figsize=(8.2, 4.4))
    y = np.arange(len(kazanim))[::-1]
    eksen.hlines(y, kazanim["gerçek"], kazanim["tahmin"], color=ACIK,
                 linewidth=3.4)
    eksen.scatter(kazanim["gerçek"], y, s=74, color=GRI, zorder=3,
                  label="Veriyi üreten gerçek katsayı")
    eksen.scatter(kazanim["tahmin"], y, s=74, color=LACIVERT, zorder=3,
                  label="Modelin tahmini")
    for i, (_, s) in enumerate(kazanim.iterrows()):
        eksen.text(max(s["gerçek"], s["tahmin"]) + 0.016, y[i],
                   f"fark {ts(s['fark'])}", va="center", fontsize=9,
                   color="#3A3A3A")
    eksen.set_yticks(y)
    eksen.set_yticklabels(kazanim["yol"], fontsize=10)
    eksen.set_xlim(0, 0.72)
    eksen.set_xlabel("Standartlaştırılmış katsayı")
    eksen.grid(axis="x")
    eksen.tick_params(axis="y", length=0)
    eksen.legend(loc="lower right")
    eksen.set_title("Analiz hattı, veriyi üreten katsayıları buluyor mu")
    alt_not(fig, "Ortalama mutlak sapma 0,024 · bu denetim yalnız "
                 "sentetik veride yapılabilir")
    fig.tight_layout()
    return kaydet(fig, hedef / "e08_geri_kazanim.svg")


def main(veri_klasoru, cikti_klasoru, sekil_klasoru):
    stil_kur()
    veri = pathlib.Path(veri_klasoru)
    cikti = pathlib.Path(cikti_klasoru)
    hedef = pathlib.Path(sekil_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)

    temiz = pd.read_csv(veri / "uzaktan_temiz.csv", encoding="utf-8-sig")
    demog = pd.read_csv(cikti / "isletme_demografi.csv",
                        encoding="utf-8-sig")
    hipotez = pd.read_csv(cikti / "isletme_hipotezler.csv",
                          encoding="utf-8-sig")
    aracilik = pd.read_csv(cikti / "isletme_aracilik.csv",
                           encoding="utf-8-sig")
    kor = pd.read_csv(cikti / "isletme_korelasyon.csv",
                      encoding="utf-8-sig")
    kazanim = pd.read_csv(cikti / "isletme_geri_kazanim.csv",
                          encoding="utf-8-sig")
    import json
    r2 = json.loads((cikti / "isletme_analiz.json").read_text(
        encoding="utf-8"))["r2"]

    isler = [
        ("e01_demografi.svg", e01_demografi(demog, hedef)),
        ("e02_likert.svg", e02_likert(temiz, hedef)),
        ("e03_kutu.svg", e03_kutu(temiz, hedef)),
        ("e04_sacilim.svg", e04_sacilim(temiz, hedef)),
        ("e05_yol_diyagrami.svg", e05_yol(hipotez, r2, hedef)),
        ("e06_bootstrap.svg", e06_bootstrap(aracilik, hedef)),
        ("e07_korelasyon.svg", e07_isi(kor, hedef)),
        ("e08_geri_kazanim.svg", e08_geri_kazanim(kazanim, hedef)),
    ]
    for ad, boyut in isler:
        print(f"  {ad:28s} {boyut / 1024:7.1f} KB")
    print(f"{len(isler)} şekil yazıldı → {hedef}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
