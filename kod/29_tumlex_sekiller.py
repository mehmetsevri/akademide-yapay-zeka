# -*- coding: utf-8 -*-
"""
29 — TUMLEX ön bulgularının şekilleri

TUMLEX, DergiPark'taki Türkçe mühendislik makalelerinde ChatGPT'nin
yayımlanmasından (30 Kasım 2022) önce ve sonra GÖNDERİLEN makaleler
arasındaki yazım değişimini ölçen, hâlâ süren bir çalışma. Buradaki
iki şekil, çalışmanın öz (abstract) düzeyindeki ön bulgularından
üretildi.

ÜÇ ŞEKİL, ÜÇ AYRI İŞ
  t03  havuzlanmış değişim ile dergi içi değişimin karşılaştırması.
       "Dergi karışımı değişmiştir" itirazını doğrudan sınar.
  t01  yıllık seri — eğim grafiği. Asıl soru "oran arttı mı" değil,
       "artış ne zaman başladı". Öncesi dönemin yılları plasebo
       işlevi görür: 2016'dan 2022'ye düzgün bir tırmanış varsa ve
       sonrası onu sürdürüyorsa, bu dilin kendi kaymasıdır.
  t02  konu kayması ile üslup kayması ayrımı. Artan sözcüklerin bir
       kısmı mühendisliğin gündeminin değişmesidir (makine, derin,
       hibrit); yazım izi değildir. İkisini aynı grafikte göstermek
       bulguyu çöpe çevirir, bu yüzden ayrı renklerle ayrıldı.

Kelime bulutu bilerek yapılmadı: bulut SIKLIK kodlar, buradaki bulgu
ise DEĞİŞİM. Sıklık bulutu "bir, ile, olarak" gösterir.

Kullanım:
  python 29_tumlex_sekiller.py <veri_klasörü> <şekil_klasörü>
"""
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from sekil_stili import (ACIK, AMBER, GRI, KIRMIZI, LACIVERT, MOR, TURKUAZ,
                         YESIL, alt_not, kaydet, stil_kur, tam, ts)

# Hangi sütun hangi adla gösterilecek ve hangi renkte
SERILER = [
    ("ortaya_koy", "“ortaya koy…”", KIRMIZI),
    ("bulgular", "“bulgular”", AMBER),
    ("gostermektedir", "“göstermektedir”", MOR),
    ("kritik", "“kritik”", TURKUAZ),
    ("kapsamli", "“kapsamlı”", YESIL),
]
AYRAC = 2022.5          # ChatGPT 30 Kasım 2022


def t01_egim(seri, hedef):
    fig, eksen = plt.subplots(figsize=(10.2, 5.4))
    yil = seri["yil"].to_numpy(dtype=float)

    eksen.axvspan(yil.min() - 0.4, AYRAC, color="#F4F5F7", zorder=0)
    eksen.axvline(AYRAC, color=GRI, linewidth=1.2, linestyle="--", zorder=1)
    eksen.text(AYRAC - 0.12, 46.5, "ChatGPT · 30 Kasım 2022", rotation=90,
               ha="right", va="top", fontsize=9, color=GRI)
    eksen.text(2016.0, 46.5, "Öncesi — plasebo yılları", fontsize=9.5,
               color=GRI, va="top")

    for sutun, ad, renk in SERILER:
        y = seri[sutun].to_numpy(dtype=float)
        eksen.plot(yil, y, color=renk, linewidth=2.2, marker="o",
                   markersize=4, zorder=3)
        eksen.text(yil[-1] + 0.12, y[-1], f"{ad}  %{ts(y[-1], 1)}",
                   color=renk, fontsize=9.5, va="center")

    eksen.set_xlim(2015.6, 2029.4)
    eksen.set_ylim(0, 48)
    eksen.set_xticks(range(2016, 2027))
    eksen.set_xticklabels([str(y) for y in range(2016, 2027)], fontsize=9)
    eksen.set_xlabel("Makalenin GÖNDERİLME yılı")
    eksen.set_ylabel("Bu kalıbı en az bir kez içeren öz (%)")
    eksen.set_title("Yedi yıl düz, dört yılda sıçrama")
    alt_not(fig, "TUMLEX ön bulgusu · 36 dergi · 21.752 makale · öz "
                 "düzeyi · 2026 yılı kesik (317 öz) · nötr kontrol "
                 "kurulmadı, nedensellik çıkarımı yapılamaz")
    fig.tight_layout()
    return kaydet(fig, hedef / "t01_tumlex_egim.svg")


def t02_ayrim(secki, hedef):
    secki = secki.sort_values("oran_kati")
    fig, eksen = plt.subplots(figsize=(9.4, 7.0))
    y = np.arange(len(secki))
    renk = [AMBER if t == "konu" else (LACIVERT if k >= 1 else GRI)
            for t, k in zip(secki["tur"], secki["oran_kati"])]
    eksen.barh(y, secki["oran_kati"], color=renk, height=0.66, alpha=0.9)
    eksen.axvline(1, color=GRI, linewidth=1.1)
    # Etiket her zaman çubuğun SAĞINA konur. Birden küçük çubuklarda
    # sola koymak etiketi çubuğun içine düşürüyor ve okunurluğu
    # bozuyordu.
    for i, (_, s) in enumerate(secki.iterrows()):
        eksen.text(s["oran_kati"] + 0.09, i, "×" + ts(s["oran_kati"], 2),
                   va="center", ha="left", fontsize=8.8, color="#3A3A3A")
    eksen.set_yticks(y)
    eksen.set_yticklabels(secki["sozcuk"], fontsize=9.5)
    eksen.set_xlim(0, max(secki["oran_kati"]) * 1.2)
    eksen.set_xlabel("Sonrası dönem oranının öncesine katı (1 = değişim yok)")
    eksen.grid(axis="x")
    eksen.tick_params(axis="y", length=0)

    isaret = [
        plt.Line2D([], [], marker="s", linestyle="", markersize=9,
                   color=LACIVERT, label="Üslup — yazım izi adayı"),
        plt.Line2D([], [], marker="s", linestyle="", markersize=9,
                   color=AMBER, label="Konu — alanın gündemi, yazım izi değil"),
        plt.Line2D([], [], marker="s", linestyle="", markersize=9,
                   color=GRI, label="Azalan — edilgen işlem kalıpları"),
    ]
    eksen.legend(handles=isaret, loc="lower right", fontsize=9)
    eksen.set_title("Konu kayması ile üslup kayması aynı şey değil")
    alt_not(fig, "TUMLEX ön bulgusu · öz düzeyi · 10.000 sözcükteki "
                 "oranın dönemler arası katı · tüm değerler |z| > 6")
    fig.tight_layout()
    return kaydet(fig, hedef / "t02_tumlex_ayrim.svg")


ADLAR = {
    "maktadir": "-maktadır", "bulgular": "bulgular",
    "gostermektedir": "göstermektedir", "ortaya_koy": "ortaya koy…",
    "kapsamli": "kapsamlı", "kritik": "kritik", "mistir": "-mıştır",
    "yapilmistir": "yapılmıştır", "yurutulmustur": "yürütülmüştür",
    "tohum": "tohum", "cimlenme": "çimlenme", "hasat": "hasat",
    "deneme": "deneme", "makine": "makine", "ogrenme": "öğrenme",
}


def t03_dergi_ici(dergi, hedef):
    """Havuzlanmış değişimle dergi içi değişimi yan yana koyar.

    Soru şu: ölçülen kayma dergilerin kendi içinde mi oldu, yoksa
    korpusun dergi karışımı mı değişti? İkisi aynı çıkıyorsa bileşim
    açıklaması düşer. Grafik, iki noktayı bir çizgiyle bağlıyor;
    çizgi kısaldıkça bileşimin payı azalıyor.
    """
    dergi = dergi.copy()
    dergi["mutlak"] = dergi["havuz_puan"].abs()
    dergi = dergi.sort_values(["tur", "mutlak"])
    fig, eksen = plt.subplots(figsize=(9.8, 6.4))
    y = np.arange(len(dergi))

    for i, (_, s) in enumerate(dergi.iterrows()):
        renk = LACIVERT if s["tur"] == "uslup" else AMBER
        eksen.plot([s["havuz_puan"], s["dergi_ici_puan"]], [i, i],
                   color=renk, linewidth=2.4, alpha=0.35, zorder=2,
                   solid_capstyle="round")
        eksen.scatter([s["havuz_puan"]], [i], s=58, color=renk,
                      zorder=3, label=None)
        eksen.scatter([s["dergi_ici_puan"]], [i], s=58, facecolors="white",
                      edgecolors=renk, linewidths=1.9, zorder=4)
        uc = max(s["havuz_puan"], s["dergi_ici_puan"])
        eksen.text(uc + 0.55, i, "%" + ts(s["kalan_yuzde"], 0),
                   va="center", fontsize=8.6, color=GRI)

    eksen.axvline(0, color="#C7CBD1", linewidth=1.1)
    eksen.set_yticks(y)
    eksen.set_yticklabels([ADLAR.get(g, g) for g in dergi["gosterge"]],
                          fontsize=9.5)
    eksen.set_xlim(-7, 24)
    eksen.set_xlabel("Öncesi ile sonrası arasındaki fark (yüzde puan)")
    eksen.grid(axis="x")
    eksen.tick_params(axis="y", length=0)

    isaret = [
        plt.Line2D([], [], marker="o", linestyle="", markersize=8,
                   color=GRI, label="Havuzlanmış — bütün korpus"),
        plt.Line2D([], [], marker="o", linestyle="", markersize=8,
                   markerfacecolor="white", markeredgecolor=GRI,
                   markeredgewidth=1.8, color="none",
                   label="Dergi içi — her dergi kendi içinde"),
        plt.Line2D([], [], marker="s", linestyle="", markersize=9,
                   color=LACIVERT, label="Üslup göstergesi"),
        plt.Line2D([], [], marker="s", linestyle="", markersize=9,
                   color=AMBER, label="Konu göstergesi"),
    ]
    eksen.legend(handles=isaret, loc="lower right", fontsize=8.8)
    eksen.set_title("Kayma dergilerin kendi içinde mi oldu")
    alt_not(fig, "Her iki dönemde en az 25 özü olan 31 dergi · n ile "
                 "ağırlıklı ortalama · sağdaki yüzde, havuzlanmış "
                 "değişimin dergi içinde kalan payı")
    fig.tight_layout()
    return kaydet(fig, hedef / "t03_tumlex_dergi_ici.svg")


def main(veri_klasoru, sekil_klasoru):
    stil_kur()
    veri = pathlib.Path(veri_klasoru)
    hedef = pathlib.Path(sekil_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    seri = pd.read_csv(veri / "tumlex_yillik_seri.csv")
    secki = pd.read_csv(veri / "tumlex_sozcuk_secki.csv",
                        encoding="utf-8-sig")
    dergi = pd.read_csv(veri / "tumlex_dergi_ici.csv")
    for ad, boyut in [("t01_tumlex_egim.svg", t01_egim(seri, hedef)),
                      ("t02_tumlex_ayrim.svg", t02_ayrim(secki, hedef)),
                      ("t03_tumlex_dergi_ici.svg",
                       t03_dergi_ici(dergi, hedef))]:
        print(f"  {ad:26s} {boyut / 1024:7.1f} KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
