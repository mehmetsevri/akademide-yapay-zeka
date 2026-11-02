# -*- coding: utf-8 -*-
"""
28 — Kentsel dönüşüm araştırmasının şekilleri

Nitel araştırmada şekil, sayıyı değil İLİŞKİYİ gösterir. Altı şekil:

  m01  tematik ağ haritası (temalar ve kodlar)
  m02  tema sıklığı ve katılımcı yayılımı
  m03  tema × katılımcı grubu ısı haritası
  m04  dönüşüm matrisi: öncesi · inşaat · sonrası
  m05  doygunluk eğrisi
  m06  kod eş-görünüm ağı

Kullanım:
  python 28_sekiller_kentsel.py <çıktı_klasörü> <şekil_klasörü>
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

TEMA_RENK = {
    "Mekânsal yabancılaşma ve güvensizlik": LACIVERT,
    "Komşuluk ağlarının çözülmesi ve atomize yaşam": TURKUAZ,
    "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı": MOR,
    "Ekonomik baskı ve yerinden edilme": AMBER,
    "Kuşaklar arası ayrışma ve konforun kazananları": YESIL,
}
TEMA_KISA = {
    "Mekânsal yabancılaşma ve güvensizlik": "Mekânsal\nyabancılaşma",
    "Komşuluk ağlarının çözülmesi ve atomize yaşam": "Komşuluk\nağlarının\nçözülmesi",
    "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı": "Hafıza ve\naidiyet kaybı",
    "Ekonomik baskı ve yerinden edilme": "Ekonomik baskı\nve yerinden\nedilme",
    "Kuşaklar arası ayrışma ve konforun kazananları": "Ayrışma ve\nkonforun\nkazananları",
}
GRUP_ADI = {"A": "Yerinde\nkalan", "B": "Mahalleden\nayrılan",
            "C": "Esnaf", "D": "Yeni\nsakin", "E": "Kilit\naktör"}


def m01_ag(kod_kitabi, siklik, hedef):
    """Tematik ağ haritası: ortada temalar, çevresinde kodlar."""
    fig, eksen = plt.subplots(figsize=(11.4, 8.4))
    eksen.set_xlim(-1.32, 1.32)
    eksen.set_ylim(-1.30, 1.22)
    eksen.axis("off")

    temalar = list(TEMA_RENK)
    aci_tema = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi, len(temalar),
                           endpoint=False)
    siklik_kod = dict(zip(siklik["kod"], siklik["n"]))

    for tema, aci in zip(temalar, aci_tema):
        tx, ty = 0.52 * np.cos(aci), 0.52 * np.sin(aci)
        renk = TEMA_RENK[tema]
        kodlar = kod_kitabi[kod_kitabi["tema"] == tema]["kod"].tolist()
        yay = np.pi * 2 / len(temalar) * 0.84
        alt_aci = np.linspace(aci - yay / 2, aci + yay / 2, len(kodlar))
        for kod, ka in zip(kodlar, alt_aci):
            kx, ky = 1.08 * np.cos(ka), 1.02 * np.sin(ka)
            n = siklik_kod.get(kod, 0)
            eksen.plot([tx, kx], [ty, ky], color=renk, alpha=0.32,
                       linewidth=0.7 + n / 14)
            eksen.scatter([kx], [ky], s=42 + n * 5.6, color=renk,
                          alpha=0.88, zorder=3, edgecolors="white",
                          linewidths=1.1)
            # Tepeye ya da dibe düşen düğümlerde yatay kaydırma işe
            # yaramaz; etiket düğümün üstüne biner. O düğümlerde etiket
            # dikey olarak uzaklaştırılıyor.
            if abs(kx) < 0.18:
                eksen.text(kx, ky + (0.085 if ky > 0 else -0.085),
                           f"{kod} ({n})", ha="center",
                           va="bottom" if ky > 0 else "top",
                           fontsize=7.6, color="#2A2A2A")
            else:
                hiza = "left" if kx > 0 else "right"
                eksen.text(kx + (0.055 if kx > 0 else -0.055), ky,
                           f"{kod}\n({n})", ha=hiza, va="center",
                           fontsize=7.6, color="#2A2A2A", linespacing=1.15)
        # Tema adı düğümün İÇİNE sığmıyor — uzun Türkçe adlar daireyi
        # taşırıyordu. Ad dairenin altına, koyu renkle yazılıyor.
        eksen.scatter([tx], [ty], s=900, color=renk, alpha=0.95, zorder=4,
                      edgecolors="white", linewidths=2)
        eksen.text(tx, ty - 0.115, TEMA_KISA[tema], ha="center", va="top",
                   fontsize=8.6, color=renk, fontweight="bold",
                   zorder=5, linespacing=1.2,
                   bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                             edgecolor="none", alpha=0.86))

    eksen.set_title("Tematik ağ haritası — beş tema, yirmi beş kod",
                    loc="left", pad=6)
    alt_not(fig, "Düğüm büyüklüğü ve çizgi kalınlığı kodun korpustaki "
                 "sıklığıyla orantılı · parantez içindeki sayı kodlanan "
                 "parça sayısı")
    fig.tight_layout()
    return kaydet(fig, hedef / "m01_tematik_ag.svg")


def m02_tema_siklik(tema_df, hedef):
    alt = tema_df.sort_values("parca")
    fig, eksen = plt.subplots(figsize=(9.6, 4.4))
    y = np.arange(len(alt))
    renkler = [TEMA_RENK[t] for t in alt["tema"]]
    eksen.barh(y, alt["parca"], color=renkler, height=0.56, alpha=0.9)
    for i, (_, s) in enumerate(alt.iterrows()):
        eksen.text(s["parca"] + 3, i,
                   f"{int(s['parca'])} parça · {int(s['katilimci'])}/38 "
                   f"katılımcı (%{ts(s['katilimci_%'], 0)})",
                   va="center", fontsize=9, color="#3A3A3A")
    eksen.set_yticks(y)
    eksen.set_yticklabels([t.replace(" ve ", "\nve ") for t in alt["tema"]],
                          fontsize=9)
    eksen.set_xlim(0, alt["parca"].max() * 1.72)
    eksen.set_xlabel("Kodlanan parça sayısı")
    eksen.grid(axis="x")
    eksen.tick_params(axis="y", length=0)
    eksen.set_title("Tema ağırlığı ve katılımcı yayılımı")
    alt_not(fig, "Parça sayısı korpustaki ağırlığı, katılımcı sayısı "
                 "deneyimin ne kadar ortak olduğunu gösterir")
    fig.tight_layout()
    return kaydet(fig, hedef / "m02_tema_siklik.svg")


def m03_grup(grup_df, hedef):
    m = grup_df.set_index(grup_df.columns[0])
    sutunlar = [s for s in ["A", "B", "C", "D", "E"] if s in m.columns]
    m = m[sutunlar]
    sira = [t for t in TEMA_RENK if t in m.index]
    m = m.loc[sira]
    fig, eksen = plt.subplots(figsize=(8.2, 4.8))
    gorsel = eksen.imshow(m.to_numpy(dtype=float), cmap="BuPu", vmin=0,
                          vmax=float(m.to_numpy(dtype=float).max()))
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            deger = float(m.iat[i, j])
            eksen.text(j, i, f"%{ts(deger, 1)}", ha="center", va="center",
                       fontsize=9.5,
                       color="white" if deger > m.to_numpy(
                           dtype=float).max() * 0.6 else "#1A1A1A")
    eksen.set_xticks(range(len(sutunlar)),
                     [GRUP_ADI[s] for s in sutunlar], fontsize=9)
    eksen.set_yticks(range(len(sira)),
                     [TEMA_KISA[t].replace("\n", " ") for t in sira],
                     fontsize=9)
    eksen.grid(False)
    eksen.set_title("Hangi grup hangi temayı dile getiriyor", pad=12)
    fig.colorbar(gorsel, ax=eksen, shrink=0.8,
                 label="Grubun parçalarındaki pay (%)")
    alt_not(fig, "Sütunlar %100'e tamamlanır: her grubun kendi içindeki "
                 "dağılım")
    fig.tight_layout()
    return kaydet(fig, hedef / "m03_tema_grup.svg")


def m04_matris(matris_df, hedef):
    m = matris_df.set_index(matris_df.columns[0])
    evreler = [e for e in ["öncesi", "inşaat", "sonrası"] if e in m.columns]
    sira = [t for t in TEMA_RENK if t in m.index]
    fig, eksen = plt.subplots(figsize=(9.4, 4.6))
    x = np.arange(len(evreler))
    alt_toplam = np.zeros(len(evreler))
    for tema in sira:
        degerler = m.loc[tema, evreler].to_numpy(dtype=float)
        eksen.bar(x, degerler, bottom=alt_toplam, color=TEMA_RENK[tema],
                  width=0.56, label=tema, alpha=0.92)
        for i, d in enumerate(degerler):
            if d >= 8:
                eksen.text(x[i], alt_toplam[i] + d / 2, f"{int(d)}",
                           ha="center", va="center", fontsize=9,
                           color="white")
        alt_toplam += degerler
    eksen.set_xticks(x, ["Dönüşüm öncesi", "İnşaat süreci",
                         "Dönüşüm sonrası"], fontsize=10.5)
    eksen.set_ylabel("Kodlanan parça sayısı")
    eksen.grid(axis="y")
    eksen.legend(loc="upper left", fontsize=8.6, ncol=1,
                 bbox_to_anchor=(1.01, 1.0))
    eksen.set_title("Dönüşüm matrisi: temalar üç evrede")
    alt_not(fig, "Her parça, katılımcının hangi evreyi anlattığına göre "
                 "sınıflandırıldı")
    fig.tight_layout()
    return kaydet(fig, hedef / "m04_donusum_matrisi.svg")


def m05_doygunluk(egri, hedef):
    fig, eksen = plt.subplots(figsize=(9.2, 4.4))
    eksen.bar(egri["gorusme"], egri["yeni_kod"], color=ACIK, width=0.68,
              label="O görüşmede ilk kez çıkan kod")
    ikinci = eksen.twinx()
    ikinci.plot(egri["gorusme"], egri["kumulatif_kod"], color=LACIVERT,
                linewidth=2.4, marker="o", markersize=3.6,
                label="Kümülatif kod sayısı")
    ikinci.set_ylabel("Kümülatif kod sayısı")
    ikinci.set_ylim(0, egri["kumulatif_kod"].max() * 1.14)
    ikinci.grid(False)

    son = int(egri[egri["yeni_kod"] > 0]["gorusme"].max())
    eksen.axvline(son + 0.5, color=KIRMIZI, linestyle="--", linewidth=1.3)
    eksen.text(son + 0.9, eksen.get_ylim()[1] * 0.82,
               f"{son}. görüşmeden sonra\nyeni kod çıkmadı",
               fontsize=9.5, color=KIRMIZI)
    eksen.set_xlabel("Görüşme sırası (tarih sırasına göre)")
    eksen.set_ylabel("Yeni kod sayısı")
    eksen.grid(axis="y")
    eksen.set_title("Doygunluk eğrisi")
    cizgiler = eksen.get_legend_handles_labels()
    cizgiler2 = ikinci.get_legend_handles_labels()
    eksen.legend(cizgiler[0] + cizgiler2[0], cizgiler[1] + cizgiler2[1],
                 loc="center right", fontsize=9)
    alt_not(fig, "Örneklem büyüklüğünün gerekçesi: doygunluğa ulaşıldıktan "
                 "sonra 21 görüşme daha yapıldı")
    fig.tight_layout()
    return kaydet(fig, hedef / "m05_doygunluk.svg")


def m06_es_gorunum(es, kod_kitabi, hedef):
    kodlar = kod_kitabi["kod"].tolist()
    tema_of = dict(zip(kod_kitabi["kod"], kod_kitabi["tema"]))
    n = len(kodlar)
    konum = {}
    for i, kod in enumerate(kodlar):
        aci = np.pi / 2 - 2 * np.pi * i / n
        konum[kod] = (np.cos(aci), np.sin(aci))

    fig, eksen = plt.subplots(figsize=(8.8, 8.8))
    eksen.set_xlim(-1.42, 1.42)
    eksen.set_ylim(-1.34, 1.34)
    eksen.axis("off")

    en_cok = es["birlikte_gecen_katilimci"].max()
    for _, s in es[es["birlikte_gecen_katilimci"] >= 8].iterrows():
        x1, y1 = konum[s["kod_1"]]
        x2, y2 = konum[s["kod_2"]]
        guc = s["birlikte_gecen_katilimci"] / en_cok
        renk = (KIRMIZI if s["tema_asiyor"] else GRI)
        eksen.plot([x1, x2], [y1, y2], color=renk,
                   alpha=0.14 + 0.52 * guc, linewidth=0.5 + 2.8 * guc,
                   zorder=1)

    for kod in kodlar:
        x, y = konum[kod]
        eksen.scatter([x], [y], s=160, color=TEMA_RENK[tema_of[kod]],
                      zorder=3, edgecolors="white", linewidths=1.4)
        aci = np.degrees(np.arctan2(y, x))
        hiza = "left" if x > 0 else "right"
        eksen.text(x * 1.1, y * 1.1, kod, ha=hiza, va="center",
                   fontsize=8.4, color="#2A2A2A",
                   rotation=aci if x > 0 else aci + 180,
                   rotation_mode="anchor")

    isaretler = [plt.Line2D([], [], marker="o", linestyle="", markersize=8,
                            color=renk, label=tema.split(" ve ")[0])
                 for tema, renk in TEMA_RENK.items()]
    isaretler.append(plt.Line2D([], [], color=KIRMIZI, linewidth=2,
                                label="Tema sınırını aşan bağ"))
    eksen.legend(handles=isaretler, loc="upper left",
                 bbox_to_anchor=(-0.08, 1.04), fontsize=8.4)
    eksen.set_title("Kod eş-görünüm ağı", loc="left", pad=4)
    alt_not(fig, "Bağ, iki kodun aynı katılımcının anlatısında birlikte "
                 "geçmesi demektir · en az 8 katılımcıda görülen bağlar "
                 "çizildi")
    fig.tight_layout()
    return kaydet(fig, hedef / "m06_es_gorunum.svg")


def main(cikti_klasoru, sekil_klasoru):
    stil_kur()
    cikti = pathlib.Path(cikti_klasoru)
    hedef = pathlib.Path(sekil_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)

    kod_kitabi = pd.read_csv(cikti / "kentsel_kod_kitabi.csv",
                             encoding="utf-8-sig")
    siklik = pd.read_csv(cikti / "kentsel_kod_sikliklari.csv",
                         encoding="utf-8-sig")
    tema_df = pd.read_csv(cikti / "kentsel_tema_sikliklari.csv",
                          encoding="utf-8-sig")
    grup_df = pd.read_csv(cikti / "kentsel_tema_grup.csv",
                          encoding="utf-8-sig")
    matris = pd.read_csv(cikti / "kentsel_donusum_matrisi.csv",
                         encoding="utf-8-sig")
    egri = pd.read_csv(cikti / "kentsel_doygunluk.csv",
                       encoding="utf-8-sig")
    es = pd.read_csv(cikti / "kentsel_es_gorunum.csv", encoding="utf-8-sig")

    isler = [
        ("m01_tematik_ag.svg", m01_ag(kod_kitabi, siklik, hedef)),
        ("m02_tema_siklik.svg", m02_tema_siklik(tema_df, hedef)),
        ("m03_tema_grup.svg", m03_grup(grup_df, hedef)),
        ("m04_donusum_matrisi.svg", m04_matris(matris, hedef)),
        ("m05_doygunluk.svg", m05_doygunluk(egri, hedef)),
        ("m06_es_gorunum.svg", m06_es_gorunum(es, kod_kitabi, hedef)),
    ]
    for ad, boyut in isler:
        print(f"  {ad:28s} {boyut / 1024:7.1f} KB")
    print(f"{len(isler)} şekil yazıldı → {hedef}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
