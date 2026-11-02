# -*- coding: utf-8 -*-
"""
03 — Anket verisini temizle ve ölçek puanlarını hesapla

Bu betik kursun 6. bölümünde verilen istemin (prompt) çıktısıdır.
Her temizleme kararı, kararın gerekçesiyle birlikte bir günlüğe yazılır;
makalenin Yöntem bölümünde bu günlük doğrudan kaynak olarak kullanılır.

İlke: hiçbir satır sessizce silinmez. Silinen her şey sayılır, raporlanır.

Kullanım:
  python 03_anket_temizle.py <veri_klasörü> <çıktı_klasörü>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

OLCEK_ALT_UST = (1, 5)

# Serbest metinle gelen fakülte yazımlarını tek biçime indirgeme eşlemesi.
FAKULTE_ESLEME = {
    "mühendislik": "Mühendislik ve Mimarlık",
    "mühendislik ve mimarlık": "Mühendislik ve Mimarlık",
    "fen edebiyat": "Fen-Edebiyat",
    "fen-edebiyat": "Fen-Edebiyat",
    "tıp": "Tıp",
    "tıp fakültesi": "Tıp",
    "eğitim": "Eğitim",
    "eğitim fakültesi": "Eğitim",
    "iibf": "İktisadi ve İdari Bilimler",
    "İİBF": "İktisadi ve İdari Bilimler",
    "iktisadi ve idari bilimler": "İktisadi ve İdari Bilimler",
    "ilahiyat": "İlahiyat",
}

UNVAN_ESLEME = {
    "araştırma görevlisi": "Araştırma Görevlisi",
    "öğretim görevlisi": "Öğretim Görevlisi",
    "dr. öğr. üyesi": "Dr. Öğr. Üyesi",
    "dr. öğretim üyesi": "Dr. Öğr. Üyesi",
    "doçent": "Doçent",
    "doç. dr.": "Doçent",
    "profesör": "Profesör",
}


def tr_kucult(metin) -> str:
    """Türkçeye uygun küçültme: I→ı, İ→i ayrımını korur."""
    if pd.isna(metin):
        return ""
    return (str(metin).strip()
            .replace("I", "ı").replace("İ", "i")
            .lower())


def main(veri_klasoru: str, cikti_klasoru: str) -> None:
    kaynak = pathlib.Path(veri_klasoru)
    ham = pd.read_csv(kaynak / "anket_ham.csv", encoding="utf-8-sig")
    sozluk = pd.read_csv(kaynak / "anket_madde_sozlugu.csv",
                         encoding="utf-8-sig")

    gunluk = []
    baslangic = len(ham)

    def kaydet(adim, karar, etkilenen, gerekce):
        gunluk.append({"adım": adim, "karar": karar,
                       "etkilenen": etkilenen, "gerekçe": gerekce})

    # ------------------------------------------------- 1) mükerrer satırlar
    mukerrer_sayisi = int(ham.duplicated().sum())
    ham = ham.drop_duplicates().reset_index(drop=True)
    kaydet("Mükerrer kayıt", "Tamamen aynı satırların ikinci kopyası silindi",
           mukerrer_sayisi,
           "Aynı katılımcının formu iki kez göndermesi; aynı kişi iki kez "
           "sayılırsa standart hata olduğundan küçük tahmin edilir.")

    # --------------------------------------- 2) kategori yazımını tek biçime
    fak_onces = ham["fakulte"].nunique()
    ham["fakulte"] = ham["fakulte"].map(
        lambda x: FAKULTE_ESLEME.get(tr_kucult(x), str(x).strip()))
    unv_onces = ham["unvan"].nunique()
    ham["unvan"] = ham["unvan"].map(
        lambda x: UNVAN_ESLEME.get(tr_kucult(x), str(x).strip()))
    kaydet("Kategori birleştirme",
           f"fakülte {fak_onces} → {ham['fakulte'].nunique()} düzey, "
           f"unvan {unv_onces} → {ham['unvan'].nunique()} düzey",
           fak_onces - ham["fakulte"].nunique()
           + unv_onces - ham["unvan"].nunique(),
           "Form serbest metin kabul ettiği için aynı fakülte farklı "
           "yazımlarla girilmiş; birleştirilmezse grup karşılaştırmaları "
           "sahte düzeylerle çalışır.")

    # ------------------------------------------- 3) aralık dışı değerler
    madde_kodlari = sozluk["madde"].tolist()
    alt, ust = OLCEK_ALT_UST
    aralik_disi = 0
    for kod in madde_kodlari:
        ham[kod] = pd.to_numeric(ham[kod], errors="coerce")
        disi = ham[kod].notna() & (~ham[kod].between(alt, ust))
        aralik_disi += int(disi.sum())
        ham.loc[disi, kod] = np.nan
    kaydet("Ölçek dışı Likert değeri",
           f"{alt}–{ust} aralığı dışındaki hücreler eksik işaretlendi",
           aralik_disi,
           "Ölçek 5 basamaklı; 7 gibi bir değer veri girişi hatasıdır, "
           "ortalamaya katılırsa ölçek puanını yukarı çeker.")

    for sutun, (a, u) in {"yas": (22, 75), "haftalik_saat": (0, 60),
                          "akademik_yil": (0, 45)}.items():
        ham[sutun] = pd.to_numeric(ham[sutun], errors="coerce")
        disi = ham[sutun].notna() & (~ham[sutun].between(a, u))
        if int(disi.sum()):
            kaydet(f"Aralık dışı: {sutun}",
                   f"{a}–{u} dışındaki değerler eksik işaretlendi",
                   int(disi.sum()),
                   "Olanaksız değer (örn. 3 yaş, haftada 168 saat) "
                   "ölçüm değil giriş hatasıdır.")
            ham.loc[disi, sutun] = np.nan

    # ----------------------------------------------- 4) ters kodlu maddeler
    ters_maddeler = sozluk.loc[sozluk["ters_kodlu"] == "evet", "madde"].tolist()
    for kod in ters_maddeler:
        ham[kod] = (alt + ust) - ham[kod]
    kaydet("Ters kodlama", f"{', '.join(ters_maddeler)} düz kodlandı "
           f"(yeni = {alt + ust} − eski)", len(ters_maddeler),
           "Olumsuz yazılmış maddeler çevrilmezse ölçek içi tutarlılık "
           "(Cronbach α) yapay olarak düşer ve faktör yükü ters çıkar.")

    # ---------------------------- 5) madde bazında eksik veri — liste bazlı mı?
    eksik_oran = ham[madde_kodlari].isna().mean(axis=1)
    cok_eksik = eksik_oran > 0.20
    kaydet("Katılımcı bazında eksik",
           "Likert maddelerinin %20'sinden fazlasını boş bırakan katılımcı "
           "çıkarıldı", int(cok_eksik.sum()),
           "Çok sayıda madde eksikse ölçek puanı güvenilir biçimde "
           "hesaplanamaz; eşik Bennett (2001) ölçütüne dayanır.")
    ham = ham.loc[~cok_eksik].reset_index(drop=True)

    # Kalan eksikler madde ortalamasıyla değil, katılımcının kendi
    # ölçek ortalamasıyla doldurulur: kişinin yanıt üslubunu korur.
    doldurulan = 0
    for olcek in sozluk["olcek"].unique():
        kodlar = sozluk.loc[sozluk["olcek"] == olcek, "madde"].tolist()
        kisi_ort = ham[kodlar].mean(axis=1)
        for kod in kodlar:
            bos = ham[kod].isna()
            doldurulan += int(bos.sum())
            ham.loc[bos, kod] = kisi_ort[bos]
    kaydet("Madde içi eksik",
           "Kalan eksik hücreler katılımcının o ölçekteki kendi ortalamasıyla "
           "dolduruldu", doldurulan,
           "Madde ortalaması yerine kişi ortalaması kullanılması, yanıt "
           "üslubu farklarını (yüksek/düşük puanlama eğilimi) korur.")

    # ----------------------------------------------- 6) ölçek puanları
    for olcek in ["AF", "KK", "EK", "KN"]:
        kodlar = sozluk.loc[sozluk["olcek"] == olcek, "madde"].tolist()
        ham[f"{olcek}_puan"] = ham[kodlar].mean(axis=1).round(4)

    # Türetilmiş değişkenler
    ham["yogun_kullanici"] = (
        ham["haftalik_saat"] >= ham["haftalik_saat"].median()).astype(int)
    kaydet("Türetilmiş değişken",
           "yogun_kullanici = haftalık saat ≥ ortanca (%.1f saat)"
           % ham["haftalik_saat"].median(), 1,
           "Ortanca bölme, lojistik regresyon ve ki-kare örnekleri için "
           "ikili bir sonuç değişkeni sağlar; eşik veriden okunur, "
           "dışarıdan dayatılmaz.")

    # -------------------------------------------------------------- yazım
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    ham.to_csv(hedef / "anket_temiz.csv", index=False, encoding="utf-8-sig")

    rapor = {
        "başlangıç_satır": baslangic,
        "bitiş_satır": len(ham),
        "silinen_satır": baslangic - len(ham),
        "kalan_eksik_hücre": int(ham.isna().sum().sum()),
        "günlük": gunluk,
    }
    (hedef / "temizleme_gunlugu.json").write_text(
        json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Temiz dosya: {hedef / 'anket_temiz.csv'}")
    print(f"  {baslangic} satır → {len(ham)} satır "
          f"({baslangic - len(ham)} satır çıkarıldı)")
    print(f"  kalan eksik hücre: {int(ham.isna().sum().sum())}")
    print("\nTEMİZLEME GÜNLÜĞÜ")
    print("-" * 72)
    for k in gunluk:
        print(f"• {k['adım']}  [etkilenen: {k['etkilenen']}]")
        print(f"  karar  : {k['karar']}")
        print(f"  gerekçe: {k['gerekçe']}")
    print("-" * 72)
    for olcek in ["AF", "KK", "EK", "KN"]:
        s = ham[f"{olcek}_puan"]
        print(f"{olcek}_puan  ort={s.mean():.3f}  ss={s.std():.3f}  "
              f"min={s.min():.2f}  maks={s.max():.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
