# -*- coding: utf-8 -*-
"""
10 — Web güvenliği ve nitel analizin şekilleri

Değerler 06_analiz_web_guvenligi.py ve 08_tematik_analiz.py çıktılarından
okunur; hiçbiri elle girilmemiştir.

Kullanım:
  python 10_sekiller_web_nitel.py <cikti> <veri_web_csv> <sekil_klasoru>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sekil_stili as st


def main(cikti_klasoru, web_csv, sekil_klasoru):
    st.stil_kur()
    C = pathlib.Path(cikti_klasoru)
    W = json.loads((C / "web_guvenligi_analiz.json").read_text(encoding="utf-8"))
    T = json.loads((C / "tematik_analiz.json").read_text(encoding="utf-8"))
    df = pd.read_csv(web_csv, encoding="utf-8-sig")
    K = pathlib.Path(sekil_klasoru)
    uretilen = []
    WKAYNAK = ("Veri: Prasad & Chandra (2024), PhiUSIIL, UCI ML Repository · "
               "altküme n = 5.000")
    NKAYNAK = ("Veri: sentetik açık uçlu yanıtlar (116 yanıt, 45 katılımcı) — "
               "yöntem göstermek için üretilmiştir")

    # ===================== W1  etki büyüklükleri =====================
    fig, ax = plt.subplots(figsize=(7.8, 5.2))
    kars = pd.DataFrame(W["betimsel_karsilastirma"])
    kars["mutlak"] = kars["cohen_d"].abs()
    ust = kars.nlargest(14, "mutlak").sort_values("mutlak")
    renk = [st.KIRMIZI if d > 0 else st.LACIVERT for d in ust["cohen_d"]]
    ax.barh(ust["özellik"], ust["cohen_d"], color=renk, height=0.7)
    for yon, etiket in [(0.8, "büyük etki"), (-0.8, "")]:
        ax.axvline(yon, color=st.GRI, linestyle=":", linewidth=1.0)
    ax.axvline(0, color="#22262B", linewidth=1.0)
    ax.text(0.86, 0.3, "d = 0,8\nbüyük etki sınırı", fontsize=8.5,
            color=st.GRI)
    for i, d in enumerate(ust["cohen_d"]):
        ax.text(d + (0.12 if d > 0 else -0.12), i, st.ts(abs(d), 2),
                va="center", ha="left" if d > 0 else "right", fontsize=8.5)
    ax.set_xlabel("Cohen d — kimlik avı eksi meşru (standartlaştırılmış fark)")
    ax.set_title("En ayırt edici on dört özellik\n"
                 "Kırmızı: kimlik avında yüksek · Lacivert: meşruda yüksek",
                 loc="left")
    ax.set_xlim(-4.2, 2.4)
    ax.grid(axis="x")
    st.alt_not(fig, WKAYNAK + "  ·  |d| > 3 olağandışıdır; "
                              "özelliğin etiketle aynı şey olduğunu düşündürür")
    uretilen.append(("w01_etki_buyukluk.svg",
                     st.kaydet(fig, K / "w01_etki_buyukluk.svg")))

    # ===================== W2  sızıntının teşhisi =====================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.2),
                                   gridspec_kw={"width_ratios": [1.0, 1.0]})
    fig.subplots_adjust(wspace=0.42)
    kav = df.loc[df["etiket"] == "kimlik_avi", "URLSimilarityIndex"]
    mes = df.loc[df["etiket"] == "mesru", "URLSimilarityIndex"]
    ax1.hist(kav, bins=40, color=st.KIRMIZI, alpha=0.85,
             label=f"Kimlik avı (n = {st.tam(len(kav))})")
    ax1.bar([100], [len(mes)], width=2.4, color=st.LACIVERT,
            label=f"Meşru (n = {st.tam(len(mes))})")
    ax1.annotate("Meşru sınıfın TAMAMI\ntam olarak 100,0\n"
                 "standart sapma = 0",
                 xy=(100, len(mes) * 0.55), xytext=(46, len(mes) * 0.72),
                 fontsize=10, color=st.LACIVERT, fontweight="bold",
                 arrowprops={"arrowstyle": "->", "color": st.LACIVERT,
                             "linewidth": 1.6})
    ax1.set_xlabel("URLSimilarityIndex")
    ax1.set_ylabel("Kayıt sayısı")
    ax1.set_title("A · Sızıntının görüntüsü", loc="left")
    ax1.legend(loc="upper left")

    # Panel B: meşru sınıfta sabit olan beş özelliğin ve sayfa içeriğinden
    # gelen özelliklerin tek eşikle verdiği doğruluk — hepsi 06 numaralı
    # betiğin taramasından okunur.
    tarama = pd.DataFrame(W["teshis"]["tarama"])
    ust = tarama.nlargest(8, "tek_eşik_doğruluk").sort_values(
        "tek_eşik_doğruluk")
    sabitler = set(W["teshis"]["mesru_sinifta_sabit"])
    renk = [st.KIRMIZI if o in sabitler else st.AMBER
            for o in ust["özellik"]]
    ax2.barh(ust["özellik"], ust["tek_eşik_doğruluk"] * 100, color=renk,
             height=0.66)
    for i, v in enumerate(ust["tek_eşik_doğruluk"] * 100):
        ax2.text(v + 0.6, i, f"%{st.ts(v, 1)}", va="center", fontsize=8.5)
    ax2.set_xlim(50, 108)
    ax2.set_xlabel("Tek bir eşikle alınan doğruluk (%)")
    ax2.set_title("B · Modelsiz tek 'if' satırı\n"
                  "Kırmızı: meşru sınıfta sabit olan özellikler", loc="left")
    ax2.grid(axis="x")
    ax2.tick_params(axis="y", labelsize=8.5)
    st.alt_not(fig, WKAYNAK + "  ·  beş özellik meşru sınıfın 2.859 "
                              "kaydının tamamında aynı değeri alıyor")
    uretilen.append(("w02_sizinti_teshis.svg",
                     st.kaydet(fig, K / "w02_sizinti_teshis.svg")))

    # ===================== W3  üç model karşılaştırması =====================
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    kiyas = pd.DataFrame(W["model_kiyas"])
    olcutler = ["doğruluk", "kesinlik", "duyarlılık", "F1"]
    x = np.arange(len(olcutler))
    genislik = 0.26
    renkler = [st.ACIK, "#A9BBD0", st.LACIVERT]
    for i, (_, satir) in enumerate(kiyas.iterrows()):
        degerler = [satir[o] for o in olcutler]
        cubuk = ax.bar(x + (i - 1) * genislik, degerler, genislik,
                       label=satir["model"],
                       color=renkler[i], edgecolor="#9AA0A6", linewidth=0.5)
        for c, d in zip(cubuk, degerler):
            ax.text(c.get_x() + c.get_width() / 2, d + 0.004,
                    st.ts(d, 3), ha="center", fontsize=8,
                    color="#22262B", rotation=90, va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels([o.capitalize() for o in olcutler])
    ax.set_ylim(0.90, 1.035)
    ax.set_ylabel("Değer")
    # Eksen 0'dan değil 0,90'dan başlıyor. Kesilmiş eksen farkları
    # büyütür; bu yüzden KESME AÇIKÇA İŞARETLENİR. İşaretlenmemiş
    # kesilmiş eksen, şekille yanıltmanın en yaygın biçimidir.
    ax.text(-0.52, 0.902, "⌁", fontsize=16, color=st.KIRMIZI,
            ha="center", va="center", clip_on=False)
    ax.text(-0.46, 0.9105, "eksen 0,90'dan başlıyor", fontsize=8.5,
            color=st.KIRMIZI, rotation=90, va="bottom")
    ax.set_title("Aynı veri, üç çerçeve, üç farklı sayı\n"
                 "Raporlanacak olan üçüncüsüdür", loc="left")
    ax.legend(loc="lower left", ncol=1)
    ax.grid(axis="y")
    st.alt_not(fig, WKAYNAK + "  ·  düşey eksen 0,90'dan başlar (kesilmiş "
                              "eksen, işaretlenmiştir)  ·  ilk iki sayı "
                              "modelin değil, veri setinin kuruluşunun "
                              "ölçüsüdür")
    uretilen.append(("w03_model_kiyas.svg",
                     st.kaydet(fig, K / "w03_model_kiyas.svg")))

    # ===================== W4  ROC =====================
    fig, ax = plt.subplots(figsize=(5.8, 5.4))
    e = W["egriler"]
    ax.plot(e["naif_roc"]["fpr"], e["naif_roc"]["tpr"], color=st.KIRMIZI,
            linewidth=2.2,
            label=f"Naif model — AUC {st.ts(W['naif_model']['ROC_AUC'], 3)}")
    ax.plot(e["roc"]["fpr"], e["roc"]["tpr"], color=st.LACIVERT,
            linewidth=2.2,
            label=f"Yerleşime uygun — AUC "
                  f"{st.ts(W['durust_model']['ROC_AUC'], 3)}")
    ax.plot([0, 1], [0, 1], color=st.GRI, linestyle="--", linewidth=1.1,
            label="rastgele tahmin — AUC 0,500")
    ax.set_xlabel("Yanlış pozitif oranı (1 − özgüllük)")
    ax.set_ylabel("Doğru pozitif oranı (duyarlılık)")
    ax.set_title("ROC eğrisi", loc="left")
    ax.legend(loc="lower right")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    st.alt_not(fig, WKAYNAK + "  ·  köşeye yapışan eğri şüphe uyandırmalıdır")
    uretilen.append(("w04_roc.svg", st.kaydet(fig, K / "w04_roc.svg")))

    # ===================== W5  karışıklık matrisi =====================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.0))
    for ax, model, ad in [(ax1, W["naif_model"], "Naif model (40 özellik)"),
                          (ax2, W["durust_model"],
                           "Yerleşime uygun (11 özellik)")]:
        km = model["karışıklık"]
        M = np.array([[km["DN_doğru_negatif"], km["YP_yanlış_pozitif"]],
                      [km["YN_yanlış_negatif"], km["DP_doğru_pozitif"]]])
        ax.imshow(M, cmap="Blues", vmin=0, vmax=M.max() * 1.15)
        etiket = [["Doğru negatif", "Yanlış pozitif"],
                  ["Yanlış negatif", "Doğru pozitif"]]
        for i in range(2):
            for j in range(2):
                koyu = M[i, j] > M.max() * 0.5
                ax.text(j, i - 0.12, st.tam(M[i, j]), ha="center",
                        va="center", fontsize=19, fontweight="bold",
                        color="white" if koyu else "#22262B")
                ax.text(j, i + 0.22, etiket[i][j], ha="center", va="center",
                        fontsize=9, color="white" if koyu else "#4A4A4A")
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(["meşru", "kimlik avı"])
        ax.set_yticklabels(["meşru", "kimlik avı"])
        ax.set_xlabel("Modelin tahmini")
        ax.set_ylabel("Gerçek durum")
        ax.set_title(f"{ad}\nF1 = {st.ts(model['F1'], 4)}", loc="left")
        ax.grid(visible=False)
    st.alt_not(fig, WKAYNAK + "  ·  test kümesi 1.500 kayıt · "
                              "pozitif sınıf = kimlik avı")
    uretilen.append(("w05_karisiklik.svg",
                     st.kaydet(fig, K / "w05_karisiklik.svg")))

    # ===================== W6  permütasyon önemi =====================
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    perm = pd.DataFrame(W["permutasyon_onemi"]).sort_values("ortalama_düşüş")
    ax.barh(perm["özellik"], perm["ortalama_düşüş"], color=st.TURKUAZ,
            height=0.68, xerr=perm["ss"],
            error_kw={"ecolor": "#44484D", "elinewidth": 1.0, "capsize": 2})
    for i, v in enumerate(perm["ortalama_düşüş"]):
        if v > 0.004:
            ax.text(v + 0.008, i, st.ts(v, 3), va="center", fontsize=8.5)
    ax.set_xlabel("Özellik karıştırıldığında F1'deki düşüş")
    ax.set_title("Model kararını hangi URL nitelikleri taşıyor?\n"
                 "Permütasyon önemi, 20 yineleme", loc="left")
    ax.grid(axis="x")
    st.alt_not(fig, WKAYNAK + "  ·  Tartışma bölümü bu listeden yazılır, "
                              "modelin kendisinden değil")
    uretilen.append(("w06_permutasyon.svg",
                     st.kaydet(fig, K / "w06_permutasyon.svg")))

    # ===================== W7  çapraz doğrulama =====================
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    cd = W["capraz_dogrulama"]
    katlar = cd["f1_katlar"]
    x = np.arange(1, len(katlar) + 1)
    ax.axhspan(cd["f1_ortalama"] - cd["f1_ss"], cd["f1_ortalama"] + cd["f1_ss"],
               color="#DCE8EC", label="ortalama ± 1 standart sapma")
    ax.axhline(cd["f1_ortalama"], color=st.LACIVERT, linewidth=1.6,
               label=f"ortalama F1 = {st.ts(cd['f1_ortalama'], 4)}")
    ax.plot(x, katlar, "o", color=st.AMBER, markersize=10,
            markeredgecolor="white", markeredgewidth=1.6, zorder=4,
            label="tek tek katların F1 değeri")
    for xi, v in zip(x, katlar):
        ax.text(xi, v + 0.0022, st.ts(v, 4), ha="center", fontsize=8.5,
                color="#22262B")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{i}. kat" for i in x])
    ax.set_ylabel("F1")
    ax.set_ylim(min(katlar) - 0.006, max(katlar) + 0.008)
    ax.set_title("Beş katlı çapraz doğrulama — tek bölünme yanıltır",
                 loc="left")
    ax.legend(loc="lower right", ncol=1)
    ax.grid(axis="y")
    st.alt_not(fig, WKAYNAK + "  ·  en iyi kat ile en kötü kat arasındaki "
                              f"fark: {st.ts(max(katlar)-min(katlar), 4)}")
    uretilen.append(("w07_capraz_dogrulama.svg",
                     st.kaydet(fig, K / "w07_capraz_dogrulama.svg")))

    # ===================== N1  tema sıklıkları =====================
    fig, eksenler = plt.subplots(1, 3, figsize=(12.4, 4.6))
    sorular = {1: "Fayda görülen aşamalar", 2: "Çekince ve kaygılar",
               3: "Kurumdan beklentiler"}
    temalar = pd.DataFrame(T["temalar"])
    for ax, (no, baslik) in zip(eksenler, sorular.items()):
        alt = temalar[temalar["soru_no"] == no].sort_values("katilimci")
        renkler = [st.LACIVERT if i == len(alt) - 1 else st.TURKUAZ
                   for i in range(len(alt))]
        ax.barh(alt["tema"], alt["katilimci"], color=renkler, height=0.66)
        for i, (k, y) in enumerate(zip(alt["katilimci"], alt["yuzde"])):
            ax.text(k + 0.22, i, f"{k}  (%{y:.0f})", va="center", fontsize=9)
        ax.set_xlim(0, alt["katilimci"].max() * 1.45)
        ax.set_xlabel("Katılımcı sayısı")
        ax.set_title(f"Soru {no} — {baslik}\n"
                     f"n = {int(alt['soru_yanit_sayisi'].iloc[0])} yanıt",
                     loc="left", fontsize=11)
        ax.grid(axis="x")
        ax.tick_params(axis="y", labelsize=9.5)
    st.alt_not(fig, NKAYNAK)
    uretilen.append(("n01_tema_sikligi.svg",
                     st.kaydet(fig, K / "n01_tema_sikligi.svg")))

    # ===================== N2  kod → tema haritası =====================
    fig, ax = plt.subplots(figsize=(9.0, 7.2))
    kod_kitabi = pd.DataFrame(T["kod_kitabi"])
    kod_kitabi["soru"] = kod_kitabi["kod"].str[1].astype(int)
    atamalar = pd.DataFrame(T["atamalar"])
    kod_sikligi = atamalar["kod"].value_counts().to_dict()
    y = 0
    tema_renk = {}
    renk_dongusu = [st.LACIVERT, st.TURKUAZ, st.AMBER, st.YESIL,
                    st.KIRMIZI, st.MOR, st.GRI]
    for soru in [1, 2, 3]:
        alt = kod_kitabi[kod_kitabi["soru"] == soru]
        for i, tema in enumerate(alt["tema"].unique()):
            tema_renk[tema] = renk_dongusu[i % len(renk_dongusu)]
    for soru in [3, 2, 1]:
        alt = kod_kitabi[kod_kitabi["soru"] == soru]
        ax.text(-0.9, y + 0.6, f"SORU {soru}", fontsize=11,
                fontweight="bold", color="#22262B")
        y += 1.4
        for tema in alt["tema"].unique():
            kodlar = alt[alt["tema"] == tema]
            renk = tema_renk[tema]
            toplam = sum(kod_sikligi.get(k, 0) for k in kodlar["kod"])
            ax.add_patch(Rectangle((-0.85, y - 0.34), 0.14, 0.68,
                                   color=renk, zorder=2))
            ax.text(-0.62, y, f"{tema}  ({toplam})", fontsize=9.8,
                    color="#22262B", va="center", fontweight="bold")
            x = 1.62
            for _, kod in kodlar.iterrows():
                n = kod_sikligi.get(kod["kod"], 0)
                genislik = 0.09 + n * 0.055
                ax.add_patch(Rectangle((x, y - 0.26), genislik, 0.52,
                                       color=renk, alpha=0.30 + min(n, 6) * 0.11,
                                       zorder=2))
                if n:
                    ax.text(x + genislik / 2, y, str(n), ha="center",
                            va="center", fontsize=8, color="#22262B")
                x += genislik + 0.035
            y += 0.78
        y += 0.5
    ax.set_xlim(-1.0, 3.8)
    ax.set_ylim(-0.4, y)
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_title("Kod — tema haritası\n"
                 f"{T['kod_sayisi']} kod, {T['atama_sayisi']} atama · "
                 "kutu genişliği = kodun sıklığı", loc="left")
    st.alt_not(fig, NKAYNAK + "  ·  boş kutu: kod kitabında tanımlı ama "
                              "veride karşılığı çıkmamış kod")
    uretilen.append(("n02_kod_tema_haritasi.svg",
                     st.kaydet(fig, K / "n02_kod_tema_haritasi.svg")))

    # ===================== N3  kodlayıcı uyumu =====================
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    u = T["kodlayici_uyumu"]
    degerler = [u["beklenen_uyum"] * 100, u["gözlenen_uyum"] * 100,
                u["kappa"] * 100]
    etiketler = ["Rastlantıyla\nbeklenen uyum", "Gözlenen uyum",
                 "Cohen kappa\n(rastlantı düzeltilmiş)"]
    renkler = [st.ACIK, st.TURKUAZ, st.LACIVERT]
    cubuk = ax.bar(etiketler, degerler, color=renkler, width=0.52,
                   edgecolor="#9AA0A6", linewidth=0.5)
    for c, d in zip(cubuk, degerler):
        ax.text(c.get_x() + c.get_width() / 2, d + 2.5, f"%{st.ts(d, 1)}",
                ha="center", fontsize=11, fontweight="bold", color="#22262B")
    for esik, ad in [(60, "orta"), (75, "iyi")]:
        ax.axhline(esik, color=st.KIRMIZI, linestyle=":", linewidth=1.0,
                   zorder=0)
        ax.text(-0.46, esik + 1.2,
                f"kappa {st.ts(esik / 100, 2)} — {ad}",
                fontsize=8.5, color=st.KIRMIZI, ha="left", zorder=6)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Yüzde")
    ax.set_title(f"Kodlayıcılar arası uyum — {u['n']} yanıtlık ikinci okuma\n"
                 f"kappa = {st.ts(u['kappa'], 3)} ({u['yorum']} uyum)",
                 loc="left")
    ax.grid(axis="y")
    st.alt_not(fig, NKAYNAK + "  ·  yüzde uyum tek başına yetmez; yaygın bir "
                              "temayı herkese vermek de uyum üretir")
    uretilen.append(("n03_kodlayici_uyumu.svg",
                     st.kaydet(fig, K / "n03_kodlayici_uyumu.svg")))

    print(f"{len(uretilen)} şekil üretildi → {K}")
    for ad_, boyut in uretilen:
        print(f"  {ad_:32s} {boyut/1024:7.1f} KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
