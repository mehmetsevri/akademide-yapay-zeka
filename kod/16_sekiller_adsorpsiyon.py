# -*- coding: utf-8 -*-
"""
16 — Kimya örneği: şekiller

Bölüm 6 ve 7'deki doldurulmuş istemlerin gerçek görsel çıktıları.

Şekiller:
  k01_temizleme    — temizleme adımlarının kaç satırı etkilediği
  k02_anova_kiyas  — eksik model ile bloklanmış modelin F değerleri
  k03_etkilesim    — pH × adsorban etkileşim grafiği
  k04_izoterm      — Langmuir ve Freundlich uyumu

Kullanım:
  python 16_sekiller_adsorpsiyon.py <analiz_json> <veri_csv> <şekil_klasörü>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sekil_stili as st
import matplotlib.pyplot as plt

KAYNAK = ("Kaynak: sentetik adsorpsiyon veri seti (216 deney tasarlandı, "
          "201 geçerli ölçüm) · yöntem örneğidir, bulgu değildir")


def main(analiz_json: str, veri_csv: str, sekil_klasoru: str) -> None:
    st.stil_kur()
    S = json.loads(pathlib.Path(analiz_json).read_text(encoding="utf-8"))
    df = pd.read_csv(veri_csv, encoding="utf-8-sig")
    K = pathlib.Path(sekil_klasoru)
    uretilen = []

    # ----------------------------------------------- k01: temizleme adımları
    # Yatay çubuk seçildi: adım adları uzun, dikey eksende okunmaz.
    gunluk = pd.read_csv(
        pathlib.Path(veri_csv).parent / "adsorpsiyon_karar_gunlugu.csv",
        encoding="utf-8-sig")
    # Türetilmiş değişken adımı bütün satırları "etkiliyor"; bu bir
    # temizleme kararı değil, sütun ekleme. Grafikte yer almamalı.
    g = gunluk[~gunluk["adim"].str.startswith("Türetilmiş")].copy()
    # Üç karar türü üç renkte: okur hangi adımın veri yitirdiğini,
    # hangisinin değer düzelttiğini, hangisinin yalnız not düştüğünü
    # bir bakışta ayırabilmeli.
    def tur(karar):
        if "çıkarıldı" in karar or "düşürüldü" in karar:
            return "cikarildi"
        if "işaretlendi" in karar or "bildirildi" in karar:
            return "bildirildi"
        return "duzeltildi"

    RENK = {"cikarildi": st.KIRMIZI, "duzeltildi": st.TURKUAZ,
            "bildirildi": st.GRI}
    ETIKET = {"cikarildi": "satır çıkarıldı",
              "duzeltildi": "değer düzeltildi",
              "bildirildi": "yalnız işaretlendi"}
    turler = [tur(k) for k in g["karar"]]

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    y = np.arange(len(g))[::-1]
    ax.barh(y, g["etkilenen_satir"], color=[RENK[t] for t in turler],
            height=0.62)
    for yi, v in zip(y, g["etkilenen_satir"]):
        ax.text(v + 0.7, yi, str(int(v)), va="center", fontsize=9.5,
                color="#2A2A2A")
    ax.set_yticks(y)
    ax.set_yticklabels(g["adim"])
    ax.set_xlabel("Etkilenen satır sayısı")
    ax.set_xlim(0, g["etkilenen_satir"].max() * 1.12)
    ax.set_title("Temizleme adımlarının kaç satırı etkilediği\n"
                 "215 ham satırdan 201 analiz satırına (%6,5 çıkarıldı)",
                 loc="left")
    ax.grid(axis="x")
    # Gösterge için çubukların üstünde bir şerit açılıyor. Eksenin
    # altına konursa kaynak notuyla yer değiştirir; kaynak notu her
    # şeklin en alt satırı olmalı.
    from matplotlib.patches import Patch
    ax.set_ylim(-0.62, len(g) + 0.15)
    ax.legend(handles=[Patch(facecolor=RENK[t], label=ETIKET[t])
                       for t in ("cikarildi", "duzeltildi", "bildirildi")],
              loc="upper left", bbox_to_anchor=(-0.005, 1.03), ncol=3,
              handlelength=1.1, handletextpad=0.5, columnspacing=2.0)
    st.alt_not(fig, KAYNAK + "  ·  şüpheli dönem çıkarılmadı, etiketlendi; "
                             "duyarlılık analizi onsuz da yinelendi")
    uretilen.append(("k01_temizleme.svg",
                     st.kaydet(fig, K / "k01_temizleme.svg")))

    # ------------------------------------------- k02: eksik model kıyaslaması
    eksik = {r["kaynak"]: r for r in S["adim0_eksik_model"]}
    tam_m = {r["kaynak"]: r for r in S["anova"]}
    ilgi = ["adsorban", "pH", "sıcaklık", "adsorban × pH"]

    # Nokta-çizgi (dumbbell) düzeni: logaritmik eksende çubuk uzunluğu
    # oran taşımaz, nokta konumu taşır. İki kurulumun F değeri arasına
    # çizilen çizgi, farkın büyüklüğünü doğrudan görünür kılar.
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    y = np.arange(len(ilgi))[::-1]
    f_eksik = np.array([eksik[k]["F"] for k in ilgi])
    f_tam = np.array([tam_m[k]["F"] for k in ilgi])
    for yi, a, b in zip(y, f_eksik, f_tam):
        ax.plot([a, b], [yi, yi], color=st.ACIK, lw=3.5, zorder=1,
                solid_capstyle="round")
    ax.scatter(f_eksik, y, s=90, color=st.GRI, zorder=3,
               label="derişim ve süre modelde DEĞİL")
    ax.scatter(f_tam, y, s=90, color=st.LACIVERT, zorder=3,
               label="derişim ve süre blok olarak modelde")
    # Varsayılan log biçimleyici üs gösterimi (10²) kullanır; üs küçük
    # puntoda kaybolduğu için düz sayıya çeviriyoruz.
    ax.set_xscale("log")
    ax.set_xlim(0.0009, 700)
    ax.set_xticks([0.001, 0.01, 0.1, 1, 10, 100])
    ax.set_xticklabels(["0,001", "0,01", "0,1", "1", "10", "100"])
    ax.axvline(1, color=st.KIRMIZI, lw=1, ls="--", zorder=0)
    ax.text(1.18, len(ilgi) - 0.78, "F = 1\netki yok sınırı", fontsize=8.5,
            color=st.KIRMIZI, va="top")
    for yi, v in zip(y, f_eksik):
        # Nokta sol kenara yakınsa etiket eksen dışına taşar ve kategori
        # adının üstüne biner; o durumda etiketi noktanın üstüne alıyoruz.
        if v / 1.35 < ax.get_xlim()[0] * 3:
            ax.text(v, yi + 0.26, st.ts(v, 3), va="bottom", ha="center",
                    fontsize=8.5, color=st.GRI)
        else:
            ax.text(v / 1.35, yi, st.ts(v, 3), va="center", ha="right",
                    fontsize=8.5, color=st.GRI)
    for yi, v in zip(y, f_tam):
        ax.text(v * 1.35, yi, st.ts(v, 1), va="center", fontsize=8.5,
                color=st.LACIVERT)
    ax.set_yticks(y)
    ax.set_yticklabels(ilgi)
    ax.set_ylim(-0.95, len(ilgi) - 0.55)
    ax.set_xlabel("F değeri (logaritmik ölçek)")
    ax.set_title("Aynı veri, iki model kurulumu\n"
                 "İhmal edilen faktörün varyansı hata terimini şişirir",
                 loc="left")
    ax.grid(axis="x")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=2,
              handletextpad=0.3, columnspacing=1.6)
    st.alt_not(fig, KAYNAK + "  ·  gri kurulumda hiçbir etki anlamlı "
                             "değil; lacivert kurulumda dördü de anlamlı")
    uretilen.append(("k02_anova_kiyas.svg",
                     st.kaydet(fig, K / "k02_anova_kiyas.svg")))

    # ----------------------------------------------------- k03: etkileşim
    # Etkileşim grafiği: paralel olmayan çizgiler etkileşim demektir.
    # Bu yüzden ham ortalama yerine blok düzeltilmiş ortalama kullanmak
    # gerekir; aksi hâlde çizgiler bloklardan gelen kaymayı da taşır.
    # Düzeltme: her hücre ortalamasını, o derişim-süre bloğunun genel
    # ortalamasına göre merkezleyip genel ortalamayı geri ekliyoruz.
    genel = df["q_mgG"].mean()
    blok_ort = df.groupby(["baslangic_derisim_mgL", "temas_suresi_dk"],
                          observed=True)["q_mgG"].transform("mean")
    df = df.assign(q_duz=df["q_mgG"] - blok_ort + genel)
    ort = (df.groupby(["pH", "adsorban"], observed=True)["q_duz"]
           .agg(["mean", "sem", "size"]).reset_index())

    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    ad_g = {"cay_posasi": "Çay posası", "ticari": "Ticari kömür"}
    for i, (ads, renk) in enumerate((("cay_posasi", st.AMBER),
                                     ("ticari", st.LACIVERT))):
        a = ort[ort["adsorban"] == ads].sort_values("pH")
        ax.errorbar(a["pH"], a["mean"], yerr=1.96 * a["sem"], color=renk,
                    marker="o", markersize=6, capsize=4, lw=2)
        # Doğrudan etiketleme: açıklama kutusu yerine çizginin ucuna yaz
        ax.text(a["pH"].iloc[-1] + 0.28, a["mean"].iloc[-1],
                ad_g[ads], color=renk, va="center", fontsize=10,
                fontweight="bold")
    ax.set_xticks([3, 7, 10])
    ax.set_xlabel("Çözelti pH'ı")
    ax.set_ylabel("Blok düzeltilmiş q (mg/g)")
    ax.set_xlim(2.3, 12.4)
    e = [r for r in S["anova"] if r["kaynak"] == "adsorban × pH"][0]
    ax.set_title("pH × adsorban etkileşimi\n"
                 f"F(2, 186) = {st.ts(e['F'], 2)} · "
                 f"p = {st.ts(e['PR(>F)'], 3)} · "
                 f"kısmi eta kare = {st.ts(e['kismi_eta_kare'], 3)}",
                 loc="left")
    st.alt_not(fig, KAYNAK + "  ·  çubuklar %95 güven aralığı · çizgiler "
                             "paralel olmadığı için etkileşim var")
    uretilen.append(("k03_etkilesim.svg",
                     st.kaydet(fig, K / "k03_etkilesim.svg")))

    # ------------------------------------------------------- k04: izotermler
    # Ortak y ekseni: iki adsorbanın kapasitesi ancak aynı
    # ölçekte karşılaştırılabilir. x eksenleri ayrı kalıyor,
    # çünkü denge derişimi aralıkları gerçekten farklı.
    fig, axlar = plt.subplots(1, 2, figsize=(8.2, 3.6),
                              sharey=True)
    for ax, (ads, renk) in zip(axlar, (("cay_posasi", st.AMBER),
                                       ("ticari", st.YESIL))):
        a = df[(df["adsorban"] == ads) & (df["pH"] == 7)
               & (df["sicaklik_C"] == 45) & (df["temas_suresi_dk"] == 120)]
        ce = a["denge_derisim_mgL"].to_numpy(float)
        q = a["q_mgG"].to_numpy(float)
        iz = S["izoterm"][ads]
        ax.scatter(ce, q, color=renk, s=42, zorder=3,
                   label="ölçülen", edgecolor="white", lw=0.6)
        cx = np.linspace(ce.min() * 0.85, ce.max() * 1.1, 200)
        qmax, kl = iz["langmuir"]["qmax_mgG"], iz["langmuir"]["KL_Lmg"]
        kf, n = iz["freundlich"]["KF"], iz["freundlich"]["n"]
        # Eğriler doğrusal olmayan en küçük kareler uyumundan; AIC
        # karşılaştırmasında kazanan model kesiksiz çizgiyle veriliyor.
        kazanan = iz["daha_iyi"]
        ax.plot(cx, qmax * kl * cx / (1 + kl * cx), color=st.LACIVERT,
                lw=1.8, ls="-" if kazanan == "Langmuir" else "--",
                label=f"Langmuir · AIC {st.ts(iz['langmuir']['AIC'], 1)}")
        ax.plot(cx, kf * cx ** (1 / n), color=st.KIRMIZI, lw=1.8,
                ls="-" if kazanan == "Freundlich" else "--",
                label=f"Freundlich · AIC {st.ts(iz['freundlich']['AIC'], 1)}")
        ax.set_xlabel("Denge derişimi $C_e$ (mg/L)")
        ax.set_title(ad_g[ads], loc="left")
        ax.legend(loc="lower right", fontsize=8.5)
    axlar[0].set_ylabel("Tutunan miktar $q$ (mg/g)")
    fig.suptitle("İzoterm uyumu (doğrusal olmayan en küçük kareler)\n"
                 "pH 7 · 45 °C · 120 dakika",
                 x=0.005, ha="left", fontsize=12, fontweight="bold",
                 color=st.LACIVERT, y=1.16)
    st.alt_not(fig, KAYNAK + "  ·  kesiksiz çizgi: AIC'ye göre daha iyi "
                             "uyan model · n = 8-9 nokta")
    uretilen.append(("k04_izoterm.svg",
                     st.kaydet(fig, K / "k04_izoterm.svg")))

    print(f"{len(uretilen)} şekil üretildi → {K}")
    for ad_, boyut in uretilen:
        print(f"  {ad_:26s} {boyut/1024:7.1f} KB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
