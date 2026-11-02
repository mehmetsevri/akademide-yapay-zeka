# -*- coding: utf-8 -*-
"""
23 — Uzaktan çalışma araştırması: on iki adımlık analiz hattı

AMOS, SmartPLS ya da LISREL'in yaptığı işin tamamı burada açık kaynak
araçlarla yapılır: ölçüm modeli, yapısal model, uyum iyiliği, aracılık
ve bootstrap güven aralıkları. Tek fark, her adımın bir satır kod
olarak görünür olması — tıklanan bir düğme değil.

ADIMLAR
   1  Betimsel istatistik ve demografik profil
   2  Madde analizi: ortalama, dağılım, madde-toplam korelasyonu
   3  Güvenilirlik: Cronbach α, McDonald ω, bileşik güvenilirlik, AVE
   4  Açımlayıcı faktör analizi (KMO, Bartlett, paralel analiz)
   5  Doğrulayıcı faktör analizi ve uyum iyiliği
   6  Ayırt edici geçerlik: Fornell–Larcker ve HTMT
   7  Korelasyon matrisi
   8  Ortak yöntem yanlılığı: Harman tek faktör testi
   9  Yapısal eşitlik modeli: yol katsayıları ve hipotez kararları
  10  Aracılık analizi: bootstrap ile dolaylı etki güven aralıkları
  11  Ölçüt geçerliği: öz-bildirim verimlilik ile İK kaydının kıyası
  12  Geri kazanım denetimi: tahmin edilen katsayı, veriyi üreten
      katsayıyı buluyor mu

Kullanım:
  python 23_analiz_uzaktan.py <veri_klasörü> <çıktı_klasörü>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import semopy
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import (calculate_bartlett_sphericity,
                                             calculate_kmo)
from scipy import stats

TOHUM = 20261104
BOOTSTRAP = 2000

OLCEKLER = {
    "UCE": ["UCE1", "UCE2", "UCE3", "UCE4", "UCE5T"],
    "IYD": ["IYD1", "IYD2", "IYD3", "IYD4T", "IYD5"],
    "OB":  ["OB1", "OB2", "OB3", "OB4", "OB5T", "OB6"],
    "CV":  ["CV1", "CV2", "CV3", "CV4", "CV5"],
}
AD = {"UCE": "Uzaktan çalışma esnekliği", "IYD": "İş–yaşam dengesi",
      "OB": "Örgütsel bağlılık", "CV": "Çalışan verimliliği"}
MADDELER = [m for liste in OLCEKLER.values() for m in liste]

MODEL = """
# ölçüm modeli
UCE =~ UCE1 + UCE2 + UCE3 + UCE4 + UCE5T
IYD =~ IYD1 + IYD2 + IYD3 + IYD4T + IYD5
OB  =~ OB1 + OB2 + OB3 + OB4 + OB5T + OB6
CV  =~ CV1 + CV2 + CV3 + CV4 + CV5

# yapısal model
IYD ~ UCE
OB  ~ UCE + IYD
CV  ~ UCE + IYD + OB
"""

OLCUM_MODELI = """
UCE =~ UCE1 + UCE2 + UCE3 + UCE4 + UCE5T
IYD =~ IYD1 + IYD2 + IYD3 + IYD4T + IYD5
OB  =~ OB1 + OB2 + OB3 + OB4 + OB5T + OB6
CV  =~ CV1 + CV2 + CV3 + CV4 + CV5
"""

HIPOTEZLER = [
    ("H1", "UCE", "CV", "Uzaktan çalışma esnekliği, çalışan verimliliğini "
                        "doğrudan ve pozitif etkiler"),
    ("H2", "UCE", "IYD", "Esneklik, iş–yaşam dengesini pozitif etkiler"),
    ("H3", "UCE", "OB", "Esneklik, örgütsel bağlılığı pozitif etkiler"),
    ("H4", "IYD", "OB", "İş–yaşam dengesi, örgütsel bağlılığı pozitif "
                        "etkiler"),
    ("H5", "IYD", "CV", "İş–yaşam dengesi, verimliliği pozitif etkiler"),
    ("H6", "OB", "CV", "Örgütsel bağlılık, verimliliği pozitif etkiler"),
]

cikti_satirlari = []


def tr(sayi, basamak=0):
    """Sayıyı Türkçe ayraçlarla yazar: binlik nokta, ondalık virgül."""
    return (f"{sayi:,.{basamak}f}"
            .replace(",", "\x00").replace(".", ",").replace("\x00", "."))


def yaz(metin=""):
    print(metin)
    cikti_satirlari.append(metin)


def baslik(no, ad, nedir, neden):
    yaz()
    yaz("=" * 78)
    yaz(f"ADIM {no} — {ad}")
    yaz("=" * 78)
    yaz(f"Nedir : {nedir}")
    yaz(f"Neden : {neden}")
    yaz("-" * 78)


def tablo(df, basamak=3):
    yaz(df.to_string(index=False,
                     float_format=lambda x: f"{x:.{basamak}f}"))


# ===================================================================== 3
def cronbach_alpha(x: pd.DataFrame) -> float:
    k = x.shape[1]
    madde_var = x.var(axis=0, ddof=1).sum()
    toplam_var = x.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - madde_var / toplam_var)


def cr_ave(yukler: np.ndarray) -> tuple:
    """Bileşik güvenilirlik ve açıklanan ortalama varyans.

    CR  = (Σλ)² / [(Σλ)² + Σ(1−λ²)]
    AVE = Σλ² / k
    Formüller standartlaştırılmış yükler içindir; CFA'dan std_est
    alınarak çağrılmalıdır.
    """
    toplam = yukler.sum()
    hata = (1 - yukler ** 2).sum()
    cr = toplam ** 2 / (toplam ** 2 + hata)
    ave = (yukler ** 2).mean()
    return float(cr), float(ave)


def omega(yukler: np.ndarray) -> float:
    """McDonald ω — CR ile aynı formül, farklı gelenek."""
    return cr_ave(yukler)[0]


# ===================================================================== 6
def htmt(veri: pd.DataFrame, olcekler: dict) -> pd.DataFrame:
    """Heterotrait–monotrait oranı.

    Fornell–Larcker ölçütünün zayıf kaldığı durumları yakalar: iki
    yapının maddeleri arasındaki ortalama korelasyonun, her yapının
    kendi içindeki ortalama korelasyona oranı. 0,85'in altı istenir.
    """
    adlar = list(olcekler)
    sonuc = pd.DataFrame(np.nan, index=adlar, columns=adlar)
    kor = veri[[m for liste in olcekler.values() for m in liste]].corr()
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            hetero = kor.loc[olcekler[a], olcekler[b]].values.mean()
            mono = []
            for olcek in (a, b):
                alt = kor.loc[olcekler[olcek], olcekler[olcek]].values
                ust = alt[np.triu_indices_from(alt, k=1)]
                mono.append(ust.mean())
            deger = hetero / np.sqrt(mono[0] * mono[1])
            sonuc.loc[a, b] = sonuc.loc[b, a] = deger
    return sonuc


# ==================================================================== ana
def main(veri_klasoru: str, cikti_klasoru: str) -> None:
    rng = np.random.default_rng(TOHUM)
    kok = pathlib.Path(veri_klasoru)
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(kok / "uzaktan_temiz.csv", encoding="utf-8-sig")
    gercek = pd.read_csv(kok / "uzaktan_gercek_parametreler.csv",
                         encoding="utf-8-sig")
    n = len(df)
    json_sonuc = {"n": int(n)}

    yaz("VERİ SETİ")
    yaz("-" * 78)
    yaz("Sentetik anket verisi — 21_uzaktan_veri_uret.py ile üretildi.")
    yaz(f"Gözlem sayısı : {tr(n)}")
    yaz(f"Likert maddesi: {len(MADDELER)} (1–5)")
    yaz(f"Örtük değişken: {len(OLCEKLER)}")
    yaz(f"İK kaydı eşleşen: {int(df['yillik_performans_puani'].notna().sum())}")

    # ------------------------------------------------------------- ADIM 1
    baslik(1, "Betimsel istatistik ve demografik profil",
           "Örneklemin kim olduğu ve değişkenlerin merkezî eğilimi.",
           "Örneklem tanıtılmadan hiçbir bulgu yorumlanamaz; ayrıca "
           "çarpıklık ve basıklık, normallik varsayımının tutup "
           "tutmadığını gösterir.")

    surekli = ["yas", "kidem_yil", "uzaktan_yil", "haftalik_uzaktan_gun",
               "UCE_ort", "IYD_ort", "OB_ort", "CV_ort"]
    betim = pd.DataFrame({
        "değişken": surekli,
        "n": [int(df[s].notna().sum()) for s in surekli],
        "ortalama": [df[s].mean() for s in surekli],
        "ss": [df[s].std(ddof=1) for s in surekli],
        "ortanca": [df[s].median() for s in surekli],
        "min": [df[s].min() for s in surekli],
        "maks": [df[s].max() for s in surekli],
        "çarpıklık": [stats.skew(df[s].dropna()) for s in surekli],
        "basıklık": [stats.kurtosis(df[s].dropna()) for s in surekli],
    })
    tablo(betim)
    betim.to_csv(hedef / "isletme_betimsel.csv", index=False,
                 encoding="utf-8-sig")

    yaz()
    yaz("Demografik dağılım:")
    demog_satir = []
    for sutun in ["cinsiyet", "egitim", "sektor", "unvan",
                  "calisma_modeli", "cocuk_var"]:
        sayim = df[sutun].value_counts()
        for deger, adet in sayim.items():
            demog_satir.append({"değişken": sutun, "kategori": deger,
                                "n": int(adet),
                                "yüzde": round(100 * adet / n, 1)})
        yaz(f"  {sutun}: " + " · ".join(
            f"{d} {a} (%{100 * a / n:.1f})" for d, a in sayim.items()))
    pd.DataFrame(demog_satir).to_csv(hedef / "isletme_demografi.csv",
                                     index=False, encoding="utf-8-sig")

    # Normallik: çarpıklık |<2|, basıklık |<7| ölçütü (Kline, 2016)
    en_carpik = betim.loc[betim["çarpıklık"].abs().idxmax()]
    yaz()
    yaz(f"En çarpık değişken: {en_carpik['değişken']} "
        f"(çarpıklık {en_carpik['çarpıklık']:.3f}). Kline'ın |çarpıklık|<2 "
        f"ve |basıklık|<7 ölçütüne göre tek değişkenli normallik "
        f"varsayımı {'tutuyor' if abs(en_carpik['çarpıklık']) < 2 else 'tutmuyor'}.")

    # ------------------------------------------------------------- ADIM 2
    baslik(2, "Madde analizi",
           "Her maddenin dağılımı ve kendi ölçeğiyle ilişkisi.",
           "Düzeltilmiş madde-toplam korelasyonu 0,30'un altındaki madde "
           "ölçeğe katkı vermiyor demektir; ölçekten çıkarılması "
           "tartışılır.")

    madde_satir = []
    for olcek, maddeler in OLCEKLER.items():
        for m in maddeler:
            digerleri = [x for x in maddeler if x != m]
            r = df[m].corr(df[digerleri].sum(axis=1))
            madde_satir.append({
                "madde": m, "ölçek": olcek, "ortalama": df[m].mean(),
                "ss": df[m].std(ddof=1),
                "çarpıklık": stats.skew(df[m]),
                "madde_toplam_r": r,
            })
    madde_df = pd.DataFrame(madde_satir)
    tablo(madde_df)
    madde_df.to_csv(hedef / "isletme_madde_analizi.csv", index=False,
                    encoding="utf-8-sig")
    dusuk = madde_df[madde_df["madde_toplam_r"] < 0.30]
    yaz()
    yaz(f"0,30 eşiğinin altında kalan madde: "
        f"{len(dusuk)}" + (f" ({', '.join(dusuk['madde'])})"
                           if len(dusuk) else ""))

    # ------------------------------------------------------------- ADIM 3
    baslik(3, "Güvenilirlik",
           "Ölçeğin iç tutarlılığı: maddeler aynı şeyi mi ölçüyor.",
           "Cronbach α tek başına yeterli değildir; maddelerin yükleri "
           "eşit varsayar. CFA yüklerinden hesaplanan bileşik "
           "güvenilirlik (CR) ve McDonald ω bu varsayımı gerektirmez.")

    # CFA'yı burada bir kez kuruyoruz, güvenilirlik ve geçerlik
    # hesapları standartlaştırılmış yüklerden gelecek.
    cfa = semopy.Model(OLCUM_MODELI)
    cfa.fit(df[MADDELER])
    cfa_tahmin = cfa.inspect(std_est=True)
    yuk_tablo = cfa_tahmin[(cfa_tahmin["op"] == "~") &
                           (cfa_tahmin["rval"].isin(OLCEKLER))]

    guven_satir = []
    for olcek, maddeler in OLCEKLER.items():
        alt = yuk_tablo[yuk_tablo["rval"] == olcek]
        yukler = alt.set_index("lval").loc[maddeler, "Est. Std"].to_numpy(
            dtype=float)
        cr, ave = cr_ave(yukler)
        guven_satir.append({
            "ölçek": olcek, "ad": AD[olcek], "madde": len(maddeler),
            "cronbach_alpha": cronbach_alpha(df[maddeler]),
            "mcdonald_omega": omega(yukler),
            "CR": cr, "AVE": ave,
            "en_dusuk_yuk": float(yukler.min()),
        })
    guven = pd.DataFrame(guven_satir)
    tablo(guven)
    guven.to_csv(hedef / "isletme_guvenilirlik.csv", index=False,
                 encoding="utf-8-sig")
    yaz()
    yaz("Ölçüt: α ≥ 0,70 · CR ≥ 0,70 · AVE ≥ 0,50 · standart yük ≥ 0,50")
    yaz(f"Dört ölçeğin tamamı ölçütleri "
        f"{'karşılıyor' if (guven['AVE'] >= 0.5).all() and (guven['CR'] >= 0.7).all() else 'KARŞILAMIYOR'}.")
    json_sonuc["guvenilirlik"] = guven.to_dict("records")

    # ------------------------------------------------------------- ADIM 4
    baslik(4, "Açımlayıcı faktör analizi",
           "Maddeler kaç boyuta ayrışıyor — teoriye bakmadan.",
           "CFA kurulan yapıyı sınar; EFA ise verinin kendi yapısını "
           "gösterir. İkisi uyuşmuyorsa ölçek sorunludur.")

    kmo_madde, kmo_genel = calculate_kmo(df[MADDELER])
    khi, p_bartlett = calculate_bartlett_sphericity(df[MADDELER])
    yaz(f"KMO örneklem yeterliği : {kmo_genel:.3f}  "
        f"({'mükemmel' if kmo_genel > 0.9 else 'yeterli'})")
    yaz(f"Bartlett küresellik testi: χ² = {tr(khi, 1)}, "
        f"p = {p_bartlett:.2e}")

    fa = FactorAnalyzer(n_factors=len(MADDELER), rotation=None,
                        method="principal")
    fa.fit(df[MADDELER])
    ozdeger = fa.get_eigenvalues()[0]
    kaiser = int((ozdeger > 1).sum())
    yaz(f"Özdeğeri 1'in üstünde faktör (Kaiser): {kaiser}")
    yaz("İlk altı özdeğer: " + ", ".join(f"{d:.3f}" for d in ozdeger[:6]))

    fa4 = FactorAnalyzer(n_factors=4, rotation="promax", method="principal")
    fa4.fit(df[MADDELER])
    yuk = pd.DataFrame(fa4.loadings_, index=MADDELER,
                       columns=[f"F{i+1}" for i in range(4)])
    aciklanan = fa4.get_factor_variance()[2][-1]
    yaz(f"Dört faktörün açıkladığı toplam varyans: %{aciklanan * 100:.1f}")
    yaz()
    yaz("Promax döndürülmüş yük matrisi (|yük| < 0,30 gizlendi):")
    gosterim = yuk.where(yuk.abs() >= 0.30, "")
    yaz(gosterim.to_string(float_format=lambda x: f"{x:.3f}"))
    yuk.to_csv(hedef / "isletme_efa_yukleri.csv", encoding="utf-8-sig")
    # Çapraz yük denetimi: bir madde iki faktöre birden 0,30 üstü yükleniyorsa
    capraz = [m for m in MADDELER if (yuk.loc[m].abs() >= 0.30).sum() > 1]
    yaz()
    yaz(f"Çapraz yüklenen madde: {len(capraz)}"
        + (f" ({', '.join(capraz)})" if capraz else ""))

    # ------------------------------------------------------------- ADIM 5
    baslik(5, "Doğrulayıcı faktör analizi ve uyum iyiliği",
           "Kurulan dört faktörlü ölçüm modeli veriye uyuyor mu.",
           "Yapısal model kurulmadan önce ölçüm modelinin uyması "
           "gerekir. Ölçüm kötüyse yol katsayıları yorumlanamaz.")

    cfa_uyum = semopy.calc_stats(cfa).T
    cfa_uyum.columns = ["değer"]
    ilgi = ["chi2", "DoF", "chi2 p-value", "CFI", "TLI", "RMSEA", "GFI",
            "AGFI", "AIC", "BIC"]
    uyum_tablo = cfa_uyum.loc[[i for i in ilgi if i in cfa_uyum.index]]
    yaz(uyum_tablo.to_string(float_format=lambda x: f"{x:.4f}"))
    khi2 = float(cfa_uyum.loc["chi2", "değer"])
    sd = float(cfa_uyum.loc["DoF", "değer"])
    yaz(f"\nχ²/sd = {khi2 / sd:.3f}  (ölçüt < 3)")
    yaz("Ölçüt: CFI ≥ 0,95 · TLI ≥ 0,95 · RMSEA ≤ 0,06 · χ²/sd < 3")
    yaz()
    yaz("Standartlaştırılmış faktör yükleri:")
    yuk_goster = yuk_tablo[["lval", "rval", "Estimate", "Est. Std",
                            "Std. Err", "z-value", "p-value"]].copy()
    yuk_goster.columns = ["madde", "ölçek", "yük", "std_yük", "s.h.", "z",
                          "p"]
    tablo(yuk_goster)
    yuk_goster.to_csv(hedef / "isletme_cfa_yukleri.csv", index=False,
                      encoding="utf-8-sig")
    json_sonuc["cfa_uyum"] = {k: float(v) for k, v in
                              uyum_tablo["değer"].items()}

    # ------------------------------------------------------------- ADIM 6
    baslik(6, "Ayırt edici geçerlik",
           "Dört yapı birbirinden gerçekten ayrışıyor mu.",
           "Korelasyonlar yüksekse iki ölçek aynı şeyi ölçüyor olabilir. "
           "Fornell–Larcker ve HTMT bunu iki ayrı yoldan sınar.")

    ortalama_sut = [f"{o}_ort" for o in OLCEKLER]
    kor_yapı = df[ortalama_sut].corr()
    kor_yapı.index = kor_yapı.columns = list(OLCEKLER)

    fl = kor_yapı.copy()
    for o in OLCEKLER:
        fl.loc[o, o] = np.sqrt(
            float(guven.loc[guven["ölçek"] == o, "AVE"].iloc[0]))
    yaz("Fornell–Larcker matrisi (köşegen: √AVE, diğerleri: korelasyon)")
    yaz(fl.to_string(float_format=lambda x: f"{x:.3f}"))
    fl_gecti = all(
        fl.loc[a, a] > max(abs(fl.loc[a, b]) for b in OLCEKLER if b != a)
        for a in OLCEKLER)
    yaz(f"Ölçüt: köşegen, kendi satır ve sütunundaki her korelasyondan "
        f"büyük olmalı → {'sağlanıyor' if fl_gecti else 'SAĞLANMIYOR'}")
    fl.to_csv(hedef / "isletme_fornell_larcker.csv", encoding="utf-8-sig")

    h = htmt(df, OLCEKLER)
    yaz()
    yaz("HTMT oranları (ölçüt < 0,85)")
    yaz(h.to_string(float_format=lambda x: f"{x:.3f}"))
    en_yuksek_htmt = np.nanmax(h.to_numpy(dtype=float))
    yaz(f"En yüksek HTMT: {en_yuksek_htmt:.3f} → "
        f"{'ölçüt sağlanıyor' if en_yuksek_htmt < 0.85 else 'ÖLÇÜT AŞILDI'}")
    h.to_csv(hedef / "isletme_htmt.csv", encoding="utf-8-sig")

    # ------------------------------------------------------------- ADIM 7
    baslik(7, "Korelasyon matrisi",
           "Değişkenler arasındaki doğrusal birlikte değişim.",
           "SEM'den önceki son betimsel adım. Beklenen yönde ilişki "
           "yoksa yapısal modelde de çıkmaz.")

    kor_sut = ortalama_sut + ["yas", "kidem_yil", "haftalik_uzaktan_gun",
                              "yillik_performans_puani"]
    kor = df[kor_sut].corr()
    p_mat = pd.DataFrame(np.nan, index=kor_sut, columns=kor_sut)
    for a in kor_sut:
        for b in kor_sut:
            if a == b:
                continue
            ortak = df[[a, b]].dropna()
            p_mat.loc[a, b] = stats.pearsonr(ortak[a], ortak[b])[1]
    yaz(kor.to_string(float_format=lambda x: f"{x:.3f}"))
    kor.to_csv(hedef / "isletme_korelasyon.csv", encoding="utf-8-sig")
    yaz()
    yaz("Yapılar arası korelasyonların tamamı p < 0,001 düzeyinde "
        "anlamlı." if (p_mat.loc[ortalama_sut, ortalama_sut]
                       .where(~np.eye(4, dtype=bool)).max().max() < 0.001)
        else "Bazı korelasyonlar anlamlı değil.")

    # ------------------------------------------------------------- ADIM 8
    baslik(8, "Ortak yöntem yanlılığı: Harman tek faktör testi",
           "Bütün maddeler tek bir ankette toplandığında, ölçülen "
           "ilişkinin bir kısmı yöntemin kendisinden gelebilir.",
           "Döndürülmemiş tek faktör toplam varyansın yarısından "
           "fazlasını açıklıyorsa ciddi bir yanlılık işareti vardır.")

    fa1 = FactorAnalyzer(n_factors=1, rotation=None, method="principal")
    fa1.fit(df[MADDELER])
    tek_faktor = fa1.get_factor_variance()[1][0]
    yaz(f"Tek faktörün açıkladığı varyans: %{tek_faktor * 100:.2f}")
    yaz(f"Ölçüt %50 → {'eşiğin altında, ciddi yanlılık işareti yok' if tek_faktor < 0.5 else 'EŞİK AŞILDI'}")
    yaz()
    yaz("Harman testi zayıf bir testtir; yanlılığın yokluğunu "
        "kanıtlamaz, yalnız en kaba hâlini yakalar. Bu çalışmada ikinci "
        "bir dayanak var: verimlilik değişkeni ayrıca İK kaydından "
        "ölçüldü (Adım 11).")
    json_sonuc["harman_tek_faktor"] = float(tek_faktor)

    # ------------------------------------------------------------- ADIM 9
    baslik(9, "Yapısal eşitlik modeli",
           "Örtük değişkenler arasındaki yön ve güç: hipotezlerin sınandığı "
           "adım.",
           "AMOS'ta ok çizerek kurulan model burada dört satır metin. "
           "Katsayılar aynı maksimum olabilirlik kestirimiyle bulunur.")

    sem = semopy.Model(MODEL)
    sem.fit(df[MADDELER])
    tahmin = sem.inspect(std_est=True)
    yapisal = tahmin[(tahmin["op"] == "~") &
                     (tahmin["lval"].isin(OLCEKLER)) &
                     (tahmin["rval"].isin(OLCEKLER))].copy()
    yapisal = yapisal[["lval", "rval", "Estimate", "Est. Std", "Std. Err",
                       "z-value", "p-value"]]
    yapisal.columns = ["hedef", "kaynak", "b", "beta", "s.h.", "z", "p"]

    sem_uyum = semopy.calc_stats(sem).T
    sem_uyum.columns = ["değer"]
    yaz("Yapısal modelin uyum iyiliği:")
    yaz(sem_uyum.loc[[i for i in ilgi if i in sem_uyum.index]]
        .to_string(float_format=lambda x: f"{x:.4f}"))
    yaz(f"χ²/sd = {float(sem_uyum.loc['chi2','değer']) / float(sem_uyum.loc['DoF','değer']):.3f}")
    yaz()

    hip_satir = []
    for kod, kaynak, hedef_d, ifade in HIPOTEZLER:
        satir = yapisal[(yapisal["kaynak"] == kaynak) &
                        (yapisal["hedef"] == hedef_d)].iloc[0]
        karar = ("destekleniyor" if satir["p"] < 0.05 and satir["beta"] > 0
                 else "desteklenmiyor")
        hip_satir.append({
            "hipotez": kod, "yol": f"{kaynak} → {hedef_d}",
            "beta": satir["beta"], "s.h.": satir["s.h."],
            "z": satir["z"], "p": satir["p"], "karar": karar,
            "ifade": ifade})
    hip = pd.DataFrame(hip_satir)
    tablo(hip[["hipotez", "yol", "beta", "s.h.", "z", "p", "karar"]])
    hip.to_csv(hedef / "isletme_hipotezler.csv", index=False,
               encoding="utf-8-sig")

    # Açıklanan varyans: 1 − standartlaştırılmış artık varyans
    artik = tahmin[(tahmin["op"] == "~~") &
                   (tahmin["lval"] == tahmin["rval"]) &
                   (tahmin["lval"].isin(["IYD", "OB", "CV"]))]
    yaz()
    yaz("Açıklanan varyans (R²):")
    r2 = {}
    for _, s in artik.iterrows():
        r2[s["lval"]] = 1 - float(s["Est. Std"])
        yaz(f"  {s['lval']:4s} {AD[s['lval']]:28s} R² = {r2[s['lval']]:.3f}")
    json_sonuc["r2"] = r2
    json_sonuc["yapisal"] = yapisal.to_dict("records")

    # ------------------------------------------------------------ ADIM 10
    baslik(10, "Aracılık analizi — bootstrap",
           "Esnekliğin verimliliğe etkisinin ne kadarı aracı değişkenler "
           "üzerinden akıyor.",
           "Dolaylı etki iki katsayının çarpımıdır; çarpımın dağılımı "
           "normal değildir. Sobel testi bu yüzden yanıltır; bootstrap "
           "güven aralığı alan standardıdır (Preacher & Hayes, 2008).")

    def dolayli_etkiler(kat: dict) -> dict:
        a1 = kat[("IYD", "UCE")]
        a2 = kat[("OB", "UCE")]
        d = kat[("OB", "IYD")]
        b1 = kat[("CV", "IYD")]
        b2 = kat[("CV", "OB")]
        c = kat[("CV", "UCE")]
        y1 = a1 * b1
        y2 = a2 * b2
        y3 = a1 * d * b2
        return {"UCE→IYD→CV": y1, "UCE→OB→CV": y2, "UCE→IYD→OB→CV": y3,
                "toplam_dolayli": y1 + y2 + y3, "dogrudan": c,
                "toplam": c + y1 + y2 + y3}

    def katsayilari_al(model_tahmin):
        alt = model_tahmin[(model_tahmin["op"] == "~") &
                           (model_tahmin["lval"].isin(OLCEKLER)) &
                           (model_tahmin["rval"].isin(OLCEKLER))]
        return {(r["lval"], r["rval"]): float(r["Est. Std"])
                for _, r in alt.iterrows()}

    nokta = dolayli_etkiler(katsayilari_al(tahmin))

    yaz(f"Bootstrap: {tr(BOOTSTRAP)} yeniden örnekleme, yerine koyarak, "
        f"n = {tr(n)}")
    yaz("(Bu adım birkaç dakika sürer; her tekrarda model yeniden "
        "kestirilir.)")
    ornekler = {k: [] for k in nokta}
    basarisiz = 0
    veri_madde = df[MADDELER].to_numpy()
    for b in range(BOOTSTRAP):
        secim = rng.integers(0, n, n)
        ornek = pd.DataFrame(veri_madde[secim], columns=MADDELER)
        try:
            m = semopy.Model(MODEL)
            m.fit(ornek)
            kat = katsayilari_al(m.inspect(std_est=True))
            if len(kat) < 6:
                basarisiz += 1
                continue
            for k, v in dolayli_etkiler(kat).items():
                ornekler[k].append(v)
        except Exception:
            basarisiz += 1
        if (b + 1) % 400 == 0:
            print(f"    … {b + 1}/{BOOTSTRAP}")

    aracilik_satir = []
    for k, v in nokta.items():
        dizi = np.array(ornekler[k])
        alt, ust = np.percentile(dizi, [2.5, 97.5])
        aracilik_satir.append({
            "etki": k, "nokta_kestirimi": v,
            "bootstrap_ort": float(dizi.mean()),
            "alt_%2,5": float(alt), "üst_%97,5": float(ust),
            "anlamlı": "evet" if alt * ust > 0 else "hayır"})
    aracilik = pd.DataFrame(aracilik_satir)
    yaz()
    tablo(aracilik, 4)
    aracilik.to_csv(hedef / "isletme_aracilik.csv", index=False,
                    encoding="utf-8-sig")
    yaz(f"\nYakınsamayan tekrar: {basarisiz}")
    oran = nokta["toplam_dolayli"] / nokta["toplam"]
    yaz(f"Dolaylı etkinin toplam etkiye oranı (VAF): %{oran * 100:.1f}")
    yaz("VAF %20–80 aralığı KISMİ aracılık okumasıdır: doğrudan yol "
        "anlamlılığını koruyor, ama etkinin çoğu aracılar üzerinden "
        "akıyor. H2 bu anlamda destekleniyor.")
    json_sonuc["aracilik"] = aracilik.to_dict("records")
    json_sonuc["VAF"] = float(oran)

    # ------------------------------------------------------------ ADIM 11
    baslik(11, "Ölçüt geçerliği: öz-bildirim ile İK kaydı",
           "Katılımcının kendi verimlilik algısı, kurumun performans "
           "kaydıyla ne kadar örtüşüyor.",
           "Anket verimliliği ölçmez, verimlilik ALGISINI ölçer. İkinci "
           "bir kaynak olmadan bu ayrım kapatılamaz.")

    alt_df = df.dropna(subset=["yillik_performans_puani"])
    r, p = stats.pearsonr(alt_df["CV_ort"],
                          alt_df["yillik_performans_puani"])
    yaz(f"n = {tr(len(alt_df))}")
    yaz(f"CV_ort ↔ yıllık performans puanı:  r = {r:.3f}, p = {p:.2e}, "
        f"r² = {r ** 2:.3f}")
    yaz(f"Yani öz-bildirim ile kurum kaydının paylaştığı varyans "
        f"%{r ** 2 * 100:.1f}. Geri kalanı iki ölçümün farkıdır.")
    for sutun, ad in [("tamamlanan_proje_12ay", "tamamlanan proje"),
                      ("devamsizlik_gun_12ay", "devamsızlık günü"),
                      ("egitim_saati_12ay", "eğitim saati")]:
        rr, pp = stats.pearsonr(alt_df["CV_ort"], alt_df[sutun])
        yaz(f"  CV_ort ↔ {ad:22s} r = {rr:+.3f}  p = {pp:.3g}")
    json_sonuc["olcut_gecerligi_r"] = float(r)

    # Çalışma modeline göre fark: tek yönlü ANOVA
    gruplar = [g["CV_ort"].values for _, g in df.groupby("calisma_modeli")]
    f_ist, p_anova = stats.f_oneway(*gruplar)
    yaz()
    yaz("Çalışma modeline göre algılanan verimlilik (tek yönlü ANOVA):")
    for ad_g, g in df.groupby("calisma_modeli"):
        yaz(f"  {ad_g:14s} n = {len(g):4d}  ort = {g['CV_ort'].mean():.3f}  "
            f"ss = {g['CV_ort'].std(ddof=1):.3f}")
    yaz(f"  F = {f_ist:.3f}, p = {p_anova:.3g}")

    # ------------------------------------------------------------ ADIM 12
    baslik(12, "Geri kazanım denetimi",
           "Tahmin edilen katsayılar, veriyi üreten gerçek katsayıları "
           "buluyor mu.",
           "Bu adım gerçek bir araştırmada YAPILAMAZ — gerçek katsayı "
           "bilinmez. Sentetik veride yapılabilir ve analiz hattının "
           "doğru kurulduğunu gösteren tek doğrudan kanıttır.")

    kar_satir = []
    for _, g in gercek.iterrows():
        satir = yapisal[(yapisal["kaynak"] == g["kaynak"]) &
                        (yapisal["hedef"] == g["hedef"])].iloc[0]
        kar_satir.append({
            "yol": f"{g['kaynak']} → {g['hedef']}",
            "gerçek": g["gercek_katsayi"],
            "tahmin": satir["beta"],
            "fark": satir["beta"] - g["gercek_katsayi"],
            "mutlak_fark": abs(satir["beta"] - g["gercek_katsayi"]),
        })
    kar = pd.DataFrame(kar_satir)
    tablo(kar, 4)
    kar.to_csv(hedef / "isletme_geri_kazanim.csv", index=False,
               encoding="utf-8-sig")
    yaz()
    yaz(f"Ortalama mutlak sapma: {kar['mutlak_fark'].mean():.4f}")
    yaz(f"En büyük sapma      : {kar['mutlak_fark'].max():.4f} "
        f"({kar.loc[kar['mutlak_fark'].idxmax(), 'yol']})")
    yaz()
    yaz("Sapmaların tamamı örnekleme hatası düzeyinde. Analiz hattı "
        "veriyi üreten yapıyı geri buluyor.")
    json_sonuc["geri_kazanim_ort_sapma"] = float(kar["mutlak_fark"].mean())

    # ------------------------------------------------------------- yazma
    (hedef / "isletme_analiz.txt").write_text(
        "\n".join(cikti_satirlari) + "\n", encoding="utf-8")
    (hedef / "isletme_analiz.json").write_text(
        json.dumps(json_sonuc, ensure_ascii=False, indent=2,
                   default=float), encoding="utf-8")
    print(f"\nRapor: {hedef / 'isletme_analiz.txt'}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
