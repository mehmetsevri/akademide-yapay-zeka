# -*- coding: utf-8 -*-
"""
14 — Kimya örneği: adsorpsiyon verisini temizleme

Bölüm 6'daki doldurulmuş temizleme isteminin gerçekten koşturulmuş
hâli. İstem yedi kirin her biri için ne yapılacağını söylüyordu;
bu betik tam olarak onu uygular ve her kararı gerekçesiyle günlüğe
yazar.

Temizleme kuralı: hiçbir satır sessizce silinmez. Silinen her satırın
sayısı ve nedeni karar günlüğüne yazılır.

Kullanım:
  python 14_adsorpsiyon_temizle.py <ham_klasör> <çıktı_klasörü>
"""
import pathlib
import sys

import numpy as np
import pandas as pd

HACIM_L = 0.05
KUTLE_G = 0.10

# Yazım çeşitlerinin tek bir ada eşlenmesi. Küçük harfe indirip
# boşlukları kırptıktan sonra bakılır.
ADSORBAN_ESLEME = {
    "cay_posasi": "cay_posasi", "çay posası": "cay_posasi",
    "cay posasi": "cay_posasi", "çp": "cay_posasi",
    "tea waste": "cay_posasi",
    "ticari": "ticari", "ticari ak": "ticari", "commercial": "ticari",
}


def main(ham_klasoru: str, cikti_klasoru: str) -> None:
    ham = pathlib.Path(ham_klasoru) / "adsorpsiyon_ham.csv"
    df = pd.read_csv(ham, encoding="utf-8-sig")
    baslangic = len(df)
    gunluk = []

    def kaydet(adim, karar, gerekce, etkilenen):
        gunluk.append({"adim": adim, "karar": karar,
                       "gerekce": gerekce, "etkilenen_satir": etkilenen})

    # --- 1. Mükerrer satırlar -------------------------------------------
    # deney_no benzersiz olmalı; aynı numara iki kez varsa ikinci girişi
    # düşürüyoruz. İçerikleri aynı olduğu için bilgi yitimi yok.
    mukerrer = int(df.duplicated(keep="first").sum())
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    kaydet("Mükerrer kayıt", "İkinci giriş düşürüldü",
           "Bütün sütunları birebir aynı; çifte veri girişi.", mukerrer)

    # --- 2. Adsorban adı birleştirme ------------------------------------
    anahtar = df["adsorban"].astype(str).str.strip().str.lower()
    tanimsiz = anahtar[~anahtar.isin(ADSORBAN_ESLEME)].unique()
    if len(tanimsiz):
        raise ValueError(f"Eşlenemeyen adsorban adı: {list(tanimsiz)}")
    degisen = int((df["adsorban"] != anahtar.map(ADSORBAN_ESLEME)).sum())
    df["adsorban"] = anahtar.map(ADSORBAN_ESLEME)
    kaydet("Adsorban adı", "Yedi yazım iki ada indirildi",
           "'çay posası', 'ÇP', 'tea waste' aynı malzeme; üç öğrenci "
           "farklı yazmış. Eşleme tablosu betikte açık.", degisen)

    # --- 3. Fahrenheit girilmiş sıcaklıklar -----------------------------
    # Tasarımda yalnız 25 ve 45 °C var. 50'nin üstündeki her değer
    # Fahrenheit'tır: 77 °F = 25 °C, 113 °F = 45 °C.
    fahrenheit = df["sicaklik_C"] > 50
    df.loc[fahrenheit, "sicaklik_C"] = (
        (df.loc[fahrenheit, "sicaklik_C"] - 32) * 5 / 9).round(0)
    kaydet("Sıcaklık birimi", "Fahrenheit → Celsius çevrildi",
           "Tasarımda yalnız 25 ve 45 °C var; 50 °C üstü değerler "
           "birim karışıklığı. 77 °F = 25 °C, 113 °F = 45 °C.",
           int(fahrenheit.sum()))

    # --- 4. Olanaksız ölçümler ------------------------------------------
    # Adsorpsiyon derişimi düşürür. Denge derişimi başlangıçtan büyükse
    # ölçüm hatalıdır; düzeltilemez, bu yüzden düşer.
    olanaksiz = df["denge_derisim_mgL"] >= df["baslangic_derisim_mgL"]
    df = df[~olanaksiz].reset_index(drop=True)
    kaydet("Olanaksız ölçüm", "Satır çıkarıldı",
           "Denge derişimi başlangıçtan büyük ya da eşit. Adsorpsiyon "
           "derişimi düşürür; bu fiziksel olarak olanaksız.",
           int(olanaksiz.sum()))

    # --- 5. Şüpheli cihaz dönemi ----------------------------------------
    # 12-18 Mart'ta spektrofotometre lambası zayıfmış. Bu satırlar
    # ÇIKARILMIYOR, işaretleniyor: karar okura bırakılıyor.
    tarih = pd.to_datetime(df["tarih"])
    df["supheli_donem"] = tarih.between("2026-03-12", "2026-03-18")
    kaydet("Şüpheli dönem", "Çıkarılmadı, işaretlendi",
           "12-18 Mart arası cihaz bakım kaydı var. Satırlar "
           "'supheli_donem' sütunuyla etiketlendi; duyarlılık analizi "
           "bunları hariç tutarak yineleniyor.",
           int(df["supheli_donem"].sum()))

    # --- 6. Boş hücreler -------------------------------------------------
    # pH ve denge derişimi analizde zorunlu. Doldurmak uydurmak olur.
    bos = df[["pH", "denge_derisim_mgL"]].isna().any(axis=1)
    df = df[~bos].reset_index(drop=True)
    kaydet("Boş hücre", "Satır çıkarıldı",
           "pH ve denge derişimi analizin zorunlu girdileri. Ortalamayla "
           "doldurmak ölçülmeyen bir deneyi ölçülmüş göstermek olur.",
           int(bos.sum()))

    # --- 7. Türetilmiş değişkenler --------------------------------------
    # q: birim adsorban kütlesine tutunan boyar madde (mg/g)
    df["q_mgG"] = ((df["baslangic_derisim_mgL"] - df["denge_derisim_mgL"])
                   * HACIM_L / KUTLE_G).round(3)
    # Giderim verimi (%)
    df["giderim_yuzde"] = (
        (df["baslangic_derisim_mgL"] - df["denge_derisim_mgL"])
        / df["baslangic_derisim_mgL"] * 100).round(2)
    kaydet("Türetilmiş değişken", "q ve giderim verimi eklendi",
           "q = (C0 − Ce)·V/m, V = 0,05 L ve m = 0,1 g. Giderim verimi "
           "yüzde olarak. İkisi de ham sütunlardan hesaplanır, "
           "elle girilmez.", len(df))

    # --- 8. Eksik tekrar denetimi ---------------------------------------
    sayim = df.groupby(["adsorban", "baslangic_derisim_mgL", "pH",
                        "sicaklik_C", "temas_suresi_dk"],
                       observed=True).size()
    eksik = sayim[sayim < 3]
    kaydet("Tekrar sayısı", "Eksik koşullar bildirildi",
           f"Planda her koşul için 3 tekrar vardı. {len(eksik)} koşulda "
           "daha az tekrar kaldı; bu koşullar analizde daha az ağırlık "
           "taşıdığı için ANOVA dengesiz tasarım olarak kurulacak.",
           int(eksik.sum()))

    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    df.to_csv(hedef / "adsorpsiyon_temiz.csv", index=False,
              encoding="utf-8-sig")
    gunluk_df = pd.DataFrame(gunluk)
    gunluk_df.to_csv(hedef / "adsorpsiyon_karar_gunlugu.csv", index=False,
                     encoding="utf-8-sig")

    # --- Günlüğü okunur metin olarak da yaz -----------------------------
    satirlar = ["ADSORPSİYON VERİSİ — TEMİZLEME KARAR GÜNLÜĞÜ", "=" * 60, "",
                f"Ham satır sayısı   : {baslangic}",
                f"Temiz satır sayısı : {len(df)}",
                f"Çıkarılan          : {baslangic - len(df)} "
                f"(%{(baslangic - len(df)) / baslangic * 100:.1f})", ""]
    for i, g in enumerate(gunluk, 1):
        satirlar += [f"{i}. {g['adim']}",
                     f"   Karar   : {g['karar']}",
                     f"   Gerekçe : {g['gerekce']}",
                     f"   Etkilenen satır: {g['etkilenen_satir']}", ""]
    satirlar += ["Eksik tekrarlı koşullar:", ""]
    for anahtar_, n in eksik.items():
        satirlar.append(f"   {anahtar_} → {n} tekrar (planda 3)")
    (hedef / "adsorpsiyon_karar_gunlugu.txt").write_text(
        "\n".join(satirlar) + "\n", encoding="utf-8-sig")

    print("\n".join(satirlar))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
