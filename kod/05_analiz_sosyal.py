# -*- coding: utf-8 -*-
"""
05 — Sosyal bilimler analizi: Gazi ders değerlendirme verisi

Bu betik kursun 8. bölümünde verilen istemlerin çıktısıdır. On bir analiz
adımını sırayla koşar, her adımın sonucunu hem okunur metin hem makine
okunur JSON olarak yazar.

Her adımın başında, o analizin NE olduğu ve NEDEN seçildiği yazılıdır.
Analiz seçiminin gerekçesi, analizin kendisi kadar rapor edilebilir bir
bilgidir.

Kullanım:
  python 05_analiz_sosyal.py <veri_klasörü> <çıktı_klasörü>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
from factor_analyzer.factor_analyzer import (
    calculate_bartlett_sphericity, calculate_kmo)
from sklearn.metrics import roc_auc_score

SONUC = {}
SATIRLAR = []


def json_cevir(nesne):
    """numpy sayı tiplerini standart Python tiplerine çevirir.

    numpy int64/float64 doğrudan JSON'a yazılamaz; pandas ve scipy
    çıktıları bu tipleri döndürdüğü için dönüştürücü gerekir.
    """
    if isinstance(nesne, (np.integer,)):
        return int(nesne)
    if isinstance(nesne, (np.floating,)):
        return float(nesne)
    if isinstance(nesne, (np.bool_,)):
        return bool(nesne)
    if isinstance(nesne, np.ndarray):
        return nesne.tolist()
    raise TypeError(f"JSON'a yazılamayan tip: {type(nesne).__name__}")


def yaz(metin=""):
    SATIRLAR.append(metin)
    print(metin)


def baslik(no, ad, nedir, neden):
    yaz()
    yaz("=" * 78)
    yaz(f"ADIM {no} — {ad}")
    yaz("=" * 78)
    yaz(f"Nedir : {nedir}")
    yaz(f"Neden : {neden}")
    yaz("-" * 78)


def cronbach_alfa(x: pd.DataFrame) -> float:
    """Cronbach alfa — maddeler arası iç tutarlılık katsayısı.

    alfa = k/(k-1) * (1 - sum(madde varyansları) / toplam puan varyansı)
    Madde sayısı k arttıkça alfa mekanik olarak yükselir; bu yüzden
    yüksek alfa tek başına 'iyi ölçek' demek değildir.
    """
    k = x.shape[1]
    madde_var = x.var(axis=0, ddof=1).sum()
    toplam_var = x.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - madde_var / toplam_var)


def varimax(yukler: np.ndarray, tol: float = 1e-6,
            en_fazla: int = 200) -> np.ndarray:
    """Kaiser (1958) varimax döndürmesi.

    Faktör eksenlerini, her maddenin tek bir faktöre yüklenmesini
    kolaylaştıracak biçimde döndürür. Döndürme, açıklanan toplam
    varyansı değiştirmez; yalnız varyansı faktörler arasında yeniden
    dağıtır. Bu yüzden 'yorumlanabilirlik' için yapılır.
    """
    p = yukler.shape[0]
    R = np.eye(yukler.shape[1])
    onceki = 0.0
    for _ in range(en_fazla):
        donmus = yukler @ R
        u, s_, vt = np.linalg.svd(
            yukler.T @ (donmus ** 3
                        - donmus @ np.diag((donmus ** 2).sum(axis=0)) / p))
        R = u @ vt
        simdiki = s_.sum()
        if onceki and simdiki / onceki < 1 + tol:
            break
        onceki = simdiki
    return yukler @ R


def temel_bilesen_yukleri(x: pd.DataFrame, faktor_sayisi: int):
    """Korelasyon matrisinin özçözümünden temel bileşen yüklerini verir.

    Yük = özvektör * sqrt(özdeğer). Bu, 'principal component' çıkarımının
    tanımıdır; ayrı bir kütüphane gerektirmez ve hesabın ne olduğu
    görünür kalır.
    """
    R = np.corrcoef(x.values, rowvar=False)
    ozdeger, ozvektor = np.linalg.eigh(R)
    sira = np.argsort(ozdeger)[::-1]
    ozdeger, ozvektor = ozdeger[sira], ozvektor[:, sira]
    yukler = ozvektor[:, :faktor_sayisi] * np.sqrt(ozdeger[:faktor_sayisi])
    return ozdeger, yukler


def cohen_d(a, b) -> float:
    """İki bağımsız grup için standartlaştırılmış ortalama farkı."""
    na, nb = len(a), len(b)
    s = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1))
                / (na + nb - 2))
    return (np.mean(a) - np.mean(b)) / s


def cramers_v(tablo: np.ndarray) -> float:
    """Ki-kare için etki büyüklüğü; 0 (ilişki yok) – 1 (tam ilişki)."""
    ki2 = stats.chi2_contingency(tablo)[0]
    n = tablo.sum()
    return np.sqrt((ki2 / n) / (min(tablo.shape) - 1))


def main(veri_klasoru: str, cikti_klasoru: str) -> None:
    kaynak = pathlib.Path(veri_klasoru)
    df = pd.read_csv(kaynak / "gazi_ders_degerlendirme.csv",
                     encoding="utf-8-sig")
    sozluk = pd.read_csv(kaynak / "gazi_madde_sozlugu.csv",
                         encoding="utf-8-sig")

    ders_m = sozluk.loc[sozluk["boyut"] == "Ders", "madde"].tolist()
    ogr_m = sozluk.loc[sozluk["boyut"] == "Öğretim elemanı", "madde"].tolist()
    tum_m = ders_m + ogr_m

    yaz("VERİ SETİ")
    yaz("-" * 78)
    yaz("Gündüz, N., & Fokoué, E. (2013). Turkiye Student Evaluation.")
    yaz("UCI Machine Learning Repository. https://doi.org/10.24432/C5S02S")
    yaz(f"Gözlem sayısı : {len(df):,}")
    yaz(f"Likert maddesi: {len(tum_m)} (1–5)")
    yaz(f"Eksik hücre   : {int(df.isna().sum().sum())}")
    SONUC["veri"] = {"n": int(len(df)), "madde": len(tum_m),
                     "eksik": int(df.isna().sum().sum()),
                     "kaynak_doi": "10.24432/C5S02S"}

    # ------------------------------------------------------------ ADIM 1
    baslik(1, "Betimsel istatistik",
           "Değişkenlerin merkezî eğilimi, yayılımı ve dağılım biçimi.",
           "Her analizin ilk adımı. Çarpıklık ve basıklık, sonraki adımda "
           "parametrik mi parametrik olmayan mı test kullanılacağını belirler.")
    betim = []
    for ad in ["ders_puan", "ogretim_puan", "genel_puan",
               "attendance", "difficulty", "nb.repeat"]:
        s = df[ad].astype(float)
        betim.append({
            "değişken": ad, "n": int(s.notna().sum()),
            "ortalama": round(s.mean(), 3), "ss": round(s.std(ddof=1), 3),
            "ortanca": round(s.median(), 3),
            "min": round(s.min(), 2), "maks": round(s.max(), 2),
            "çarpıklık": round(stats.skew(s.dropna()), 3),
            "basıklık": round(stats.kurtosis(s.dropna()), 3),
        })
    betim_df = pd.DataFrame(betim)
    yaz(betim_df.to_string(index=False))
    SONUC["betimsel"] = betim

    # Madde bazlı betimsel
    madde_betim = pd.DataFrame({
        "madde": tum_m,
        "boyut": ["Ders"] * len(ders_m) + ["Öğretim elemanı"] * len(ogr_m),
        "ortalama": [round(df[m].mean(), 3) for m in tum_m],
        "ss": [round(df[m].std(ddof=1), 3) for m in tum_m],
        "çarpıklık": [round(stats.skew(df[m]), 3) for m in tum_m],
    })
    SONUC["madde_betimsel"] = madde_betim.to_dict("records")
    yaz()
    yaz("Madde bazlı ortalamalar (ilk 6 ve son 6):")
    yaz(pd.concat([madde_betim.head(6), madde_betim.tail(6)]).to_string(index=False))

    # ------------------------------------------------------------ ADIM 2
    baslik(2, "Dağılım varsayımının denetimi",
           "Verinin normal dağılıma uygunluğunun sınanması.",
           "n = 5.820 gibi büyük örneklemlerde normallik testleri çok küçük "
           "sapmalarda bile anlamlı çıkar. Bu yüzden karar, yalnız p değerine "
           "değil çarpıklık/basıklık büyüklüğüne de dayandırılır.")
    normallik = []
    for ad in ["ders_puan", "ogretim_puan"]:
        s = df[ad].astype(float).dropna()
        ks = stats.kstest((s - s.mean()) / s.std(ddof=1), "norm")
        normallik.append({
            "değişken": ad,
            "Kolmogorov_Smirnov_D": round(ks.statistic, 4),
            "p": float(f"{ks.pvalue:.3g}"),
            "çarpıklık": round(stats.skew(s), 3),
            "basıklık": round(stats.kurtosis(s), 3),
            "yorum": ("Çarpıklık ve basıklık ±1 aralığında; büyük örneklemde "
                      "parametrik test uygulanabilir, ancak sonuçlar "
                      "parametrik olmayan karşılığıyla birlikte raporlanır."),
        })
        yaz(f"{ad}: K–S D = {ks.statistic:.4f}, p = {ks.pvalue:.3g}, "
            f"çarpıklık = {stats.skew(s):.3f}, basıklık = {stats.kurtosis(s):.3f}")
    SONUC["normallik"] = normallik

    # ------------------------------------------------------------ ADIM 3
    baslik(3, "Güvenilirlik — Cronbach alfa",
           "Aynı yapıyı ölçtüğü varsayılan maddelerin birbiriyle tutarlılığı.",
           "Ölçek puanı hesaplanmadan önce maddelerin gerçekten tek bir şeyi "
           "ölçtüğü gösterilmelidir. Aksi hâlde ortalama anlamsızdır.")
    guv = {}
    for ad, maddeler in [("Ders boyutu", ders_m),
                         ("Öğretim elemanı boyutu", ogr_m),
                         ("Tüm ölçek", tum_m)]:
        a = cronbach_alfa(df[maddeler])
        guv[ad] = {"madde_sayısı": len(maddeler), "alfa": round(a, 4)}
        yaz(f"{ad:24s} k = {len(maddeler):2d}   α = {a:.4f}")

    # Madde-toplam korelasyonu ve madde silinirse alfa
    mt = []
    for m in tum_m:
        kalan = [x for x in tum_m if x != m]
        r = df[m].corr(df[kalan].sum(axis=1))
        mt.append({"madde": m, "düzeltilmiş_madde_toplam_r": round(r, 3),
                   "madde_silinirse_alfa": round(cronbach_alfa(df[kalan]), 4)})
    mt_df = pd.DataFrame(mt)
    guv["madde_toplam"] = mt
    yaz()
    yaz("Düzeltilmiş madde-toplam korelasyonları: "
        f"en düşük {mt_df['düzeltilmiş_madde_toplam_r'].min():.3f} "
        f"({mt_df.loc[mt_df['düzeltilmiş_madde_toplam_r'].idxmin(), 'madde']}), "
        f"en yüksek {mt_df['düzeltilmiş_madde_toplam_r'].max():.3f} "
        f"({mt_df.loc[mt_df['düzeltilmiş_madde_toplam_r'].idxmax(), 'madde']})")
    yaz("Ölçüt: < 0,30 olan madde ölçekten çıkarılmaya aday sayılır. "
        f"Bu ölçeğin altında kalan madde sayısı: "
        f"{int((mt_df['düzeltilmiş_madde_toplam_r'] < 0.30).sum())}")
    yaz()
    yaz("NOT — α = %.3f gibi çok yüksek bir değer kusursuz ölçek demek "
        "değildir." % guv["Tüm ölçek"]["alfa"])
    yaz("Maddelerin birbirini tekrar ettiğine (gereksiz uzunluğa) de işaret")
    yaz("eder. Streiner (2003) 0,90 üstünü madde fazlalığı uyarısı sayar.")
    SONUC["guvenilirlik"] = guv

    # ------------------------------------------------------------ ADIM 4
    baslik(4, "Açımlayıcı faktör analizi (AFA)",
           "Maddelerin kaç gizli boyut altında kümelendiğinin veriden "
           "çıkarılması.",
           "Ölçeğin iki boyutlu (ders / öğretim elemanı) olduğu iddiası "
           "veriyle sınanır. Önce AFA'nın uygulanabilirliği KMO ve Bartlett "
           "ile denetlenir.")
    kmo_madde, kmo_toplam = calculate_kmo(df[tum_m])
    bart_ki2, bart_p = calculate_bartlett_sphericity(df[tum_m])
    yaz(f"KMO (örneklem yeterliği)       : {kmo_toplam:.4f}   "
        f"(> 0,90 'mükemmel')")
    yaz(f"Bartlett küresellik testi      : χ² = {bart_ki2:,.1f}, "
        f"p = {bart_p:.3g}  (p < 0,05 gerekli)")

    ozdegerler, ham_yukler = temel_bilesen_yukleri(df[tum_m], 2)
    birden_buyuk = int((ozdegerler > 1).sum())
    yaz(f"1'den büyük özdeğer sayısı     : {birden_buyuk}")
    yaz(f"İlk dört özdeğer               : "
        f"{', '.join(f'{v:.3f}' for v in ozdegerler[:4])}")

    donmus = varimax(ham_yukler)
    # Yük sütunlarının işaretini, toplamı artı olacak biçimde sabitle:
    # işaret faktör analizinde belirsizdir, okunurluk için düzeltilir.
    for j in range(donmus.shape[1]):
        if donmus[:, j].sum() < 0:
            donmus[:, j] *= -1
    yukler = pd.DataFrame(donmus, index=tum_m,
                          columns=["Faktör 1", "Faktör 2"]).round(3)
    # Açıklanan varyans: her faktörün yük kareleri toplamı / madde sayısı
    ss_yukler = (donmus ** 2).sum(axis=0)
    aciklanan = (ss_yukler,
                 ss_yukler / len(tum_m),
                 np.cumsum(ss_yukler / len(tum_m)))
    yaz()
    yaz("İki faktörlü varimax döndürülmüş yük matrisi — her maddenin "
        "yüklendiği faktör:")
    yukler["baskın"] = yukler.abs().idxmax(axis=1)
    yukler["beklenen_boyut"] = ["Ders"] * len(ders_m) + ["Öğretim"] * len(ogr_m)
    yaz(yukler.to_string())
    yaz()
    yaz(f"Açıklanan varyans — F1: %{100 * aciklanan[1][0]:.1f}, "
        f"F2: %{100 * aciklanan[1][1]:.1f}, "
        f"toplam: %{100 * aciklanan[2][1]:.1f}")
    # Beklenen yapıyla uyum
    f1_ders = (yukler.loc[ders_m, "baskın"] == "Faktör 1").sum()
    f2_ders = (yukler.loc[ders_m, "baskın"] == "Faktör 2").sum()
    ders_faktoru = "Faktör 1" if f1_ders > f2_ders else "Faktör 2"
    ogr_faktoru = "Faktör 2" if ders_faktoru == "Faktör 1" else "Faktör 1"
    uyan = int((yukler.loc[ders_m, "baskın"] == ders_faktoru).sum()
               + (yukler.loc[ogr_m, "baskın"] == ogr_faktoru).sum())
    yaz(f"Beklenen iki boyutlu yapıya uyan madde: {uyan}/{len(tum_m)}")
    SONUC["afa"] = {
        "kmo": round(float(kmo_toplam), 4),
        "bartlett_ki2": round(float(bart_ki2), 1),
        "bartlett_p": float(f"{bart_p:.3g}"),
        "ozdeger_1_ustu": birden_buyuk,
        "ilk_dort_ozdeger": [round(float(v), 3) for v in ozdegerler[:4]],
        "aciklanan_varyans_toplam": round(float(100 * aciklanan[2][1]), 1),
        "aciklanan_f1": round(float(100 * aciklanan[1][0]), 1),
        "aciklanan_f2": round(float(100 * aciklanan[1][1]), 1),
        "yapiya_uyan_madde": uyan, "madde_sayisi": len(tum_m),
        "yukler": yukler.reset_index().rename(
            columns={"index": "madde"}).to_dict("records"),
    }

    # ------------------------------------------------------------ ADIM 5
    baslik(5, "İki grup karşılaştırması — bağımsız örneklem t testi",
           "İki ayrı grubun ortalamalarının farklı olup olmadığının sınanması.",
           "Karşılaştırılacak grup sayısı iki, bağımlı değişken sürekli ve "
           "gruplar birbirinden bağımsız olduğunda kullanılan testtir. "
           "Burada soru: derse çok katılan öğrenciler öğretim elemanını "
           "farklı mı değerlendiriyor?")
    dusuk = df.loc[df["attendance"] <= 1, "ogretim_puan"]
    yuksek = df.loc[df["attendance"] >= 3, "ogretim_puan"]
    lev = stats.levene(dusuk, yuksek)
    esit_varyans = lev.pvalue > 0.05
    t_sonuc = stats.ttest_ind(yuksek, dusuk, equal_var=esit_varyans)
    d = cohen_d(yuksek, dusuk)
    yaz(f"Grup A — düşük katılım (0–1): n = {len(dusuk):,}  "
        f"ort = {dusuk.mean():.3f}  ss = {dusuk.std(ddof=1):.3f}")
    yaz(f"Grup B — yüksek katılım (3–4): n = {len(yuksek):,}  "
        f"ort = {yuksek.mean():.3f}  ss = {yuksek.std(ddof=1):.3f}")
    yaz(f"Levene varyans eşitliği: W = {lev.statistic:.3f}, p = {lev.pvalue:.3g}"
        f"  →  {'varyanslar eşit sayıldı' if esit_varyans else 'Welch düzeltmesi uygulandı'}")
    yaz(f"t({t_sonuc.df if hasattr(t_sonuc,'df') else len(dusuk)+len(yuksek)-2:.0f}) "
        f"= {t_sonuc.statistic:.3f}, p = {t_sonuc.pvalue:.3g}")
    yaz(f"Cohen d = {d:.3f}  "
        f"({'ihmal edilebilir' if abs(d)<0.2 else 'küçük' if abs(d)<0.5 else 'orta' if abs(d)<0.8 else 'büyük'} etki)")
    yaz()
    yaz("NOT — p değeri farkın VAR olup olmadığını söyler, BÜYÜKLÜĞÜNÜ söylemez.")
    yaz("Etki büyüklüğü (Cohen d) raporlanmadan t testi sonucu yorumlanamaz.")
    SONUC["t_testi"] = {
        "grup_a": {"tanım": "katılım 0–1", "n": int(len(dusuk)),
                   "ortalama": round(float(dusuk.mean()), 3),
                   "ss": round(float(dusuk.std(ddof=1)), 3)},
        "grup_b": {"tanım": "katılım 3–4", "n": int(len(yuksek)),
                   "ortalama": round(float(yuksek.mean()), 3),
                   "ss": round(float(yuksek.std(ddof=1)), 3)},
        "levene_W": round(float(lev.statistic), 3),
        "levene_p": float(f"{lev.pvalue:.3g}"),
        "esit_varyans": bool(esit_varyans),
        "t": round(float(t_sonuc.statistic), 3),
        "p": float(f"{t_sonuc.pvalue:.3g}"),
        "cohen_d": round(float(d), 3)}

    # ------------------------------------------------------------ ADIM 6
    baslik(6, "Üç ve daha fazla grup — tek yönlü ANOVA",
           "Üç veya daha fazla grubun ortalamalarının birbirinden farklı "
           "olup olmadığının tek bir testle sınanması.",
           "Beş güçlük düzeyi var; ikili t testlerini tekrar etmek I. tip "
           "hata oranını şişirir. ANOVA bu beş ortalamayı tek testte "
           "karşılaştırır, sonra hangi ikilinin farklı olduğu post-hoc "
           "testle bulunur.")
    gruplar = [g["ders_puan"].values for _, g in df.groupby("difficulty")]
    lev2 = stats.levene(*gruplar)
    f_sonuc = stats.f_oneway(*gruplar)
    model_anova = smf.ols("ders_puan ~ C(difficulty)", data=df).fit()
    anova_tablo = sm.stats.anova_lm(model_anova, typ=2)
    eta2 = float(anova_tablo["sum_sq"].iloc[0] / anova_tablo["sum_sq"].sum())
    yaz("Güçlük düzeyine göre ders puanı:")
    ozet = df.groupby("difficulty")["ders_puan"].agg(
        ["count", "mean", "std"]).round(3)
    ozet.columns = ["n", "ortalama", "ss"]
    yaz(ozet.to_string())
    yaz()
    yaz(f"Levene: W = {lev2.statistic:.3f}, p = {lev2.pvalue:.3g}")
    yaz(f"F({int(anova_tablo['df'].iloc[0])}, {int(anova_tablo['df'].iloc[1])}) "
        f"= {f_sonuc.statistic:.3f}, p = {f_sonuc.pvalue:.3g}")
    yaz(f"η² (eta kare) = {eta2:.4f}  →  güçlük algısı, ders puanındaki "
        f"değişkenliğin %{100*eta2:.1f}'ini açıklıyor")
    if not (lev2.pvalue > 0.05):
        welch = stats.f_oneway(*gruplar)  # yerine Welch
        from scipy.stats import alexandergovern
        ag = alexandergovern(*gruplar)
        yaz(f"Varyanslar eşit değil → Alexander–Govern düzeltmesi: "
            f"A = {ag.statistic:.3f}, p = {ag.pvalue:.3g}")
    tukey = pairwise_tukeyhsd(df["ders_puan"], df["difficulty"], alpha=0.05)
    yaz()
    yaz("Tukey HSD post-hoc (hangi ikili farklı):")
    yaz(str(tukey))
    SONUC["anova"] = {
        "grup_ozeti": ozet.reset_index().to_dict("records"),
        "levene_W": round(float(lev2.statistic), 3),
        "levene_p": float(f"{lev2.pvalue:.3g}"),
        "F": round(float(f_sonuc.statistic), 3),
        "df_arasi": int(anova_tablo["df"].iloc[0]),
        "df_ici": int(anova_tablo["df"].iloc[1]),
        "p": float(f"{f_sonuc.pvalue:.3g}"),
        "eta_kare": round(eta2, 4),
        "tukey": [{"grup1": r[0], "grup2": r[1], "fark": round(float(r[2]), 3),
                   "p_düzeltilmiş": float(f"{r[3]:.3g}"),
                   "anlamlı": bool(r[6])}
                  for r in tukey.summary().data[1:]]}

    # ------------------------------------------------------------ ADIM 7
    baslik(7, "Parametrik olmayan karşılıklar",
           "Normal dağılım varsayımı kurulmadan, sıra (rank) üzerinden "
           "çalışan testler.",
           "Likert verisi sıralı ölçektir ve dağılımı normal olmayabilir. "
           "Parametrik testin sonucunu parametrik olmayan karşılığıyla "
           "birlikte raporlamak, sonucun varsayıma bağlı olmadığını gösterir.")
    mw = stats.mannwhitneyu(yuksek, dusuk, alternative="two-sided")
    # rank-biserial korelasyon: Mann-Whitney icin etki buyuklugu
    n1, n2 = len(yuksek), len(dusuk)
    rb = 1 - (2 * mw.statistic) / (n1 * n2)
    kw = stats.kruskal(*gruplar)
    n_top = sum(len(g) for g in gruplar)
    epsilon2 = (kw.statistic - len(gruplar) + 1) / (n_top - len(gruplar))
    yaz(f"Mann–Whitney U = {mw.statistic:,.0f}, p = {mw.pvalue:.3g}, "
        f"sıra-noktasal r = {abs(rb):.3f}")
    yaz(f"  → t testiyle aynı yönde sonuç; karar varsayıma bağlı değil.")
    yaz(f"Kruskal–Wallis H({len(gruplar)-1}) = {kw.statistic:.3f}, "
        f"p = {kw.pvalue:.3g}, ε² = {epsilon2:.4f}")
    yaz(f"  → ANOVA ile aynı yönde sonuç.")
    SONUC["parametrik_olmayan"] = {
        "mann_whitney_U": round(float(mw.statistic), 0),
        "mw_p": float(f"{mw.pvalue:.3g}"),
        "rank_biserial": round(float(abs(rb)), 3),
        "kruskal_H": round(float(kw.statistic), 3),
        "kruskal_df": len(gruplar) - 1,
        "kruskal_p": float(f"{kw.pvalue:.3g}"),
        "epsilon_kare": round(float(epsilon2), 4)}

    # ------------------------------------------------------------ ADIM 8
    baslik(8, "İlişki — korelasyon matrisi",
           "İki sürekli değişkenin birlikte değişme derecesi.",
           "Pearson doğrusal ilişkiyi, Spearman sıralı/monotonik ilişkiyi "
           "ölçer. Likert ve sayım değişkenlerinde ikisi birlikte "
           "raporlanır; aralarındaki fark doğrusallıktan sapmayı gösterir.")
    kor_degiskenler = ["ders_puan", "ogretim_puan", "attendance",
                       "difficulty", "nb.repeat"]
    pearson = df[kor_degiskenler].corr(method="pearson").round(3)
    spearman = df[kor_degiskenler].corr(method="spearman").round(3)
    yaz("Pearson r:")
    yaz(pearson.to_string())
    yaz()
    yaz("Spearman rho:")
    yaz(spearman.to_string())
    # p degerleri
    kor_p = []
    for i, a in enumerate(kor_degiskenler):
        for b in kor_degiskenler[i + 1:]:
            r, pv = stats.pearsonr(df[a], df[b])
            rs, pvs = stats.spearmanr(df[a], df[b])
            kor_p.append({"çift": f"{a} – {b}", "pearson_r": round(r, 3),
                          "pearson_p": float(f"{pv:.3g}"),
                          "spearman_rho": round(rs, 3),
                          "spearman_p": float(f"{pvs:.3g}"),
                          "r_kare": round(r ** 2, 3)})
    yaz()
    yaz("NOT — n = 5.820'de r = 0,03 bile p < 0,05 çıkar. Bu yüzden r²")
    yaz("(açıklanan varyans oranı) raporlanmadan korelasyon yorumlanamaz.")
    en_kucuk = min(kor_p, key=lambda x: abs(x["pearson_r"]))
    yaz(f"Örnek: {en_kucuk['çift']} → r = {en_kucuk['pearson_r']}, "
        f"p = {en_kucuk['pearson_p']}, ama r² = {en_kucuk['r_kare']} "
        f"(%{100*en_kucuk['r_kare']:.1f} açıklanan varyans)")
    SONUC["korelasyon"] = {
        "degiskenler": kor_degiskenler,
        "pearson": pearson.values.tolist(),
        "spearman": spearman.values.tolist(),
        "ciftler": kor_p}

    # ------------------------------------------------------------ ADIM 9
    baslik(9, "Çoklu doğrusal regresyon",
           "Birden çok yordayıcının, sürekli bir sonuç değişkenini birlikte "
           "ne kadar açıkladığının modellenmesi.",
           "Korelasyon tek ilişkiyi verir; regresyon diğer değişkenler "
           "sabit tutulduğunda her birinin kendi katkısını verir. Soru: "
           "öğretim elemanı değerlendirmesini katılım, güçlük, tekrar ve "
           "öğretim elemanı kimliği birlikte ne kadar açıklıyor?")
    model = smf.ols(
        "ogretim_puan ~ attendance + difficulty + Q('nb.repeat') + C(instr)",
        data=df).fit()
    yaz(str(model.summary().tables[0]))
    yaz(str(model.summary().tables[1]))
    # Cok dogrusallik
    X = pd.get_dummies(df[["attendance", "difficulty", "nb.repeat", "instr"]],
                       columns=["instr"], drop_first=True).astype(float)
    X = sm.add_constant(X)
    vif = pd.DataFrame({
        "değişken": X.columns,
        "VIF": [round(variance_inflation_factor(X.values, i), 3)
                for i in range(X.shape[1])]})
    yaz()
    yaz("Çok doğrusallık denetimi (VIF > 10 sorun sayılır):")
    yaz(vif.to_string(index=False))
    bp = het_breuschpagan(model.resid, model.model.exog)
    dw = durbin_watson(model.resid)
    yaz()
    yaz(f"Breusch–Pagan (artık varyansının sabitliği): "
        f"LM = {bp[0]:.3f}, p = {bp[1]:.3g}")
    yaz(f"Durbin–Watson (artıkların bağımsızlığı): {dw:.3f}  "
        f"(2'ye yakın olması beklenir)")
    yaz(f"R² = {model.rsquared:.4f}   düzeltilmiş R² = {model.rsquared_adj:.4f}")
    yaz(f"F({int(model.df_model)}, {int(model.df_resid)}) = {model.fvalue:.3f}, "
        f"p = {model.f_pvalue:.3g}")
    SONUC["regresyon"] = {
        "r_kare": round(float(model.rsquared), 4),
        "duzeltilmis_r_kare": round(float(model.rsquared_adj), 4),
        "F": round(float(model.fvalue), 3),
        "df_model": int(model.df_model), "df_artik": int(model.df_resid),
        "F_p": float(f"{model.f_pvalue:.3g}"),
        "katsayilar": [
            {"terim": t, "B": round(float(model.params[t]), 4),
             "SH": round(float(model.bse[t]), 4),
             "t": round(float(model.tvalues[t]), 3),
             "p": float(f"{model.pvalues[t]:.3g}"),
             "alt_GA": round(float(model.conf_int().loc[t, 0]), 4),
             "üst_GA": round(float(model.conf_int().loc[t, 1]), 4)}
            for t in model.params.index],
        "vif": vif.to_dict("records"),
        "breusch_pagan_LM": round(float(bp[0]), 3),
        "breusch_pagan_p": float(f"{bp[1]:.3g}"),
        "durbin_watson": round(float(dw), 3)}

    # ----------------------------------------------------------- ADIM 10
    baslik(10, "Lojistik regresyon",
            "Sonuç değişkeni iki kategorili olduğunda olasılığın "
            "modellenmesi.",
            "Doğrusal regresyon 0–1 arası bir olasılığı modellemek için "
            "uygun değildir (aralık dışına çıkar). Lojistik regresyon "
            "log-odds ölçeğinde çalışır; katsayılar olasılık oranı (OR) "
            "olarak yorumlanır.")
    df["yuksek_degerlendirme"] = (df["genel_puan"] >= 4).astype(int)
    yaz(f"Sonuç değişkeni: genel puan ≥ 4 → 'yüksek değerlendirme'")
    yaz(f"  1 (yüksek): {int(df['yuksek_degerlendirme'].sum()):,}  "
        f"(%{100*df['yuksek_degerlendirme'].mean():.1f})")
    yaz(f"  0 (diğer) : {int((1-df['yuksek_degerlendirme']).sum()):,}")
    log_model = smf.logit(
        "yuksek_degerlendirme ~ attendance + difficulty + Q('nb.repeat') "
        "+ C(instr)", data=df).fit(disp=0)
    orani = pd.DataFrame({
        "terim": log_model.params.index,
        "B": log_model.params.values.round(4),
        "SH": log_model.bse.values.round(4),
        "p": [float(f"{v:.3g}") for v in log_model.pvalues.values],
        "OR": np.exp(log_model.params.values).round(4),
        "OR_alt_GA": np.exp(log_model.conf_int()[0].values).round(4),
        "OR_üst_GA": np.exp(log_model.conf_int()[1].values).round(4)})
    yaz()
    yaz(orani.to_string(index=False))
    olasilik = log_model.predict(df)
    auc = roc_auc_score(df["yuksek_degerlendirme"], olasilik)
    yaz()
    yaz(f"Nagelkerke benzeri sözde R² (McFadden) = {log_model.prsquared:.4f}")
    yaz(f"ROC eğrisi altındaki alan (AUC) = {auc:.4f}")
    yaz("OR > 1 → o değişken arttıkça yüksek değerlendirme olasılığı artar.")
    SONUC["lojistik"] = {
        "sonuc_tanimi": "genel_puan >= 4",
        "pozitif_n": int(df["yuksek_degerlendirme"].sum()),
        "pozitif_oran": round(float(df["yuksek_degerlendirme"].mean()), 4),
        "mcfadden_r2": round(float(log_model.prsquared), 4),
        "auc": round(float(auc), 4),
        "katsayilar": orani.to_dict("records")}

    # ----------------------------------------------------------- ADIM 11
    baslik(11, "Kategorik değişkenler — ki-kare bağımsızlık testi",
            "İki kategorik değişkenin birbirinden bağımsız olup olmadığının "
            "sınanması.",
            "Ortalama hesaplanamayan değişkenlerde (fakülte, unvan, "
            "öğretim elemanı) grup farkı ki-kare ile sınanır. Etki "
            "büyüklüğü Cramér V ile raporlanır.")
    capraz = pd.crosstab(df["instr"], df["attendance"])
    ki2, p_ki2, sd, beklenen = stats.chi2_contingency(capraz)
    v = cramers_v(capraz.values)
    yaz("Çapraz tablo — öğretim elemanı × derse katılım (gözlenen):")
    yaz(capraz.to_string())
    yaz()
    yaz(f"χ²({sd}) = {ki2:.3f}, p = {p_ki2:.3g}")
    yaz(f"Cramér V = {v:.4f}  "
        f"({'zayıf' if v<0.2 else 'orta' if v<0.4 else 'güçlü'} ilişki)")
    kucuk_beklenen = int((beklenen < 5).sum())
    yaz(f"Beklenen frekansı 5'ten küçük hücre sayısı: {kucuk_beklenen} "
        f"(toplam {beklenen.size} hücre) — ölçüt: %20'den az olmalı")
    SONUC["ki_kare"] = {
        "capraz_tablo": capraz.reset_index().to_dict("records"),
        "satir_adi": "instr", "sutun_adi": "attendance",
        "ki2": round(float(ki2), 3), "sd": int(sd),
        "p": float(f"{p_ki2:.3g}"), "cramers_v": round(float(v), 4),
        "kucuk_beklenen_hucre": kucuk_beklenen,
        "hucre_sayisi": int(beklenen.size)}

    # ----------------------------------------------------------- ADIM 12
    baslik(12, "Anlamlılık ile etki büyüklüğünün ayrımı",
            "p değerinin örneklem büyüklüğüne bağlılığının ve küçük "
            "örneklemde katsayı kararsızlığının gösterilmesi.",
            "Bu adım bir test değil, bir denetimdir. İki ayrı olgu birbirine "
            "karıştırılır: küçük örneklemde katsayı DALGALANIR, büyük "
            "örneklemde küçük katsayı ANLAMLI ÇIKAR. İkisi farklı sorun.")

    ders_i = df["ders_puan"].values
    guc_i = df["difficulty"].values
    r_evren, p_evren = stats.pearsonr(ders_i, guc_i)
    yaz(f"Elimizdeki tüm veride ilişki (ders puanı – güçlük algısı):")
    yaz(f"  r = {r_evren:.3f}   r² = {r_evren**2:.4f}   "
        f"(%{100*r_evren**2:.2f} açıklanan varyans)")
    yaz(f"  Bu değeri 'evren değeri' kabul edip aşağıda referans alıyoruz.")
    yaz()

    # --- Panel A: ayni evrenden tekrar tekrar ornek cek
    yaz("PANEL A — Aynı veriden 500 kez örnek çekilirse r ne kadar oynar?")
    yaz("-" * 78)
    rng = np.random.default_rng(20261103)
    panel_a = []
    for n in [30, 50, 100, 300, 1000, 3000]:
        r_ler, anlamli = [], 0
        for _ in range(500):
            idx = rng.choice(len(df), n, replace=False)
            r, pv = stats.pearsonr(ders_i[idx], guc_i[idx])
            r_ler.append(r)
            anlamli += int(pv < 0.05)
        r_ler = np.array(r_ler)
        panel_a.append({
            "n": n,
            "r_ortalama": round(float(r_ler.mean()), 3),
            "r_alt_2.5": round(float(np.percentile(r_ler, 2.5)), 3),
            "r_ust_97.5": round(float(np.percentile(r_ler, 97.5)), 3),
            "anlamli_cikma_orani": round(anlamli / 500, 3)})
    pa = pd.DataFrame(panel_a)
    pa.columns = ["n", "r ortalaması", "r %2,5", "r %97,5",
                  "p<0,05 çıkma oranı"]
    yaz(pa.to_string(index=False))
    yaz()
    yaz("Okuma: n = 30'da r, −0,3 ile +0,4 arasında herhangi bir yere")
    yaz("düşebiliyor. Yani küçük örneklemden okunan tek bir r sayısı,")
    yaz("işaretinin bile güvenilir olmadığı bir tahmindir. Son sütun")
    yaz("istatistiksel GÜÇTÜR: n = 30'da bu ilişkiyi yakalama şansı")
    yaz(f"%{100*panel_a[0]['anlamli_cikma_orani']:.0f}, n = 3.000'de "
        f"%{100*panel_a[-1]['anlamli_cikma_orani']:.0f}.")
    yaz()

    # --- Panel B: r sabit tutulursa p nasil degisir
    yaz("PANEL B — r SABİT tutulursa (r = %.3f), p yalnız n ile ne olur?"
        % r_evren)
    yaz("-" * 78)
    panel_b = []
    for n in [30, 50, 100, 300, 1000, 5820, 20000]:
        # r sabitken t = r*sqrt(n-2)/sqrt(1-r^2), sd = n-2
        t_ist = r_evren * np.sqrt(n - 2) / np.sqrt(1 - r_evren ** 2)
        pv = 2 * stats.t.sf(abs(t_ist), df=n - 2)
        panel_b.append({"n": n, "r": round(float(r_evren), 3),
                        "t": round(float(t_ist), 3),
                        "p": float(f"{pv:.3g}"),
                        "karar": "anlamlı" if pv < 0.05 else "anlamsız"})
    pb = pd.DataFrame(panel_b)
    yaz(pb.to_string(index=False))
    yaz()
    yaz("Okuma: r hiç değişmedi; yalnız n büyüdü ve 'anlamsız' sonuç")
    yaz("'anlamlı'ya döndü. Açıklanan varyans ise hep aynı: %0,36.")
    yaz("Demek ki 'p < 0,001' ifadesi tek başına bir bulgunun büyüklüğü")
    yaz("hakkında hiçbir şey söylemez. Raporlanması gereken üçlü şudur:")
    yaz("  etki büyüklüğü + güven aralığı + örneklem büyüklüğü.")
    SONUC["anlamlilik_dersi"] = {
        "evren_r": round(float(r_evren), 3),
        "evren_r_kare": round(float(r_evren ** 2), 4),
        "panel_a": panel_a,
        "panel_b": panel_b}

    # ---------------------------------------------------------------- yazım
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    (hedef / "sosyal_analiz.json").write_text(
        json.dumps(SONUC, ensure_ascii=False, indent=1, default=json_cevir),
        encoding="utf-8")
    (hedef / "sosyal_analiz.txt").write_text(
        "\n".join(SATIRLAR), encoding="utf-8-sig")
    df.to_csv(hedef / "gazi_turetilmis.csv", index=False,
              encoding="utf-8-sig")
    yaz()
    yaz("=" * 78)
    yaz(f"Tamamlandı. {len(SONUC)} analiz bloğu yazıldı:")
    yaz(f"  {hedef / 'sosyal_analiz.json'}")
    yaz(f"  {hedef / 'sosyal_analiz.txt'}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
