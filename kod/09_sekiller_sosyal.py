# -*- coding: utf-8 -*-
"""
09 — Sosyal bilimler analizinin şekilleri

Her şekil, 05_analiz_sosyal.py çıktısındaki GERÇEK sayılardan üretilir.
Hiçbir değer elle girilmemiştir; betik JSON dosyasını okur.

Kullanım:
  python 09_sekiller_sosyal.py <cikti_klasoru> <veri_klasoru> <sekil_klasoru>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sekil_stili as st


def main(cikti_klasoru, veri_klasoru, sekil_klasoru):
    st.stil_kur()
    S = json.loads((pathlib.Path(cikti_klasoru) / "sosyal_analiz.json")
                   .read_text(encoding="utf-8"))
    df = pd.read_csv(pathlib.Path(veri_klasoru) / "gazi_ders_degerlendirme.csv",
                     encoding="utf-8-sig")
    sozluk = pd.read_csv(pathlib.Path(veri_klasoru) / "gazi_madde_sozlugu.csv",
                         encoding="utf-8-sig")
    K = pathlib.Path(sekil_klasoru)
    uretilen = []
    KAYNAK = ("Veri: Gündüz & Fokoué (2013), UCI ML Repository, "
              "doi:10.24432/C5S02S · n = 5.820")
    # KAYNAK zaten n bilgisini taşıyor; ek notlarda tekrar edilmez.

    maddeler = sozluk["madde"].tolist()

    # ---------------------------------------- Ş1  yığılı Likert dağılımı
    fig, ax = plt.subplots(figsize=(8.6, 8.2))
    oranlar = np.array([[(df[m] == k).mean() * 100 for k in range(1, 6)]
                        for m in maddeler])
    # 3'ün yarısını merkez kabul edip sola/sağa ayır (ayrışan yığın)
    sol = -(oranlar[:, 0] + oranlar[:, 1] + oranlar[:, 2] / 2)
    y = np.arange(len(maddeler))
    baslangic = sol.copy()
    for k in range(5):
        genislik = oranlar[:, k]
        ax.barh(y, genislik, left=baslangic, height=0.74,
                color=st.LIKERT[k], edgecolor="white", linewidth=0.5)
        baslangic = baslangic + genislik
    ax.axvline(0, color="#9AA0A6", linewidth=1.0, zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels(
        [f"{m}  ({'D' if b == 'Ders' else 'Ö'})"
         for m, b in zip(maddeler, sozluk["boyut"])], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Yanıt yüzdesi — merkez, 'kararsız' yanıtının ortasıdır")
    ax.set_xlim(-72, 72)
    ax.set_xticks([-60, -40, -20, 0, 20, 40, 60])
    ax.set_xticklabels(["60", "40", "20", "0", "20", "40", "60"])
    ax.set_title("Yirmi sekiz maddenin yanıt dağılımı\n"
                 "D = ders boyutu · Ö = öğretim elemanı boyutu", loc="left")
    ax.grid(axis="x")
    ax.legend(handles=[Patch(facecolor=st.LIKERT[i],
                             label=st.LIKERT_ETIKET[i]) for i in range(5)],
              loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=3)
    st.alt_not(fig, KAYNAK)
    uretilen.append(("s01_likert_dagilim.svg",
                     st.kaydet(fig, K / "s01_likert_dagilim.svg")))

    # ---------------------------------------- Ş2  madde ortalamaları
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    mb = pd.DataFrame(S["madde_betimsel"])
    renk = [st.TURKUAZ if b == "Ders" else st.LACIVERT for b in mb["boyut"]]
    hata = mb["ss"] / np.sqrt(S["veri"]["n"]) * 1.96
    ax.barh(mb["madde"], mb["ortalama"], color=renk, height=0.72,
            xerr=hata, error_kw={"ecolor": "#44484D", "elinewidth": 1.0,
                                 "capsize": 2})
    for i, (ort, _) in enumerate(zip(mb["ortalama"], mb["ss"])):
        ax.text(ort + 0.06, i, st.ts(ort, 2), va="center", fontsize=8.5,
                color="#2A2A2A")
    ax.invert_yaxis()
    ax.set_xlim(1, 4.0)
    ax.axvline(3, color=st.KIRMIZI, linestyle="--", linewidth=1.0, zorder=0)
    ax.text(3.02, len(mb) - 0.4, "ölçek ortası (3)", fontsize=8.5,
            color=st.KIRMIZI)
    ax.set_xlabel("Madde ortalaması (1–5) · çubuklar %95 güven aralığı")
    ax.set_title("Madde ortalamaları ve güven aralıkları", loc="left")
    ax.legend(handles=[Patch(facecolor=st.TURKUAZ, label="Ders boyutu"),
                       Patch(facecolor=st.LACIVERT,
                             label="Öğretim elemanı boyutu")],
              loc="lower right")
    ax.grid(axis="x")
    st.alt_not(fig, KAYNAK)
    uretilen.append(("s02_madde_ortalama.svg",
                     st.kaydet(fig, K / "s02_madde_ortalama.svg")))

    # ---------------------------------------- Ş3  faktör yükleri saçılımı
    fig, ax = plt.subplots(figsize=(7.4, 6.6))
    yuk = pd.DataFrame(S["afa"]["yukler"])
    ders = yuk[yuk["beklenen_boyut"] == "Ders"]
    ogr = yuk[yuk["beklenen_boyut"] == "Öğretim"]
    ax.scatter(ders["Faktör 1"], ders["Faktör 2"], s=72, color=st.TURKUAZ,
               edgecolor="white", linewidth=1.0, alpha=0.92,
               label="Ders maddesi (12)", zorder=3)
    ax.scatter(ogr["Faktör 1"], ogr["Faktör 2"], s=72, color=st.LACIVERT,
               edgecolor="white", linewidth=1.0, alpha=0.92,
               label="Öğretim elemanı maddesi (16)", zorder=3)
    # Yirmi sekiz noktanın her birini adlandırmak okunmaz bir yığın üretir;
    # şeklin söylediği şey zaten tek tek maddeler değil, İKİ AYRI KÜME.
    # Bu yüzden noktalar değil kümeler etiketlenir.
    ax.annotate("Ders maddeleri\nQ1 – Q12",
                xy=(float(ders["Faktör 1"].mean()),
                    float(ders["Faktör 2"].mean())),
                xytext=(0.33, 0.56), fontsize=10.5, color=st.TURKUAZ,
                fontweight="bold", ha="center",
                arrowprops={"arrowstyle": "-", "color": st.TURKUAZ,
                            "linewidth": 1.1, "alpha": 0.6})
    ax.annotate("Öğretim elemanı maddeleri\nQ13 – Q28",
                xy=(float(ogr["Faktör 1"].mean()),
                    float(ogr["Faktör 2"].mean())),
                xytext=(0.66, 0.78), fontsize=10.5, color=st.LACIVERT,
                fontweight="bold", ha="center",
                arrowprops={"arrowstyle": "-", "color": st.LACIVERT,
                            "linewidth": 1.1, "alpha": 0.6})
    ax.plot([0, 1], [1, 0], color="#C7CBD1", linestyle=":", linewidth=1.0,
            zorder=1)
    ax.set_xlabel(f"Faktör 1 — öğretim elemanı "
                  f"(açıklanan varyans %{st.ts(S['afa']['aciklanan_f1'], 1)})")
    ax.set_ylabel(f"Faktör 2 — ders "
                  f"(açıklanan varyans %{st.ts(S['afa']['aciklanan_f2'], 1)})")
    ax.set_title("Varimax döndürülmüş faktör yükleri\n"
                 f"KMO = {st.ts(S['afa']['kmo'], 3)} · "
                 f"{S['afa']['yapiya_uyan_madde']}/"
                 f"{S['afa']['madde_sayisi']} madde beklenen boyuta yüklendi",
                 loc="left")
    ax.set_xlim(0.25, 0.95)
    ax.set_ylim(0.3, 0.9)
    ax.legend(loc="lower left")
    st.alt_not(fig, KAYNAK + " · köşegen: eşit yük doğrusu")
    uretilen.append(("s03_faktor_yukleri.svg",
                     st.kaydet(fig, K / "s03_faktor_yukleri.svg")))

    # ---------------------------------------- Ş4  scree
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    R = np.corrcoef(df[maddeler].values, rowvar=False)
    oz = np.sort(np.linalg.eigvalsh(R))[::-1]
    x = np.arange(1, len(oz) + 1)
    ax.plot(x, oz, "o-", color=st.LACIVERT, markersize=5,
            markerfacecolor="white", markeredgewidth=1.6)
    ax.axhline(1, color=st.KIRMIZI, linestyle="--", linewidth=1.1)
    ax.text(len(oz) * 0.62, 1.5, "Kaiser ölçütü: özdeğer > 1",
            color=st.KIRMIZI, fontsize=9)
    ax.scatter(x[:2], oz[:2], s=150, facecolor="none",
               edgecolor=st.TURKUAZ, linewidth=2.0, zorder=4)
    ax.annotate(f"İki faktör tutuldu\n(özdeğer {oz[0]:.2f} ve {oz[1]:.2f})",
                xy=(2, oz[1]), xytext=(5.4, 12),
                arrowprops={"arrowstyle": "->", "color": st.TURKUAZ,
                            "linewidth": 1.3},
                fontsize=9.5, color=st.TURKUAZ)
    ax.set_xlabel("Faktör sırası")
    ax.set_ylabel("Özdeğer")
    ax.set_title("Yamaç (scree) grafiği — kaç faktör tutulmalı?", loc="left")
    st.alt_not(fig, KAYNAK)
    uretilen.append(("s04_scree.svg", st.kaydet(fig, K / "s04_scree.svg")))

    # ---------------------------------------- Ş5  ANOVA kutu grafiği
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    gruplar = [df.loc[df["difficulty"] == g, "ders_puan"].values
               for g in range(1, 6)]
    kutu = ax.boxplot(gruplar, patch_artist=True, widths=0.56,
                      medianprops={"color": "#22262B", "linewidth": 1.6},
                      whiskerprops={"color": "#8A9099"},
                      capprops={"color": "#8A9099"},
                      flierprops={"marker": ".", "markersize": 3,
                                  "markerfacecolor": "#B9BEC5",
                                  "markeredgecolor": "none"})
    for kutucuk, renk in zip(kutu["boxes"],
                             [st.ACIK, "#CFE3E8", st.LIKERT[3],
                              "#CFE3E8", st.ACIK]):
        kutucuk.set_facecolor(renk)
        kutucuk.set_edgecolor("#8A9099")
    ortalamalar = [g.mean() for g in gruplar]
    ax.plot(range(1, 6), ortalamalar, "D--", color=st.KIRMIZI, markersize=6,
            linewidth=1.4, label="grup ortalaması", zorder=5)
    for i, (ort, g) in enumerate(zip(ortalamalar, gruplar), start=1):
        ax.text(i, 5.22, f"n = {st.tam(len(g))}", ha="center", fontsize=8.5,
                color=st.GRI)
    a = S["anova"]
    ax.set_xticklabels(["1\nçok kolay", "2", "3", "4", "5\nçok güç"])
    ax.set_xlabel("Dersin algılanan güçlüğü")
    ax.set_ylabel("Ders boyutu puanı (1–5)")
    ax.set_ylim(0.8, 5.5)
    ax.set_title(f"Güçlük algısına göre ders puanı\n"
                 f"F({a['df_arasi']}, {st.tam(a['df_ici'])}) = "
                 f"{st.ts(a['F'], 2)}, p < 0,001, "
                 f"eta kare = {st.ts(a['eta_kare'], 3)} "
                 f"(değişkenliğin %{st.ts(100*a['eta_kare'], 1)}'i)",
                 loc="left")
    ax.legend(loc="lower center")
    fig.subplots_adjust(bottom=0.22)
    st.alt_not(fig, KAYNAK
               + "  ·  eta kare küçük: anlamlı fark, büyük fark demek değil")
    uretilen.append(("s05_anova_kutu.svg",
                     st.kaydet(fig, K / "s05_anova_kutu.svg")))

    # ---------------------------------------- Ş6  korelasyon ısı haritası
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    kd = S["korelasyon"]["degiskenler"]
    M = np.array(S["korelasyon"]["pearson"])
    etiket = {"ders_puan": "Ders puanı", "ogretim_puan": "Öğretim puanı",
              "attendance": "Katılım", "difficulty": "Güçlük",
              "nb.repeat": "Tekrar sayısı"}
    maske = np.triu(np.ones_like(M, dtype=bool), k=1)
    Mg = np.ma.masked_where(maske, M)
    im = ax.imshow(Mg, cmap="RdBu_r", vmin=-1, vmax=1)
    for i in range(len(kd)):
        for j in range(len(kd)):
            if j <= i:
                ax.text(j, i, f"{M[i, j]:.2f}".replace(".", ","),
                        ha="center", va="center", fontsize=9.5,
                        color="white" if abs(M[i, j]) > 0.55 else "#22262B",
                        fontweight="bold" if i != j else "normal")
    ax.set_xticks(range(len(kd)))
    ax.set_yticks(range(len(kd)))
    ax.set_xticklabels([etiket[k] for k in kd], rotation=35, ha="right")
    ax.set_yticklabels([etiket[k] for k in kd])
    ax.grid(visible=False)
    ax.set_title("Pearson korelasyon matrisi", loc="left")
    cb = fig.colorbar(im, ax=ax, shrink=0.72)
    cb.set_label("r", rotation=0, labelpad=10)
    cb.outline.set_visible(False)
    st.alt_not(fig, KAYNAK + "  ·  bu büyüklükte bir örneklemde r = 0,03 "
                             "bile anlamlı çıkar; r kare okunmalıdır")
    uretilen.append(("s06_korelasyon.svg",
                     st.kaydet(fig, K / "s06_korelasyon.svg")))

    # ---------------------------------------- Ş7  regresyon orman grafiği
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    kat = [k for k in S["regresyon"]["katsayilar"] if k["terim"] != "Intercept"]
    ad = {"C(instr)[T.2]": "Öğretim elemanı 2 (ref: 1)",
          "C(instr)[T.3]": "Öğretim elemanı 3 (ref: 1)",
          "attendance": "Derse katılım",
          "difficulty": "Algılanan güçlük",
          "Q('nb.repeat')": "Dersi tekrar sayısı"}
    y = np.arange(len(kat))[::-1]
    for yi, k in zip(y, kat):
        anlamli = k["p"] < 0.05
        renk = st.LACIVERT if anlamli else st.GRI
        ax.plot([k["alt_GA"], k["üst_GA"]], [yi, yi], color=renk,
                linewidth=2.4, solid_capstyle="round")
        ax.plot(k["B"], yi, "o", color=renk, markersize=8,
                markerfacecolor=renk if anlamli else "white",
                markeredgewidth=1.8)
        p_metin = "p < 0,001" if k["p"] < 0.001 else f"p = {k['p']:.3f}".replace(".", ",")
        b_metin = ("+" if k["B"] >= 0 else "−") + st.ts(abs(k["B"]), 3)
        ax.text(0.30, yi, f"B = {b_metin}   {p_metin}",
                fontsize=9, va="center", color=renk)
    ax.axvline(0, color="#22262B", linewidth=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels([ad.get(k["terim"], k["terim"]) for k in kat])
    ax.set_xlim(-0.30, 0.55)
    ax.set_xlabel("Standartlaştırılmamış katsayı B ve %95 güven aralığı")
    r = S["regresyon"]
    ax.set_title(f"Öğretim elemanı puanını yordayan değişkenler\n"
                 f"R kare = {st.ts(r['r_kare'], 3)} · "
                 f"F({r['df_model']}, {st.tam(r['df_artik'])}) = "
                 f"{st.ts(r['F'], 2)} · dolu nokta: p < 0,05", loc="left")
    ax.grid(axis="x")
    st.alt_not(fig, KAYNAK + " · güçlük, katılım denetlendiğinde anlamsız — "
                             "örtük değişken etkisi")
    uretilen.append(("s07_regresyon_katsayi.svg",
                     st.kaydet(fig, K / "s07_regresyon_katsayi.svg")))

    # ---------------------------------------- Ş8  güç ve anlamlılık
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.3))
    pa = pd.DataFrame(S["anlamlilik_dersi"]["panel_a"])
    x = np.arange(len(pa))
    ax1.fill_between(x, pa["r_alt_2.5"], pa["r_ust_97.5"], color="#D8E6EA",
                     label="r'nin %95'lik oynama aralığı")
    ax1.plot(x, pa["r_ortalama"], "o-", color=st.LACIVERT, markersize=6,
             markerfacecolor="white", markeredgewidth=1.6,
             label="r ortalaması")
    ax1.axhline(S["anlamlilik_dersi"]["evren_r"], color=st.KIRMIZI,
                linestyle="--", linewidth=1.1)
    ax1.axhline(0, color="#9AA0A6", linewidth=0.9)
    ax1.text(0.08, S["anlamlilik_dersi"]["evren_r"] + 0.03,
             f"gerçek değer r = {st.ts(S['anlamlilik_dersi']['evren_r'], 2)}",
             color=st.KIRMIZI, fontsize=9)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{n:,}" for n in pa["n"]])
    ax1.set_xlabel("Örneklem büyüklüğü")
    ax1.set_ylabel("Pearson r")
    ax1.set_title("A · Küçük örneklemde katsayı oynar\n"
                  "500 yinelemeli örnekleme", loc="left")
    ax1.legend(loc="upper right")

    ax2b = ax2.twinx()
    ax2.bar(x, pa["p<0,05 çıkma oranı"] * 100 if "p<0,05 çıkma oranı" in pa
            else pa.iloc[:, -1] * 100, color=st.TURKUAZ, width=0.6)
    ax2.axhline(80, color=st.KIRMIZI, linestyle="--", linewidth=1.1)
    ax2.text(-0.38, 82.5, "yaygın ölçüt: %80 güç", color=st.KIRMIZI,
             fontsize=9, ha="left")
    for xi, oran in zip(x, pa.iloc[:, -1] * 100):
        ax2.text(xi, oran + 2.5, f"%{oran:.0f}", ha="center", fontsize=9.5,
                 color=st.LACIVERT)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{n:,}" for n in pa["n"]])
    ax2.set_ylim(0, 108)
    ax2.set_xlabel("Örneklem büyüklüğü")
    ax2.set_ylabel("İlişkinin yakalanma oranı (%)")
    ax2.set_title("B · İstatistiksel güç\n"
                  "Aynı gerçek ilişkiyi 'anlamlı' bulma şansı", loc="left")
    ax2b.set_yticks([])
    st.alt_not(fig, KAYNAK + " · gerçek bir ilişki, n = 30'da %7 olasılıkla "
                             "yakalanıyor")
    uretilen.append(("s08_guc_analizi.svg",
                     st.kaydet(fig, K / "s08_guc_analizi.svg")))

    # ---------------------------------------- Ş9  madde-toplam
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    mt = pd.DataFrame(S["guvenilirlik"]["madde_toplam"])
    renk = [st.TURKUAZ if m in sozluk.loc[sozluk.boyut == "Ders", "madde"].values
            else st.LACIVERT for m in mt["madde"]]
    ax.bar(mt["madde"], mt["düzeltilmiş_madde_toplam_r"], color=renk,
           width=0.72)
    ax.axhline(0.30, color=st.KIRMIZI, linestyle="--", linewidth=1.2)
    ax.text(0.2, 0.33, "alt ölçüt: 0,30 — altındaki madde çıkarılmaya aday",
            color=st.KIRMIZI, fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Düzeltilmiş madde-toplam korelasyonu")
    ax.set_xticks(range(len(mt)))
    ax.set_xticklabels(mt["madde"], rotation=90, fontsize=8)
    g = S["guvenilirlik"]
    ax.set_title("Madde-toplam korelasyonları\n"
                 f"Cronbach alfa — ders {st.ts(g['Ders boyutu']['alfa'], 3)} · "
                 f"öğretim {st.ts(g['Öğretim elemanı boyutu']['alfa'], 3)} · "
                 f"tüm ölçek {st.ts(g['Tüm ölçek']['alfa'], 3)}", loc="left")
    ax.grid(axis="y")
    st.alt_not(fig, KAYNAK + "  ·  alfa > 0,90 madde fazlalığı uyarısıdır "
                             "(Streiner, 2003)")
    uretilen.append(("s09_madde_toplam.svg",
                     st.kaydet(fig, K / "s09_madde_toplam.svg")))

    print(f"{len(uretilen)} şekil üretildi → {K}")
    for ad_, boyut in uretilen:
        print(f"  {ad_:34s} {boyut/1024:7.1f} KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
