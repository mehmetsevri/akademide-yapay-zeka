# -*- coding: utf-8 -*-
"""
13 — Kimya örneği: adsorpsiyon deney verisi üretimi

!!! BU VERİ SETİ SENTETİKTİR. !!!
Gerçek bir laboratuvar çalışmasından gelmemiştir; yöntem öğretmek
için üretilmiştir. İçindeki hiçbir sayı bir bulgu olarak
alıntılanamaz.

Neden sentetik: laboratuvar defterinden yeni aktarılmış, HENÜZ
TEMİZLENMEMİŞ bir deney verisi kamuya açık olarak bulunmaz. Yayımlanan
veri setleri zaten temizlenmiştir; oysa öğretilecek şey tam olarak
temizleme adımıdır.

Üretim modeli: Langmuir izotermi. Denge derişimi, kütle dengesi ile
izotermin kesiştiği noktadan sayısal olarak çözülür.

    q = (C0 − Ce) · V / m          kütle dengesi
    q = qmax · KL · Ce / (1 + KL · Ce)   Langmuir

V = 0,05 L ve m = 0,1 g bütün deneylerde sabittir.

Tam faktöriyel tasarım:
  2 adsorban × 3 derişim × 3 pH × 2 sıcaklık × 2 temas süresi
  × 3 tekrar = 216 deney

Çıktı, laboratuvar defterinden yeni aktarılmış hâliyle yazılır:
yazım tutarsızlıkları, Fahrenheit girilmiş sıcaklıklar, olanaksız
ölçümler ve bir cihaz arızası dönemi içerir.

Kullanım:
  python 13_adsorpsiyon_veri_uret.py <çıktı_klasörü>
"""
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy.optimize import brentq

TOHUM = 20261103
HACIM_L = 0.05          # çözelti hacmi
KUTLE_G = 0.10          # adsorban kütlesi

rng = np.random.default_rng(TOHUM)

# Adsorban başına en yüksek adsorpsiyon kapasitesi (mg/g)
QMAX = {"cay_posasi": 148.0, "ticari": 176.0}

# pH'ın Langmuir sabiti üzerindeki etkisi. Katyonik boyar madde,
# yüzey negatif yüklendiğinde daha iyi tutunur; bu da yüksek pH'ta
# olur. pH 3'te yüzey protonlanır ve tutunma düşer.
PH_ETKISI = {3: 0.45, 7: 1.00, 10: 1.18}

# Sıcaklık etkisi: adsorpsiyon burada endotermik kabul edildi
SICAKLIK_ETKISI = {25: 1.00, 45: 1.22}

# Temas süresi: 60 dakikada denge henüz tam kurulmamış
SURE_ETKISI = {60: 0.88, 120: 1.00}

KL_TEMEL = {"cay_posasi": 0.055, "ticari": 0.082}


def denge_derisimi(c0, qmax, kl):
    """Kütle dengesi ile Langmuir izoterminin kesişimini çözer.

    İki denklem de q'yu verir; farkları sıfır olan Ce aranır.
    Kök, 0 ile C0 arasında tektir çünkü sol taraf azalan, sağ taraf
    artan bir fonksiyondur.
    """
    def fark(ce):
        return (c0 - ce) * HACIM_L / KUTLE_G - qmax * kl * ce / (1 + kl * ce)
    return brentq(fark, 1e-9, c0 - 1e-9)


def main(cikti_klasoru: str) -> None:
    satirlar = []
    deney_no = 1
    # Deneyler üç ay boyunca rastgele sırayla yürütüldü
    # rng.choice bir DatetimeIndex'ten numpy.datetime64 döndürür; onun
    # strftime'ı yoktur. Bu yüzden tarihleri baştan metne çeviriyoruz.
    tarihler = pd.date_range("2026-02-02", "2026-04-24", freq="D").strftime(
        "%Y-%m-%d").to_numpy()

    for adsorban in ("cay_posasi", "ticari"):
        for c0 in (25.0, 50.0, 100.0):
            for ph in (3, 7, 10):
                for sicaklik in (25, 45):
                    for sure in (60, 120):
                        kl = (KL_TEMEL[adsorban] * PH_ETKISI[ph]
                              * SICAKLIK_ETKISI[sicaklik] * SURE_ETKISI[sure])
                        qmax = QMAX[adsorban] * SURE_ETKISI[sure]
                        ce_kuramsal = denge_derisimi(c0, qmax, kl)
                        for tekrar in (1, 2, 3):
                            # Ölçüm hatası: spektrofotometre okuması
                            ce = ce_kuramsal * (1 + rng.normal(0, 0.035))
                            ce = float(np.clip(ce, 0.05, c0 * 0.99))
                            satirlar.append({
                                "deney_no": deney_no,
                                "tarih": str(rng.choice(tarihler)),
                                "adsorban": adsorban,
                                "baslangic_derisim_mgL": c0,
                                "pH": ph,
                                "sicaklik_C": float(sicaklik),
                                "temas_suresi_dk": sure,
                                "denge_derisim_mgL": round(ce, 3),
                                "tekrar_no": tekrar,
                            })
                            deney_no += 1

    df = pd.DataFrame(satirlar).astype(object)
    print(f"Temiz hâl: {len(df)} satır")

    # ------------------------------------------- laboratuvar defteri kirleri
    # 1) Adsorban adı üç öğrenci tarafından farklı yazılmış
    yazim = {"cay_posasi": ["çay posası", "cay posasi", "ÇP", "tea waste"],
             "ticari": ["Ticari", "ticari AK", "commercial"]}
    for i in rng.choice(len(df), 38, replace=False):
        df.at[i, "adsorban"] = rng.choice(yazim[df.at[i, "adsorban"]])

    # 2) Bazı sıcaklıklar Fahrenheit girilmiş (25 °C = 77 °F, 45 °C = 113 °F)
    fahrenheit = rng.choice(len(df), 14, replace=False)
    for i in fahrenheit:
        df.at[i, "sicaklik_C"] = round(df.at[i, "sicaklik_C"] * 9 / 5 + 32, 1)

    # 3) Olanaksız ölçüm: denge derişimi başlangıçtan büyük.
    #    Adsorpsiyon derişimi düşürür; bu satırlar ölçüm hatasıdır.
    for i in rng.choice(len(df), 5, replace=False):
        df.at[i, "denge_derisim_mgL"] = round(
            df.at[i, "baslangic_derisim_mgL"] * rng.uniform(1.02, 1.15), 3)

    # 4) Cihaz arızası dönemi: 12–18 Mart ölçümleri şüpheli.
    #    Spektrofotometre lambası zayıflamış, okumalar kaymış.
    ariza = pd.to_datetime(df["tarih"]).between("2026-03-12", "2026-03-18")
    for i in df.index[ariza]:
        df.at[i, "denge_derisim_mgL"] = round(
            float(df.at[i, "denge_derisim_mgL"]) * rng.uniform(1.18, 1.35), 3)

    # 5) Üç koşulda üçüncü tekrar başarısız olmuş, satır hiç girilmemiş
    ucuncu = df.index[(df["tekrar_no"] == 3)]
    dusen = rng.choice(ucuncu, 3, replace=False)
    df = df.drop(index=dusen)

    # 6) İki satır iki kez girilmiş
    df = pd.concat([df, df.iloc[[40, 150]]], ignore_index=True)

    # 7) Birkaç hücre boş kalmış
    for sutun, adet in (("pH", 4), ("denge_derisim_mgL", 3)):
        for i in rng.choice(len(df), adet, replace=False):
            df.at[i, sutun] = np.nan

    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    df.to_csv(hedef / "adsorpsiyon_ham.csv", index=False, encoding="utf-8-sig")

    # Deney planı: ne yapılması gerektiği
    plan = (df.assign(ads="x")[["baslangic_derisim_mgL"]]
            .drop_duplicates())
    plan_satirlari = [
        {"adsorban": a, "baslangic_derisim_mgL": c, "pH": p,
         "sicaklik_C": s, "temas_suresi_dk": t, "planlanan_tekrar": 3}
        for a in ("cay_posasi", "ticari") for c in (25.0, 50.0, 100.0)
        for p in (3, 7, 10) for s in (25.0, 45.0) for t in (60, 120)]
    pd.DataFrame(plan_satirlari).to_csv(
        hedef / "deney_plani.csv", index=False, encoding="utf-8-sig")

    print(f"Ham dosya  : {hedef / 'adsorpsiyon_ham.csv'}  ({len(df)} satır)")
    print(f"Deney planı: {hedef / 'deney_plani.csv'}  "
          f"({len(plan_satirlari)} koşul)")
    print(f"  yazım tutarsızlığı : 38 satır")
    print(f"  Fahrenheit girilmiş: 14 satır")
    print(f"  olanaksız ölçüm    : 5 satır")
    print(f"  şüpheli dönem      : {int(ariza.sum())} satır")
    print(f"  eksik tekrar       : 3 koşul")
    print(f"  mükerrer satır     : 2")
    print(f"  boş hücre          : {int(df.isna().sum().sum())}")


if __name__ == "__main__":
    main(sys.argv[1])
