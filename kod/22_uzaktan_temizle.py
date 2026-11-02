# -*- coding: utf-8 -*-
"""
22 — Uzaktan çalışma anketi: veri temizleme

Temizlik, veriden satır atmak değildir; her atılan satırın GEREKÇESİNİ
yazmaktır. Bu betik iki şey üretir: temizlenmiş veri dosyası ve hangi
satırın neden düştüğünü satır satır gösteren bir günlük. Hakem
"kaç anketi neden elediniz" diye sorduğunda cevabı günlük verir.

Uygulanan ölçütler ve sırası:

  1  Mükerrer kayıt           aynı katılımcı numarası iki kez
  2  Dikkat kontrolü          DK1 ≠ 2
  3  Aşırı hızlı doldurma     madde başına < 2 saniye
  4  Düz çizgi yanıtlama      21 maddenin standart sapması = 0
  5  Aralık dışı değer        Likert maddesi 1–5 dışında, yaş 18–70 dışında
  6  Aşırı eksik              21 maddenin %10'undan fazlası boş
  7  Kategori yazımı          büyük/küçük harf ve boşluk tekilleştirmesi
  8  Ters kodlama             T ile biten maddeler 6 − x ile çevrilir
  9  Kalan eksik hücre        ölçek içi ortalamayla doldurulur (madde başına
                              en çok %2 eksik olduğu için güvenli)

Sıra önemlidir: önce satır elenir, sonra kalan satırlarda düzeltme
yapılır. Tersi yapılırsa atılacak satırlar için boşuna hesap yapılır ve
ölçek ortalamaları dikkatsiz yanıtlarla kirlenir.

Kullanım:
  python 22_uzaktan_temizle.py <veri_klasörü>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

# Türkçe harf katlama. Python'un .lower() metodu "İ" harfini
# "i" + birleşen nokta (U+0307) olarak küçültür; sonuç görünürde "i"dir
# ama karakter dizisi farklıdır ve sözlükte karşılığı bulunamaz. Bu
# yüzden "LİSANS" düzeltilmeden geçip betimsel tabloda ayrı bir kategori
# olarak görünür. Aynı biçimde "I" harfi "ı" değil "i" olur.
# Katlama, eşleştirmeden ÖNCE bu iki harfi elle çevirir.
TR_KUCUK = str.maketrans({"İ": "i", "I": "ı"})


def tr_kucult(metin) -> str:
    return str(metin).translate(TR_KUCUK).lower().strip()


OLCEKLER = {
    "UCE": ["UCE1", "UCE2", "UCE3", "UCE4", "UCE5T"],
    "IYD": ["IYD1", "IYD2", "IYD3", "IYD4T", "IYD5"],
    "OB":  ["OB1", "OB2", "OB3", "OB4", "OB5T", "OB6"],
    "CV":  ["CV1", "CV2", "CV3", "CV4", "CV5"],
}
MADDELER = [m for liste in OLCEKLER.values() for m in liste]
TERS = [m for m in MADDELER if m.endswith("T")]


def main(klasor: str) -> None:
    kok = pathlib.Path(klasor)
    df = pd.read_csv(kok / "uzaktan_ham.csv", encoding="utf-8-sig")
    baslangic = len(df)
    gunluk = {"baslangic_satir": baslangic, "adimlar": [], "elenen": []}

    def ele(maske, gerekce):
        nonlocal df
        dusen = df.index[maske]
        for i in dusen:
            gunluk["elenen"].append(
                {"katilimci_no": int(df.at[i, "katilimci_no"]),
                 "gerekce": gerekce})
        df = df.drop(index=dusen)
        gunluk["adimlar"].append({"olcut": gerekce, "elenen": int(len(dusen)),
                                  "kalan": int(len(df))})
        print(f"  {gerekce:38s} −{len(dusen):>4d}   kalan {len(df)}")

    print(f"Başlangıç: {baslangic} satır")

    # 1 — mükerrer kayıt: ilk gönderim tutulur
    ele(df.duplicated(subset=["katilimci_no"], keep="first"),
        "Mükerrer kayıt")

    # 2 — dikkat kontrolü
    ele(df["DK1"] != 2, "Dikkat kontrolünü geçemeyen")

    # 3 — aşırı hızlı doldurma (21 madde × 2 sn = 42 sn alt sınır,
    #     demografikle birlikte 120 saniyenin altı gerçekçi değil)
    ele(df["doldurma_sn"] < 120, "Aşırı hızlı doldurma (<120 sn)")

    # 4 — düz çizgi: maddeler arası standart sapma sıfır
    sapma = df[MADDELER].apply(pd.to_numeric, errors="coerce").std(axis=1)
    ele(sapma.fillna(1) == 0, "Düz çizgi yanıtlama")

    # 5 — aralık dışı
    sayisal = df[MADDELER].apply(pd.to_numeric, errors="coerce")
    aralik_disi = ((sayisal < 1) | (sayisal > 5)).any(axis=1)
    ele(aralik_disi, "Likert maddesinde aralık dışı değer")
    yas = pd.to_numeric(df["yas"], errors="coerce")
    ele((yas < 18) | (yas > 70), "Yaşta aralık dışı değer")

    # 6 — aşırı eksik
    eksik_oran = df[MADDELER].isna().mean(axis=1)
    ele(eksik_oran > 0.10, "Maddelerin %10'undan fazlası boş")

    # 7 — kategori yazımı tekilleştirme
    duzeltme = {
        "cinsiyet": {"kadin": "Kadın", "kadın": "Kadın", "erkek": "Erkek",
                     "belirtmek istemiyorum": "Belirtmek istemiyorum"},
        "egitim": {"on lisans": "Ön lisans", "ön lisans": "Ön lisans",
                   "lisans": "Lisans", "y. lisans": "Yüksek lisans",
                   "yuksek lisans": "Yüksek lisans",
                   "yüksek lisans": "Yüksek lisans", "doktora": "Doktora"},
        "sektor": {"yazılım": "Yazılım ve bilişim",
                   "bilişim": "Yazılım ve bilişim",
                   "yazılım ve bilişim": "Yazılım ve bilişim",
                   "finans ve sigortacılık": "Finans ve sigortacılık",
                   "danışmanlık": "Danışmanlık",
                   "telekomünikasyon": "Telekomünikasyon"},
    }
    duzeltilen = 0
    for sutun, harita in duzeltme.items():
        once = df[sutun].copy()
        df[sutun] = (df[sutun].map(tr_kucult)
                     .map(harita).fillna(df[sutun]))
        duzeltilen += int((once.astype(str) != df[sutun].astype(str)).sum())
    gunluk["adimlar"].append({"olcut": "Kategori yazımı tekilleştirildi",
                              "duzeltilen_hucre": duzeltilen,
                              "kalan": int(len(df))})
    print(f"  {'Kategori yazımı tekilleştirildi':38s}  {duzeltilen} hücre")

    # 8 — ters kodlama
    for m in TERS:
        df[m] = 6 - pd.to_numeric(df[m], errors="coerce")
    gunluk["adimlar"].append({"olcut": "Ters kodlu maddeler çevrildi",
                              "madde": TERS, "kalan": int(len(df))})
    print(f"  {'Ters kodlu madde çevrildi':38s}  {len(TERS)} madde")

    # 9 — kalan eksik hücreler: ölçek içi kişi ortalaması
    #     Bu, madde ortalamasıyla doldurmaktan iyidir: kişinin o ölçekteki
    #     genel düzeyini korur, örneklem ortalamasına çekmez.
    dolduruldu = 0
    for olcek, maddeler in OLCEKLER.items():
        sayisal = df[maddeler].apply(pd.to_numeric, errors="coerce")
        kisi_ort = sayisal.mean(axis=1)
        for m in maddeler:
            bos = sayisal[m].isna()
            dolduruldu += int(bos.sum())
            sayisal.loc[bos, m] = kisi_ort[bos]
        df[maddeler] = sayisal
    gunluk["adimlar"].append({"olcut": "Eksik hücre kişi ortalamasıyla "
                                       "dolduruldu",
                              "doldurulan_hucre": dolduruldu,
                              "kalan": int(len(df))})
    print(f"  {'Eksik hücre dolduruldu':38s}  {dolduruldu} hücre")

    # Demografik eksikler doldurulmaz, "Belirtilmemiş" olarak işaretlenir:
    # kategorik bir değeri uydurmak, betimsel tabloyu yanıltır.
    for sutun in ("egitim",):
        df[sutun] = df[sutun].fillna("Belirtilmemiş")
    df["kidem_yil"] = pd.to_numeric(df["kidem_yil"], errors="coerce")
    df["haftalik_uzaktan_gun"] = pd.to_numeric(
        df["haftalik_uzaktan_gun"], errors="coerce")

    # ----------------------------------------------------- ölçek skorları
    for olcek, maddeler in OLCEKLER.items():
        df[f"{olcek}_ort"] = df[maddeler].mean(axis=1).round(4)

    # --------------------------------------------- ikincil veriyi birleştir
    ik = pd.read_csv(kok / "uzaktan_ik_kayitlari.csv", encoding="utf-8-sig")
    df = df.merge(ik.drop(columns=["kurum_kod"]), on="katilimci_no",
                  how="left")
    eslesen = int(df["yillik_performans_puani"].notna().sum())
    gunluk["adimlar"].append({"olcut": "İK kaydı eşleştirildi",
                              "eslesen": eslesen, "kalan": int(len(df))})
    print(f"  {'İK kaydı eşleşen':38s}  {eslesen} satır")

    gunluk["bitis_satir"] = int(len(df))
    gunluk["elenen_toplam"] = baslangic - int(len(df))
    gunluk["elenme_orani"] = round(gunluk["elenen_toplam"] / baslangic, 4)

    df.to_csv(kok / "uzaktan_temiz.csv", index=False, encoding="utf-8-sig")
    (kok / "uzaktan_temizleme_gunlugu.json").write_text(
        json.dumps(gunluk, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nTemiz veri : {len(df)} satır  "
          f"(elenme oranı %{gunluk['elenme_orani'] * 100:.1f})")
    print(f"Günlük     : {kok / 'uzaktan_temizleme_gunlugu.json'}")


if __name__ == "__main__":
    main(sys.argv[1])
