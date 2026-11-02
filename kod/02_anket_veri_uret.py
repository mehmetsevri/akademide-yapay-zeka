# -*- coding: utf-8 -*-
"""
02 — Sosyal bilimler örneği: anket veri seti üretimi

!!! BU VERİ SETİ SENTETİKTİR. !!!
Gerçek bir anket uygulamasından gelmemiştir; yöntem öğretmek için
üretilmiştir. İçindeki hiçbir sayı bir araştırma bulgusu olarak
alıntılanamaz.

Neden sentetik: Türkçe açık uçlu yanıt içeren, kişisel veri barındırmayan
ve açık lisansla dağıtılabilen bir akademisyen anketi mikro verisi kamuya
açık değildir. Öğretim için gereken şey, öğretilen her testin anlamlı bir
sonuç üretmesidir; bu da veri üretim modelinin bilinmesini gerektirir.

Üretim modeli: dört örtük (latent) değişken üzerine kurulu bir faktör
yapısı. Maddeler sürekli örtük skordan üretilir, sonra eşik değerlerle
1–5 Likert ölçeğine döndürülür.

  eta_AF  Algılanan Fayda
  eta_KK  Algılanan Kullanım Kolaylığı
  eta_EK  Etik Kaygı
  eta_KN  Kullanım Niyeti  =  f(AF, KK, EK)

Çıktı:
  anket_ham.csv              gerçek bir form çıktısının hâli — eksik
                             hücreler, tutarsız kategori yazımları, boşluk
                             kirleri, mükerrer satır, aralığa sığmayan değer
  anket_madde_sozlugu.csv    hangi madde hangi ölçekte, hangisi ters kodlu

Temiz dosya ayrı bir betikle (03_anket_temizle.py) üretilir.

Kullanım:
  python 02_anket_veri_uret.py <çıktı_klasörü>
"""
import sys
import pathlib
import numpy as np
import pandas as pd

TOHUM = 20261103
N = 312

rng = np.random.default_rng(TOHUM)

# ---------------------------------------------------------------- maddeler
# (kod, metin, örtük değişken, faktör yükü, eşik kayması, ters kodlu mu)
MADDELER = [
    ("AF1",  "Üretken yapay zekâ araçları literatür taramamı hızlandırıyor.",             "AF", 0.78,  0.35, False),
    ("AF2",  "Bu araçlar makale yazım sürecimde zaman kazandırıyor.",                      "AF", 0.82,  0.30, False),
    ("AF3",  "Yabancı dilde yazarken bu araçlar metnimin niteliğini artırıyor.",           "AF", 0.71,  0.45, False),
    ("AF4",  "Veri analizi adımlarında bu araçlardan yararlanıyorum.",                     "AF", 0.64, -0.20, False),
    ("AF5",  "Bu araçlar araştırma verimliliğimi yükseltiyor.",                            "AF", 0.80,  0.25, False),
    ("AF6T", "Bu araçların araştırma sürecime somut bir katkısı yok.",                     "AF", 0.66,  0.10, True),

    ("KK1",  "Bu araçları kullanmayı öğrenmek benim için kolay oldu.",                     "KK", 0.76,  0.30, False),
    ("KK2",  "İstediğim çıktıyı almak için nasıl soru yazacağımı biliyorum.",              "KK", 0.74, -0.10, False),
    ("KK3",  "Araçların arayüzlerinde rahatça yol alabiliyorum.",                          "KK", 0.70,  0.20, False),
    ("KK4T", "Bu araçları kullanmak bana karmaşık geliyor.",                               "KK", 0.68,  0.05, True),
    ("KK5",  "Bir sorunla karşılaştığımda çözümü kendim bulabiliyorum.",                   "KK", 0.61, -0.05, False),

    ("EK1",  "Bu araçların kullanımı bilimsel özgünlüğü zedeliyor.",                       "EK", 0.69,  0.00, False),
    ("EK2",  "Araçların ürettiği metinlerde intihal riski bulunuyor.",                     "EK", 0.73,  0.35, False),
    ("EK3",  "Araçlara veri verirken gizlilik ihlali olmasından kaygılanıyorum.",          "EK", 0.67,  0.40, False),
    ("EK4",  "Araçların uydurduğu kaynaklar literatürü kirletiyor.",                       "EK", 0.75,  0.55, False),
    ("EK5",  "Kurumsal kuralların belirsizliği bu araçları kullanırken beni tedirgin ediyor.", "EK", 0.72, 0.60, False),
    ("EK6",  "Öğrencilerin bu araçları denetimsiz kullanması akademik dürüstlüğü tehdit ediyor.", "EK", 0.70, 0.70, False),

    ("KN1",  "Önümüzdeki dönemde bu araçları araştırmalarımda kullanmayı sürdüreceğim.",    "KN", 0.81,  0.50, False),
    ("KN2",  "Bu araçları meslektaşlarıma öneririm.",                                       "KN", 0.79,  0.25, False),
    ("KN3",  "Yeni çıkan yapay zekâ araçlarını denemeye istekliyim.",                       "KN", 0.72,  0.15, False),
    ("KN4",  "Bu araçları araştırma rutinimin kalıcı bir parçası yapmayı planlıyorum.",      "KN", 0.77, -0.05, False),
]

FAKULTELER = ["Mühendislik ve Mimarlık", "Fen-Edebiyat", "Tıp",
              "Eğitim", "İktisadi ve İdari Bilimler", "İlahiyat"]
FAKULTE_AGIRLIK = [0.26, 0.18, 0.17, 0.16, 0.14, 0.09]

UNVANLAR = ["Araştırma Görevlisi", "Öğretim Görevlisi", "Dr. Öğr. Üyesi",
            "Doçent", "Profesör"]
UNVAN_AGIRLIK = [0.24, 0.12, 0.33, 0.19, 0.12]


def likert_dondur(surekli: np.ndarray, kayma: float) -> np.ndarray:
    """Sürekli örtük skoru 1–5 Likert kategorisine çevirir.

    Eşikler standart normal nicelikleridir; `kayma` eşikleri topluca
    öteleyerek madde ortalamasını aşağı/yukarı taşır. Böylece her madde
    aynı örtük değişkenden gelse de farklı ortalamaya sahip olur —
    gerçek ölçeklerde olduğu gibi.
    """
    esikler = np.array([-1.25, -0.45, 0.35, 1.15]) - kayma
    return np.searchsorted(esikler, surekli) + 1


def main(cikti_klasoru: str) -> None:
    # ----------------------------------------------------------- demografi
    fakulte = rng.choice(FAKULTELER, size=N, p=FAKULTE_AGIRLIK)
    unvan = rng.choice(UNVANLAR, size=N, p=UNVAN_AGIRLIK)
    unvan_sira = pd.Series(unvan).map(
        {u: i for i, u in enumerate(UNVANLAR)}).to_numpy()

    cinsiyet = rng.choice(["Kadın", "Erkek", "Belirtmek istemiyorum"],
                          size=N, p=[0.44, 0.53, 0.03])

    # Akademik yıl unvanla birlikte artar; yaş da akademik yıla bağlıdır.
    akademik_yil = np.clip(
        np.round(2.5 + 5.2 * unvan_sira + rng.normal(0, 2.6, N)), 1, 38
    ).astype(int)
    yas = np.clip(np.round(27 + 0.95 * akademik_yil + rng.normal(0, 2.4, N)),
                  24, 67).astype(int)

    egitim_aldi = rng.binomial(
        1, 1 / (1 + np.exp(-(-0.55 - 0.10 * unvan_sira + rng.normal(0, 0.5, N))))
    )

    # ------------------------------------------------- örtük değişkenler
    # Algılanan Fayda: eğitim alanlarda ve görece genç unvanlarda yüksek
    eta_AF = (0.52 * egitim_aldi
              - 0.11 * unvan_sira
              + rng.normal(0, 0.85, N))

    # Kullanım Kolaylığı: AF ile ilişkili, eğitimle güçlü ilişkili
    eta_KK = (0.46 * eta_AF
              + 0.60 * egitim_aldi
              - 0.09 * unvan_sira
              + rng.normal(0, 0.72, N))

    # Etik Kaygı: AF ile ters yönlü; kıdemle ve bazı fakültelerde yüksek
    fak_kaygi = pd.Series(fakulte).map({
        "Tıp": 0.34, "İlahiyat": 0.40, "Eğitim": 0.12,
        "Fen-Edebiyat": 0.00, "İktisadi ve İdari Bilimler": -0.06,
        "Mühendislik ve Mimarlık": -0.22,
    }).to_numpy()
    eta_EK = (-0.26 * eta_AF
              + 0.13 * unvan_sira
              + fak_kaygi
              + rng.normal(0, 0.80, N))

    # Kullanım Niyeti: üçünün bileşimi — regresyon dersinin hedefi
    eta_KN = (0.47 * eta_AF
              + 0.27 * eta_KK
              - 0.21 * eta_EK
              + rng.normal(0, 0.62, N))

    etalar = {"AF": eta_AF, "KK": eta_KK, "EK": eta_EK, "KN": eta_KN}
    for ad, v in etalar.items():                       # standardize et
        etalar[ad] = (v - v.mean()) / v.std()

    # ---------------------------------------------------------- maddeler
    veri = {}
    for kod, _metin, latent, yuk, kayma, ters in MADDELER:
        artik = np.sqrt(max(1 - yuk ** 2, 0.05))
        surekli = yuk * etalar[latent] + artik * rng.normal(0, 1, N)
        if ters:
            surekli = -surekli
        veri[kod] = likert_dondur(surekli, kayma if not ters else -kayma)

    # ------------------------------------------------- davranışsal ölçüler
    # Haftalık kullanım saati: sağı uzun kuyruklu (log-normal) — parametrik
    # testlerin varsayımlarının neden denetlenmesi gerektiğini gösterir.
    haftalik_saat = np.round(
        np.exp(0.72 + 0.62 * etalar["KN"] + 0.30 * egitim_aldi
               + rng.normal(0, 0.70, N)), 1)
    haftalik_saat = np.clip(haftalik_saat, 0.0, 40.0)

    arac_sayisi = np.clip(
        rng.poisson(np.exp(0.42 + 0.40 * etalar["KK"] + 0.25 * egitim_aldi)),
        0, 7)

    yayin_3yil = np.clip(
        rng.poisson(np.exp(0.78 + 0.040 * akademik_yil + 0.22 * etalar["AF"])),
        0, 24)

    cerceve = pd.DataFrame({
        "katilimci_no": [f"K{i:03d}" for i in range(1, N + 1)],
        "fakulte": fakulte,
        "unvan": unvan,
        "cinsiyet": cinsiyet,
        "yas": yas,
        "akademik_yil": akademik_yil,
        "yayin_3yil": yayin_3yil,
        "egitim_aldi": egitim_aldi,
        "haftalik_saat": haftalik_saat,
        "arac_sayisi": arac_sayisi,
        **veri,
    })

    # ---------------------------------------------- "ham" dosyayı kirlet
    ham = cerceve.copy().astype(object)

    # 1) Eksik hücreler: Likert maddelerinde rastgele ~%1,8
    madde_kodlari = [m[0] for m in MADDELER]
    maske = rng.random((N, len(madde_kodlari))) < 0.018
    for j, kod in enumerate(madde_kodlari):
        ham.loc[maske[:, j], kod] = np.nan
    # birkaç katılımcıda demografik alanlar boş
    for sutun, adet in (("yas", 5), ("yayin_3yil", 3), ("haftalik_saat", 4)):
        ham.loc[rng.choice(N, adet, replace=False), sutun] = np.nan

    # 2) Kategori yazım tutarsızlıkları (form serbest metin kabul etmiş)
    yazim = {
        "Mühendislik ve Mimarlık": ["mühendislik", "Mühendislik",
                                    " Mühendislik ve Mimarlık"],
        "Fen-Edebiyat": ["fen edebiyat", "Fen Edebiyat"],
        "Tıp": ["tıp", "TIP", "Tıp Fakültesi"],
        "Eğitim": ["eğitim", "Eğitim Fakültesi"],
        "İktisadi ve İdari Bilimler": ["İİBF", "iibf"],
        "İlahiyat": ["ilahiyat"],
    }
    for i in rng.choice(N, 22, replace=False):
        ham.at[i, "fakulte"] = rng.choice(yazim[ham.at[i, "fakulte"]])
    for i in rng.choice(N, 14, replace=False):
        ham.at[i, "unvan"] = f" {ham.at[i, 'unvan']} "      # boşluk kiri
    for i in rng.choice(N, 9, replace=False):
        ham.at[i, "unvan"] = (str(ham.at[i, "unvan"]).strip()
                              .replace("Dr. Öğr. Üyesi", "Dr. Öğretim Üyesi")
                              .replace("Doçent", "Doç. Dr."))

    # 3) Aralığa sığmayan değerler (form doğrulaması yokmuş)
    ham.at[int(rng.integers(N)), "yas"] = 3                 # imkânsız yaş
    ham.at[int(rng.integers(N)), "haftalik_saat"] = 168.0   # haftanın tamamı
    ham.at[int(rng.integers(N)), "AF3"] = 7                 # ölçek 1–5

    # 4) Mükerrer satır: iki katılımcı formu iki kez göndermiş
    ham = pd.concat([ham, ham.iloc[[17, 203]].copy()], ignore_index=True)

    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    ham.to_csv(hedef / "anket_ham.csv", index=False, encoding="utf-8-sig")

    pd.DataFrame(
        [{"madde": kod, "olcek": lat, "ters_kodlu": "evet" if ters else "hayır",
          "metin": metin}
         for kod, metin, lat, _y, _k, ters in MADDELER]
    ).to_csv(hedef / "anket_madde_sozlugu.csv", index=False,
              encoding="utf-8-sig")

    print(f"Ham dosya  : {hedef / 'anket_ham.csv'}  "
          f"({len(ham)} satır, {ham.shape[1]} sütun)")
    print(f"Madde sözl.: {hedef / 'anket_madde_sozlugu.csv'}")
    print(f"  eksik hücre   : {int(ham.isna().sum().sum())}")
    print(f"  mükerrer satır: {int(ham.duplicated().sum())}")


if __name__ == "__main__":
    main(sys.argv[1])
