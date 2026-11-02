# -*- coding: utf-8 -*-
"""
20 — Durum raporu şekilleri

VERİ SENTETİK DEĞİLDİR. Bütün sayılar yayımlanmış çalışmalardan ve
kurumsal raporlardan alınmıştır; her veri noktasının kaynağı aşağıdaki
sözlüklerde kendi satırında durur.

Şekiller:
  d01_gonderim      — yayıncı bazında gönderim hacmi artışı
  d02_llm_izi       — alanlara göre LLM izi ve beyan oranı
  d03_hakemlik      — hakem daveti kabul oranının düşüşü
  d04_ai_skoru      — AI skoruna göre editoryal sonuç
  d05_yanlis_pozitif— dedektörlerin dil kökenine göre hatası
  d06_iddia_kanit   — dolaşımdaki iddia ile doğrulanmış bulgu

Kullanım:
  python 20_durum_raporu_sekilleri.py <şekil_klasörü>
"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sekil_stili as st
import matplotlib.pyplot as plt

# --------------------------------------------------------------- veriler
# Yayıncıların kendi yıllık raporlarından ve basın açıklamalarından.
# Elsevier sayıları "3 milyon", ">3,5 milyon", ">4,2 milyon" biçiminde
# alt sınır olarak bildirilmiştir; grafikte alt sınır çizilir.
GONDERIM = {
    "Elsevier": [(2023, 3.0), (2024, 3.5), (2025, 4.2)],
    "Springer Nature": [(2024, 2.3), (2025, 3.1)],
}
# STM 2026 raporu, Dimensions verisi: makale + derleme + bildiri
KURESEL = [(2019, 3.9), (2024, 5.7)]

# LLM izi tahminleri. Hepsi sözcük sıklığı kaymasına dayanır; tek bir
# makale için "bunu yapay zekâ yazdı" demezler.
LLM_IZI = [
    ("Bilgisayar bilimleri\nLiang ve ark., 2025", 22.0),
    ("PubMed özetleri (alt sınır)\nScience Advances, 2025", 13.5),
    ("Matematik\nLiang ve ark., 2025", 9.0),
    ("Nature portföyü\nLiang ve ark., 2025", 9.0),
]
# Q1 dergilerde açık yapay zekâ beyanı — 5,2 milyon makale taraması
BEYAN_ORANI = 0.1          # 2023 sonrası, yüzde
BEYAN_2025Q1 = 0.43        # 2025'in ilk çeyreği, yüzde

# ScholarOne, sekiz yıllık işlem verisi
HAKEM_KABUL = [(2018, 43), (2024, 22)]
HAKEM_HAVUZ_BUYUME = 54    # yüzde, 2018'den beri
HAKEM_DAVET_BUYUME = 100   # yüzde, 2018'den beri (">%100")

# Organization Science, "More Versus Better" editoryal çalışması.
# Pangram skoruna göre dört grup; burada uçlar gösteriliyor.
AI_SKORU = {
    "AI skoru < %15": {"desk": 43.7, "hakem": 56.3, "rr": 11.9},
    "AI skoru ≥ %70": {"desk": 69.6, "hakem": 30.4, "rr": 3.2},
}

# Liang ve ark. (2023), Patterns. Yedi ticari dedektör.
YANLIS_POZITIF = [
    ("Ana dili İngilizce olan\nöğrenci metinleri", 5.0,
     "sekizinci sınıf kompozisyonları, n = 88"),
    ("Ana dili İngilizce olmayan\nTOEFL metinleri", 61.2,
     "n = 91, yedi dedektörün ortalaması"),
    ("Aynı TOEFL metinleri,\nsözcük dağarcığı zenginleştirilmiş", 11.6,
     "metin insan yazısı; yalnız dili değişti"),
]

# Dolaşımdaki iddia ile doğrulanmış bulgu
IDDIA_KANIT = [
    ("Masa başı ret\n(AI skoru ≥ %70)", 96.0, 69.6),
    ("Hakeme ulaşan\n(AI skoru ≥ %70)", 3.0, 30.4),
]

KAYNAK_GONDERIM = ("Kaynak: RELX 2025 yıllık raporu · Springer Nature 2025 "
                   "yıllık raporu · STM 2026 raporu (Dimensions verisi)")
KAYNAK_ORGSCI = ("Kaynak: Organization Science, “More Versus Better” "
                 "editoryal çalışması (2026) · Pangram skorları")


def main(sekil_klasoru: str) -> None:
    st.stil_kur()
    K = pathlib.Path(sekil_klasoru)
    uretilen = []

    # ------------------------------------------------- d01: gönderim hacmi
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.4, 3.6),
                                   gridspec_kw={"width_ratios": [1.45, 1]})
    for (ad, seri), renk in zip(GONDERIM.items(), (st.LACIVERT, st.TURKUAZ)):
        yillar = [y for y, _ in seri]
        deger = [d for _, d in seri]
        ax1.plot(yillar, deger, marker="o", markersize=7, color=renk, lw=2.2)
        ax1.text(yillar[-1] + 0.06, deger[-1], f"  {ad}", color=renk,
                 va="center", fontsize=10, fontweight="bold")
        for y, d in seri:
            ax1.text(y, d + 0.13, st.ts(d, 1), ha="center", fontsize=9,
                     color=renk)
    ax1.set_xticks([2023, 2024, 2025])
    ax1.set_xlim(2022.7, 2026.9)
    ax1.set_ylim(1.9, 4.9)
    ax1.set_ylabel("Yıllık gönderim (milyon)")
    ax1.set_title("Yayıncı bazında gönderim\nİki yılda yaklaşık %40 artış",
                  loc="left")

    yillar = [y for y, _ in KURESEL]
    deger = [d for _, d in KURESEL]
    ax2.bar([str(y) for y in yillar], deger, 0.5,
            color=[st.ACIK, st.LACIVERT])
    for i, d in enumerate(deger):
        ax2.text(i, d + 0.12, st.ts(d, 1), ha="center", fontsize=10,
                 fontweight="bold")
    ax2.set_ylim(0, 6.9)
    ax2.set_ylabel("Milyon yayın")
    artis = (deger[1] - deger[0]) / deger[0] * 100
    ax2.set_title(f"Küresel yayın hacmi\nBeş yılda %{st.ts(artis, 0)} artış",
                  loc="left")
    st.alt_not(fig, KAYNAK_GONDERIM + "\nElsevier sayıları alt sınır olarak "
                                      "bildirilmiştir. Küresel hacim makale, "
                                      "derleme ve bildirileri kapsar.")
    uretilen.append(("d01_gonderim.svg", st.kaydet(fig, K / "d01_gonderim.svg")))

    # --------------------------------------------------- d02: LLM izi
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    y = np.arange(len(LLM_IZI))[::-1]
    ax.barh(y, [v for _, v in LLM_IZI], 0.56, color=st.TURKUAZ)
    for yi, (_, v) in zip(y, LLM_IZI):
        ax.text(v + 0.5, yi, f"%{st.ts(v, 1)}", va="center", fontsize=10,
                fontweight="bold", color="#2A2A2A")
    ax.axvline(BEYAN_ORANI, color=st.KIRMIZI, lw=2)
    ax.text(0.75, len(LLM_IZI) - 0.45,
            f"Açıkça beyan edilen: %{st.ts(BEYAN_ORANI, 1)}\n"
            f"(2025'in ilk çeyreğinde %{st.ts(BEYAN_2025Q1, 2)})",
            fontsize=9.5, color=st.KIRMIZI, va="top")
    ax.set_yticks(y)
    ax.set_yticklabels([a for a, _ in LLM_IZI], fontsize=9)
    ax.set_xlabel("Metinlerin yüzdesi")
    ax.set_xlim(0, 26)
    ax.set_title("Metinde LLM izi var, beyanda yok\n"
                 "Tahmin edilen kullanım ile açık beyan arasındaki uçurum",
                 loc="left")
    ax.grid(axis="x")
    st.alt_not(fig, "Kaynak: Liang ve ark., Nature Human Behaviour (2025) · "
                    "Science Advances (2025) · 5,2 milyon makalelik Q1 "
                    "taraması (2026)\nTahminler sözcük sıklığı kaymasına "
                    "dayanır; tek bir makale için kanıt değildir.")
    uretilen.append(("d02_llm_izi.svg", st.kaydet(fig, K / "d02_llm_izi.svg")))

    # ------------------------------------------------- d03: hakemlik
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    yillar = [y for y, _ in HAKEM_KABUL]
    deger = [d for _, d in HAKEM_KABUL]
    ax.plot(yillar, deger, marker="o", markersize=9, color=st.KIRMIZI, lw=2.6)
    for y_, d in HAKEM_KABUL:
        ax.text(y_, d + 1.6, f"%{d}", ha="center", fontsize=12,
                fontweight="bold", color=st.KIRMIZI)
    ax.set_xticks(yillar)
    ax.set_xlim(2017.4, 2024.6)
    ax.set_ylim(0, 52)
    ax.set_ylabel("Hakem davetini kabul oranı")
    ax.set_title("Hakem havuzu büyüdü, kabul oranı yarıya indi\n"
                 f"Havuz %{HAKEM_HAVUZ_BUYUME} büyürken davet sayısı "
                 f"%{HAKEM_DAVET_BUYUME}'den fazla arttı", loc="left")
    # Bir kabul için gereken davet sayısı, ikincil eksende anlatılır
    ax.annotate("Bir kabul için\nortalama 4,5 davet", xy=(2024, 22),
                xytext=(2022.3, 38), fontsize=9.5, color=st.GRI,
                arrowprops=dict(arrowstyle="->", color=st.GRI, lw=1))
    st.alt_not(fig, "Kaynak: ScholarOne, sekiz yıllık işlem verisi · "
                    "2026 Future of Peer Review raporu")
    uretilen.append(("d03_hakemlik.svg", st.kaydet(fig, K / "d03_hakemlik.svg")))

    # ------------------------------------------------- d04: AI skoru
    fig, ax = plt.subplots(figsize=(7.6, 3.7))
    gruplar = list(AI_SKORU)
    x = np.arange(len(gruplar))
    w = 0.26
    kategori = (("desk", "Masa başında reddedildi", st.KIRMIZI),
                ("hakem", "Hakeme gönderildi", st.TURKUAZ),
                ("rr", "Düzelt ve yeniden gönder", st.LACIVERT))
    for i, (anahtar, etiket, renk) in enumerate(kategori):
        deger = [AI_SKORU[g][anahtar] for g in gruplar]
        ax.bar(x + (i - 1) * w, deger, w, color=renk, label=etiket)
        for xi, v in zip(x + (i - 1) * w, deger):
            ax.text(xi, v + 1.2, f"%{st.ts(v, 1)}", ha="center",
                    fontsize=9, color=renk, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(gruplar, fontsize=10.5)
    ax.set_ylabel("Gönderimlerin yüzdesi")
    # Gösterge çubukların üstündeki şeritte: eksenin altına konursa
    # kaynak notuyla yer değiştirir ve ikisi üst üste biner.
    ax.set_ylim(0, 96)
    ax.set_title("Yüksek AI skoru ret olasılığını artırıyor — ama\n"
                 "üçte biri yine de hakeme ulaşıyor", loc="left")
    ax.legend(loc="upper left", ncol=3, bbox_to_anchor=(-0.005, 1.02),
              handlelength=1.1, handletextpad=0.5, columnspacing=1.8)
    st.alt_not(fig, KAYNAK_ORGSCI + "\nÇalışmanın yazarları, bu makalelerin "
                                    "yüksek AI skoru NEDENİYLE reddedilmediğini "
                                    "belirtiyor.")
    uretilen.append(("d04_ai_skoru.svg", st.kaydet(fig, K / "d04_ai_skoru.svg")))

    # --------------------------------------- d05: yanlış pozitif
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    y = np.arange(len(YANLIS_POZITIF))[::-1]
    renkler = [st.YESIL, st.KIRMIZI, st.AMBER]
    ax.barh(y, [v for _, v, _ in YANLIS_POZITIF], 0.52, color=renkler)
    for yi, (_, v, alt) in zip(y, YANLIS_POZITIF):
        ax.text(v + 1.2, yi + 0.12, f"%{st.ts(v, 1)}", va="center",
                fontsize=11, fontweight="bold", color="#2A2A2A")
        ax.text(v + 1.2, yi - 0.16, alt, va="center", fontsize=8,
                color=st.GRI)
    ax.set_yticks(y)
    ax.set_yticklabels([a for a, _, _ in YANLIS_POZITIF], fontsize=9.5)
    ax.set_xlabel("Yapay zekâ ürünü diye yanlış işaretlenme oranı")
    ax.set_xlim(0, 86)
    ax.set_title("Dedektörler yapay zekâyı değil, dil çeşitliliğini ölçüyor\n"
                 "Aynı insan metni, yalnız sözcükleri zenginleşince aklandı",
                 loc="left")
    ax.grid(axis="x")
    st.alt_not(fig, "Kaynak: Liang ve ark., Patterns (2023) · yedi ticari "
                    "dedektör · 91 TOEFL ve 88 ana dili İngilizce metin")
    uretilen.append(("d05_yanlis_pozitif.svg",
                     st.kaydet(fig, K / "d05_yanlis_pozitif.svg")))

    # ------------------------------------------- d06: iddia ve kanıt
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    y = np.arange(len(IDDIA_KANIT))[::-1]
    h = 0.3
    iddia = [a for _, a, _ in IDDIA_KANIT]
    kanit = [k for _, _, k in IDDIA_KANIT]
    ax.barh(y + h / 2, iddia, h, color=st.ACIK,
            label="dolaşımdaki iddia", edgecolor=st.GRI, lw=0.8)
    ax.barh(y - h / 2, kanit, h, color=st.LACIVERT,
            label="doğrulanmış bulgu")
    for yi, v in zip(y + h / 2, iddia):
        ax.text(v + 1.4, yi, f"%{st.ts(v, 0)}", va="center", fontsize=10,
                color=st.GRI)
    for yi, v in zip(y - h / 2, kanit):
        ax.text(v + 1.4, yi, f"%{st.ts(v, 1)}", va="center", fontsize=10,
                fontweight="bold", color=st.LACIVERT)
    ax.set_yticks(y)
    ax.set_yticklabels([a for a, _, _ in IDDIA_KANIT], fontsize=10)
    ax.set_xlim(0, 112)
    ax.set_xlabel("Gönderimlerin yüzdesi")
    ax.set_title("Aynı olgu, iki ayrı sayı\n"
                 "Dolaşımdaki rakam kaynağına kadar izlenmemişti", loc="left")
    ax.grid(axis="x")
    ax.legend(loc="lower right")
    st.alt_not(fig, KAYNAK_ORGSCI + "\nSoldaki sayılar ikincil kaynaklarda "
                                    "dolaşan değerlerdir; birincil çalışmada "
                                    "karşılıkları yoktur.")
    uretilen.append(("d06_iddia_kanit.svg",
                     st.kaydet(fig, K / "d06_iddia_kanit.svg")))

    print(f"{len(uretilen)} şekil üretildi → {K}")
    for ad_, boyut in uretilen:
        print(f"  {ad_:26s} {boyut/1024:7.1f} KB")


if __name__ == "__main__":
    main(sys.argv[1])
