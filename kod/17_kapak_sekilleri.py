# -*- coding: utf-8 -*-
"""
17 — Karşılama sayfası şekilleri

Bu betiğin verisi SENTETİK DEĞİL. Sayılar yayımlanmış anket ve
bibliyometri çalışmalarından alınmıştır; her veri noktasının kaynağı
sözlükte kendi satırında durur ve şeklin altında da verilir.

Şekiller:
  a01_kullanim_artisi — araştırmacı anketlerinde YZ kullanımı
  a02_beyan_acigi     — yayımlanan makalelerde LLM izi ile beyan oranı

Kullanım:
  python 17_kapak_sekilleri.py <şekil_klasörü>
"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sekil_stili as st
import matplotlib.pyplot as plt

# --------------------------------------------------------------- veriler
# Wiley ExplanAItions, iki dalga. 2024 dalgası ~4.900 araştırmacı,
# 2025 dalgası 2.430 araştırmacı. Örneklemler aynı değil; oranlar bu
# yüzden "aynı kişilerin değişimi" değil, iki ayrı kesit.
# Son satırın 2025 değeri bir ÜST SINIRDIR: Wiley raporu kesin sayı
# vermiyor, "üçte birin altı" diyor. Uydurma bir ondalık yazmak yerine
# 33 çizilip etikete "<" konuyor.
ANKET = [
    ("Herhangi bir işte\nYZ aracı kullanan", 57, 84, ""),
    ("Araştırma ve yayın\ngörevlerinde kullanan", 45, 62, ""),
    ("YZ'nin insanı aştığına\ninanan", 53, 33, "<"),
]

# Yayımlanan metinlerde LLM izi: yöntem başına tahminler.
# Hepsi sözcük sıklığı kaymasına dayanır; tek tek makale için
# "bu YZ yazdı" demez. Aralık, yöntemin kendi belirsizliğidir.
IZ = [
    ("Gray (2024)\ntüm makaleler, 2024", 10.0, "bibliyometrik"),
    ("Liang ve ark. (2025)\nbilgisayar bilimleri", 22.0, "sözcük sıklığı"),
    ("Liang ve ark. (2025)\nmatematik", 9.0, "sözcük sıklığı"),
    ("Siler (2025)\ndört yayıncı, 2025", 57.0, "sözcük sıklığı"),
]
# Web of Science'ta 2024 için açık ÜYZ beyanı bulunan makale sayısı,
# o yıl dizinlenen toplam makaleye oranla.
BEYAN_SAYI, BEYAN_TOPLAM = 1551, 2_600_000

KAYNAK_ANKET = ("Kaynak: Wiley ExplanAItions, 2024 ve 2025 dalgaları · "
                "iki ayrı kesit, aynı kişiler değil\nSon satırın 2025 "
                "değeri üst sınırdır: rapor kesin oran vermeyip "
                "\u201cüçte birin altı\u201d diyor.")
KAYNAK_IZ = ("Kaynak: Gray (2024) · Liang ve ark., Nature Human Behaviour "
             "(2025) · Siler, PNAS (2025) · WoS beyan sayımı: Gray (2024)")


def main(sekil_klasoru: str) -> None:
    st.stil_kur()
    K = pathlib.Path(sekil_klasoru)
    uretilen = []

    # ------------------------------------------- a01: anketlerde kullanım
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    y = np.arange(len(ANKET))[::-1]
    h = 0.32
    eski = [a[1] for a in ANKET]
    yeni = [a[2] for a in ANKET]
    onek = [a[3] for a in ANKET]
    ax.barh(y + h / 2, eski, h, color=st.ACIK, label="2024")
    ax.barh(y - h / 2, yeni, h, color=st.LACIVERT, label="2025")
    for yi, v in zip(y + h / 2, eski):
        ax.text(v + 1.2, yi, f"%{v}", va="center", fontsize=9.5, color=st.GRI)
    for yi, v, o in zip(y - h / 2, yeni, onek):
        ax.text(v + 1.2, yi, f"{o}%{v}", va="center", fontsize=9.5,
                color=st.LACIVERT, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([a[0] for a in ANKET], fontsize=9.5)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Araştırmacıların yüzdesi")
    ax.set_title("Bir yılda ne değişti\n"
                 "Kullanım hızla arttı, güven azaldı", loc="left")
    ax.grid(axis="x")
    ax.legend(loc="lower right", ncol=2)
    st.alt_not(fig, KAYNAK_ANKET)
    uretilen.append(("a01_kullanim_artisi.svg",
                     st.kaydet(fig, K / "a01_kullanim_artisi.svg")))

    # --------------------------------------------- a02: beyan açığı
    # Ölçek farkı çok büyük (%0,06 ile %57). Tek eksende ikisi birden
    # okunamaz; bu yüzden tahminler çubuk, beyan oranı ayrı bir çizgi
    # ve açık etiketle veriliyor.
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    x = np.arange(len(IZ))
    # Dört tahmin de sözcük sıklığı kaymasına dayanıyor; aralarındaki
    # fark yöntemden değil korpus ve alandan geliyor. Bu yüzden tek renk:
    # farklı renk, olmayan bir yöntem ayrımı varmış izlenimi verirdi.
    ax.bar(x, [v for _, v, _ in IZ], 0.56, color=st.TURKUAZ)
    for xi, (_, v, _) in zip(x, IZ):
        ax.text(xi, v + 1.4, f"%{st.ts(v, 0)}", ha="center", fontsize=10,
                fontweight="bold", color="#2A2A2A")
    beyan = BEYAN_SAYI / BEYAN_TOPLAM * 100
    ax.axhline(beyan, color=st.KIRMIZI, lw=1.8)
    # Etiket sol üstte: en yüksek çubuk sağda olduğu için oraya
    # yazılırsa üstüne biner.
    ax.text(-0.42, 60.5,
            f"Kırmızı çizgi — açıkça beyan edilen: %{st.ts(beyan, 2)}\n"
            f"{st.tam(BEYAN_SAYI)} makale / {st.tam(BEYAN_TOPLAM)} "
            f"makale (Web of Science, 2024)",
            ha="left", va="top", fontsize=9, color=st.KIRMIZI)
    ax.set_xticks(x)
    ax.set_xticklabels([a[0] for a in IZ], fontsize=9)
    ax.set_ylabel("Makalelerin yüzdesi")
    ax.set_ylim(0, 66)
    ax.set_title("Kullanım yaygın, beyan neredeyse yok\n"
                 "Yayımlanmış metinlerde LLM izi: dört ayrı tahmin",
                 loc="left")
    st.alt_not(fig, KAYNAK_IZ + "\nTahminler sözcük sıklığı kaymasına "
                                "dayanır; tek bir makale için 'bunu yapay "
                                "zekâ yazdı' demezler.")
    uretilen.append(("a02_beyan_acigi.svg",
                     st.kaydet(fig, K / "a02_beyan_acigi.svg")))

    print(f"{len(uretilen)} şekil üretildi → {K}")
    for ad_, boyut in uretilen:
        print(f"  {ad_:28s} {boyut/1024:7.1f} KB")


if __name__ == "__main__":
    main(sys.argv[1])
