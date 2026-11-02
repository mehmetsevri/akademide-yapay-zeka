# -*- coding: utf-8 -*-
"""
15 — Kimya örneği: adsorpsiyon verisinin analizi

Bölüm 7'deki doldurulmuş analiz planı isteminin koşturulmuş hâli.

Adımlar:
  0. İlk kurulum ve neden işe yaramadığı  (öğretici adım)
  1. Varsayım denetimi
  2. Bloklanmış ANOVA: adsorban × pH × sıcaklık, derişim ve süre blok
  3. Etki büyüklüğü (kısmi eta kare) ve post hoc (Tukey HSD)
  4. Langmuir ve Freundlich izotermlerinin karşılaştırılması
  5. Şüpheli dönem için duyarlılık analizi

Kullanım:
  python 15_analiz_adsorpsiyon.py <veri_klasörü> <çıktı_klasörü>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from scipy.optimize import curve_fit

# İlgi konusu üç faktör tam etkileşimli; başlangıç derişimi ve temas
# süresi ana etki olarak modelde (blok). Neden böyle: bu ikisi q'yu
# güçlü biçimde belirler ama araştırma sorusunun konusu değildir.
# Modele konmazlarsa varyansları hata terimine gider ve bütün F
# oranlarını bastırır — Adım 0 bunu sayıyla gösteriyor.
FORMUL = ("q_mgG ~ C(adsorban) * C(pH) * C(sicaklik_C)"
          " + C(baslangic_derisim_mgL) + C(temas_suresi_dk)")
FORMUL_EKSIK = "q_mgG ~ C(adsorban) * C(pH) * C(sicaklik_C)"

# Veriyi üreten modelin GERÇEK parametreleri (13_adsorpsiyon_veri_uret.py).
# Gerçek bir çalışmada bunlar bilinmez; sentetik veride bilinir ve bu,
# tahmin yönteminin ne kadar isabetli olduğunu ölçmeyi sağlar.
# pH 7, 45 °C, 120 dk koşulunda: KL = KL_temel × 1,00 × 1,22 × 1,00
GERCEK = {"cay_posasi": {"qmax": 148.0, "KL": 0.055 * 1.22},
          "ticari": {"qmax": 176.0, "KL": 0.082 * 1.22}}

OKUNUR = {
    "C(adsorban)": "adsorban",
    "C(pH)": "pH",
    "C(sicaklik_C)": "sıcaklık",
    "C(baslangic_derisim_mgL)": "başlangıç derişimi (blok)",
    "C(temas_suresi_dk)": "temas süresi (blok)",
    "C(adsorban):C(pH)": "adsorban × pH",
    "C(adsorban):C(sicaklik_C)": "adsorban × sıcaklık",
    "C(pH):C(sicaklik_C)": "pH × sıcaklık",
    "C(adsorban):C(pH):C(sicaklik_C)": "adsorban × pH × sıcaklık",
    "Residual": "Hata",
}


def json_cevir(nesne):
    if isinstance(nesne, np.integer):
        return int(nesne)
    if isinstance(nesne, np.floating):
        return float(nesne)
    if isinstance(nesne, np.ndarray):
        return nesne.tolist()
    if isinstance(nesne, np.bool_):
        return bool(nesne)
    raise TypeError(f"JSON'a çevrilemedi: {type(nesne)}")


def ts(x, b=3):
    """Türkçe ondalık ayırıcıyla biçimler: 1234.5 → 1.234,500"""
    return (f"{x:,.{b}f}".replace(",", "\x00").replace(".", ",")
            .replace("\x00", "."))


def anova_tablosu(df, formul):
    """Type II kareler toplamıyla ANOVA ve kısmi eta kare.

    Type II seçildi çünkü tasarım dengesiz (bazı koşullarda iki tekrar
    kaldı). Type I terimlerin modele giriş sırasına duyarlıdır; Type II
    her terimi, kendisini içermeyen bütün terimler modelde varken
    sınar, bu yüzden sıradan bağımsızdır.
    """
    model = smf.ols(formul, data=df).fit()
    tablo = sm.stats.anova_lm(model, typ=2)
    hata_kt = float(tablo.loc["Residual", "sum_sq"])
    tablo["kismi_eta_kare"] = tablo["sum_sq"] / (tablo["sum_sq"] + hata_kt)
    tablo.loc["Residual", "kismi_eta_kare"] = np.nan
    tablo = tablo.reset_index().rename(columns={"index": "kaynak_ham"})
    tablo["kaynak"] = tablo["kaynak_ham"].map(OKUNUR)
    return model, tablo


def tukey_hsd(df, faktor, mse, sd_hata, bagimli="q_mgG"):
    """Tukey HSD: bütün ikili karşılaştırmalar, aile düzeyinde düzeltilmiş.

    mse ve sd_hata, BLOKLANMIŞ ANOVA modelinden gelir. Bu önemli:
    post hoc sınaması kendi hata terimini grupların içinden yeniden
    hesaplarsa, bloklanan derişim varyansı tekrar hataya karışır ve
    ANOVA ile çelişen sonuçlar üretir. Adım 0'da gösterilen tuzağın
    aynısı post hoc aşamasında da kurulabilir.

    Dengesiz tasarım için standart hata, iki grubun örneklem
    büyüklüklerinin harmonik ortalamasıyla kurulur (Tukey-Kramer).
    """
    gruplar = [(ad, g[bagimli].to_numpy(float))
               for ad, g in df.groupby(faktor, observed=True)]
    k = len(gruplar)
    cikti = []
    for i in range(k):
        for j in range(i + 1, k):
            ad1, v1 = gruplar[i]
            ad2, v2 = gruplar[j]
            fark = v1.mean() - v2.mean()
            se = np.sqrt(mse / 2 * (1 / len(v1) + 1 / len(v2)))
            q = abs(fark) / se
            cikti.append({
                "grup_1": str(ad1), "grup_2": str(ad2),
                "n_1": len(v1), "n_2": len(v2),
                "ortalama_fark": float(fark), "q": float(q),
                "p_duzeltilmis": float(
                    stats.studentized_range.sf(q, k, sd_hata))})
    return pd.DataFrame(cikti)


def _langmuir(ce, qmax, kl):
    return qmax * kl * ce / (1 + kl * ce)


def _freundlich(ce, kf, n):
    return kf * ce ** (1 / n)


def _uyum_olcutleri(q, tahmin, k):
    """R², düzeltilmiş R² ve AIC.

    AIC, farklı sayıda parametreli modelleri karşılaştırmak için
    gerekir. Burada iki modelin de iki parametresi var, bu yüzden AIC
    sıralaması R² sıralamasıyla aynı çıkar; yine de hesaplanıyor çünkü
    üçüncü bir model (örneğin Sips, üç parametreli) eklendiğinde R²
    tek başına yanıltır — parametre eklemek R²'yi her zaman yükseltir.
    """
    n = len(q)
    kalinti = q - tahmin
    sse = float((kalinti ** 2).sum())
    sst = float(((q - q.mean()) ** 2).sum())
    r2 = 1 - sse / sst
    return {"R2": r2,
            "duzeltilmis_R2": 1 - (1 - r2) * (n - 1) / (n - k - 1),
            "AIC": float(n * np.log(sse / n) + 2 * k),
            "RMSE": float(np.sqrt(sse / n))}


def izoterm_uyumu(alt):
    """Langmuir ve Freundlich'i DOĞRUSAL OLMAYAN en küçük karelerle
    uydurur ve doğrusallaştırılmış uyumla karşılaştırır.

    Langmuir   : q = qmax·KL·Ce / (1 + KL·Ce)
    Freundlich : q = KF · Ce^(1/n)

    Neden doğrusal olmayan uyum: doğrusallaştırma, örneğin Langmuir'i
    Ce/q = 1/(qmax·KL) + Ce/qmax biçimine sokar. q'daki eşit dağılmış
    ölçüm hatası Ce/q'da eşit dağılmaz — küçük q değerlerinde büyür.
    En küçük kareler her noktaya eşit ağırlık verdiği için düşük
    derişimli noktalar hak ettiğinden çok ağırlık kazanır ve qmax
    yanlı çıkar.

    Doğrusallaştırılmış uyum yine de hesaplanıyor: iki yöntemin
    parametre tahminleri arasındaki fark, bu sınırın neden konulduğunu
    sayıyla gösteriyor.
    """
    ce = alt["denge_derisim_mgL"].to_numpy(float)
    q = alt["q_mgG"].to_numpy(float)
    gecerli = (ce > 0) & (q > 0)
    ce, q = ce[gecerli], q[gecerli]
    sirali = np.argsort(ce)
    ce, q = ce[sirali], q[sirali]

    # --- doğrusal olmayan uyum (yeğlenen yöntem) ---------------------
    # Başlangıç tahminleri doğrusallaştırılmış uyumdan geliyor; bu,
    # curve_fit'in yakınsamasını hızlandırır ve yerel enküçüğe
    # takılma olasılığını düşürür.
    lin_l = stats.linregress(ce, ce / q)
    lin_f = stats.linregress(np.log(ce), np.log(q))
    bas_l = [max(1 / lin_l.slope, q.max()), max(lin_l.slope / lin_l.intercept,
                                                1e-3)]
    bas_f = [np.exp(lin_f.intercept), 1 / lin_f.slope]

    pl, kov_l = curve_fit(_langmuir, ce, q, p0=bas_l, maxfev=20000,
                          bounds=([q.max(), 1e-6], [np.inf, np.inf]))
    pf, kov_f = curve_fit(_freundlich, ce, q, p0=bas_f, maxfev=20000,
                          bounds=([1e-6, 1e-6], [np.inf, np.inf]))
    ol_l = _uyum_olcutleri(q, _langmuir(ce, *pl), 2)
    ol_f = _uyum_olcutleri(q, _freundlich(ce, *pf), 2)

    # Parametre güven aralıkları. curve_fit'in döndürdüğü kovaryans
    # matrisinin köşegeni varyanslardır; t dağılımı kullanılıyor çünkü
    # örneklem küçük (n = 8-9).
    t_kritik = float(stats.t.ppf(0.975, len(q) - 2))

    def _aralik(p_, kov):
        hata = np.sqrt(np.diag(kov))
        return [[float(v - t_kritik * h), float(v + t_kritik * h)]
                for v, h in zip(p_, hata)]

    ga_l, ga_f = _aralik(pl, kov_l), _aralik(pf, kov_f)

    # Doğrusallaştırılmış uyumun ÖZGÜN ölçekteki R²'si. Dönüştürülmüş
    # ölçekte hesaplanan R² (0,96 gibi) iki yöntem arasında
    # karşılaştırılamaz; aynı ölçekte bakmak gerekir.
    lin_qmax, lin_kl = 1 / lin_l.slope, lin_l.slope / lin_l.intercept
    lin_kf, lin_n = np.exp(lin_f.intercept), 1 / lin_f.slope
    ol_lin_l = _uyum_olcutleri(q, _langmuir(ce, lin_qmax, lin_kl), 2)
    ol_lin_f = _uyum_olcutleri(q, _freundlich(ce, lin_kf, lin_n), 2)

    return {
        "langmuir": {"qmax_mgG": float(pl[0]), "KL_Lmg": float(pl[1]),
                     "qmax_GA": ga_l[0], "KL_GA": ga_l[1], **ol_l},
        "freundlich": {"KF": float(pf[0]), "n": float(pf[1]),
                       "KF_GA": ga_f[0], "n_GA": ga_f[1], **ol_f},
        "daha_iyi": "Langmuir" if ol_l["AIC"] < ol_f["AIC"] else "Freundlich",
        "AIC_farki": abs(ol_l["AIC"] - ol_f["AIC"]),
        # Yalnız karşılaştırma için: doğrusallaştırılmış uyumun verdiği
        # parametreler. Raporlanan değerler yukarıdakilerdir.
        "dogrusallastirilmis": {
            "langmuir_qmax": float(lin_qmax), "langmuir_KL": float(lin_kl),
            "freundlich_KF": float(lin_kf), "freundlich_n": float(lin_n),
            "langmuir_R2_ozgun": ol_lin_l["R2"],
            "freundlich_R2_ozgun": ol_lin_f["R2"],
            "langmuir_AIC_ozgun": ol_lin_l["AIC"],
            "freundlich_AIC_ozgun": ol_lin_f["AIC"],
            "daha_iyi": ("Langmuir" if ol_lin_l["AIC"] < ol_lin_f["AIC"]
                         else "Freundlich")},
        "n_nokta": int(len(ce)),
    }


def tablo_yaz(satir, tablo):
    satir.append(f"{'Kaynak':<28}{'KT':>11}{'sd':>5}{'F':>12}"
                 f"{'p':>10}{'η²p':>8}")
    for _, s in tablo.iterrows():
        f_m = "—" if pd.isna(s["F"]) else ts(s["F"], 2)
        p_m = ("—" if pd.isna(s["PR(>F)"]) else
               "<0,001" if s["PR(>F)"] < 0.001 else ts(s["PR(>F)"], 3))
        e_m = ("—" if pd.isna(s["kismi_eta_kare"])
               else ts(s["kismi_eta_kare"], 3))
        satir.append(f"{s['kaynak']:<28}{ts(s['sum_sq'], 1):>11}"
                     f"{int(s['df']):>5}{f_m:>12}{p_m:>10}{e_m:>8}")


def main(veri_klasoru: str, cikti_klasoru: str) -> None:
    df = pd.read_csv(pathlib.Path(veri_klasoru) / "adsorpsiyon_temiz.csv",
                     encoding="utf-8-sig")
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    sonuc = {}
    satir = ["ADSORPSİYON VERİSİ — ANALİZ SONUÇLARI", "=" * 74, "",
             "!!! SENTETİK VERİ. Bu sayılar bir bulgu değil, yöntem",
             "    örneğidir. Hiçbiri alıntılanamaz. !!!", "",
             f"Gözlem sayısı: {len(df)}",
             "Tasarım: 2 adsorban × 3 pH × 2 sıcaklık × 3 derişim × 2 süre",
             ""]

    # --- Adım 0: ilk kurulum neden işe yaramadı -------------------------
    satir += ["", "ADIM 0 — İLK KURULUM ve NEDEN İŞE YARAMADIĞI", "-" * 74, "",
              "Analizi ilk kurduğumuzda yalnız ilgi konusu üç faktörü",
              "modele koyduk: adsorban, pH, sıcaklık. Başlangıç derişimi",
              "ile temas süresini dışarıda bıraktık — 'onlar araştırma",
              "sorusunun konusu değil' diye düşündük. Sonuç şöyle çıktı:",
              ""]
    _, tablo_eksik = anova_tablosu(df, FORMUL_EKSIK)
    tablo_yaz(satir, tablo_eksik)
    satir += ["",
              "Hiçbir etki anlamlı değil, bütün etki büyüklükleri sıfıra",
              "yakın. Oysa çay posası ile ticari kömürün farklı",
              "davrandığını betimsel tabloda zaten görüyorduk.", "",
              "Nedeni şu: q, başlangıç derişimine çok güçlü bağlıdır.",
              "25 mg/L'de yaklaşık 11 mg/g, 100 mg/L'de yaklaşık 45 mg/g",
              "tutunuyor. Bu farkı modele koymazsanız, o varyans 'hata'",
              "sayılır ve F oranının paydasını şişirir. Payda şişince",
              "bütün F değerleri birin altına düşer.", "",
              "Çözüm, deney tasarımı dilinde BLOKLAMA: kontrol edilen",
              "ama ilgi konusu olmayan faktörler modele ana etki olarak",
              "girer, etkileşimleri sorulmaz. Böylece varyansları hata",
              "teriminden çıkar. Aşağıdaki bütün adımlar bu kurulumla.", ""]
    sonuc["adim0_eksik_model"] = tablo_eksik[
        ["kaynak", "sum_sq", "df", "F", "PR(>F)", "kismi_eta_kare"]
    ].to_dict("records")

    model, tablo = anova_tablosu(df, FORMUL)

    # --- Adım 1: varsayımlar --------------------------------------------
    satir += ["", "ADIM 1 — VARSAYIM DENETİMİ", "-" * 74, "",
              "Neden bu adım: ANOVA, hata teriminin yaklaşık normal",
              "dağıldığını ve grupların varyanslarının benzer olduğunu",
              "varsayar. Varsayım tutmazsa F de p de güvenilmez olur.", ""]
    sw = stats.shapiro(model.resid)
    satir += [f"Shapiro-Wilk (model artıkları): W = {ts(sw.statistic, 4)}, "
              f"p = {ts(sw.pvalue, 4)}",
              ("  → Artıklar normallikten sapıyor."
               if sw.pvalue < 0.05 else
               "  → Artıklar normallik varsayımıyla uyumlu.")]
    # Şüpheli dönem artıkları normalliği ne kadar bozuyor?
    alt = df[~df["supheli_donem"]]
    model_alt, tablo_alt = anova_tablosu(alt, FORMUL)
    sw_alt = stats.shapiro(model_alt.resid)
    satir += ["",
              "Şüpheli dönem dışarıda bırakıldığında aynı sınama:",
              f"  W = {ts(sw_alt.statistic, 4)}, p = {ts(sw_alt.pvalue, 4)}",
              f"  W değeri {ts(sw.statistic, 3)} → {ts(sw_alt.statistic, 3)}",
              "  yükseliyor. Yani normallikten sapmanın büyük bölümü",
              "  cihaz arızası dönemindeki kaymış okumalardan geliyor.",
              "  Sapma hâlâ anlamlı; n = 201 gibi örneklemlerde",
              "  Shapiro-Wilk küçük sapmaları da yakalar. F sınaması",
              "  bu ölçekte normallik sapmalarına karşı dayanıklıdır,",
              "  ama bulgular Adım 5'te şüpheli dönem olmadan da",
              "  yineleniyor.", ""]
    gruplar = [g["q_mgG"].to_numpy(float) for _, g in
               df.groupby(["adsorban", "pH", "sicaklik_C",
                           "baslangic_derisim_mgL"], observed=True)]
    lev = stats.levene(*gruplar, center="median")
    satir += [f"Levene (36 hücre, medyan merkezli): W = {ts(lev.statistic, 3)}"
              f", p = {ts(lev.pvalue, 4)}",
              ("  → Varyanslar eşit DEĞİL."
               if lev.pvalue < 0.05 else
               "  → Varyanslar eşit varsayımıyla uyumlu."), "",
              "Sapmanın nereden geldiğini aramak gerekiyor; 'varsayım",
              "tutmadı' demek tek başına bir şey öğretmez. Aynı sınamayı",
              "her derişim düzeyi İÇİNDE ayrı ayrı yapalım:", ""]
    lev_blok = {}
    for c0, g in df.groupby("baslangic_derisim_mgL", observed=True):
        gr = [x["q_mgG"].to_numpy(float) for _, x in
              g.groupby(["adsorban", "pH", "sicaklik_C"], observed=True)]
        lv = stats.levene(*gr, center="median")
        ss = g.groupby(["adsorban", "pH", "sicaklik_C"],
                       observed=True)["q_mgG"].std()
        lev_blok[float(c0)] = {"W": float(lv.statistic), "p": float(lv.pvalue),
                               "ss_min": float(ss.min()),
                               "ss_maks": float(ss.max())}
        satir.append(f"  C0 = {ts(c0, 0):>3} mg/L: W = {ts(lv.statistic, 3)}, "
                     f"p = {ts(lv.pvalue, 4)} · hücre SS aralığı "
                     f"{ts(ss.min(), 2)}-{ts(ss.max(), 2)} mg/g")

    # Varyansın ortalamayla büyüyüp büyümediğini doğrudan sınayalım
    hucre = (df.groupby(["adsorban", "pH", "sicaklik_C",
                         "baslangic_derisim_mgL", "temas_suresi_dk"],
                        observed=True)["q_mgG"]
             .agg(["mean", "std"]).dropna())
    r_ms = stats.pearsonr(hucre["mean"], hucre["std"])
    satir += ["",
              "Hücre standart sapması, hücre ortalamasıyla birlikte",
              f"büyüyor mu: r = {ts(r_ms.statistic, 3)}, "
              f"p = {ts(r_ms.pvalue, 4)} (n = {len(hucre)} hücre).", "",
              "Tablo şunu söylüyor: 25 mg/L'de hücre içi standart sapma "
              f"{ts(lev_blok[25.0]['ss_min'], 2)}-"
              f"{ts(lev_blok[25.0]['ss_maks'], 2)} mg/g iken,",
              f"100 mg/L'de {ts(lev_blok[100.0]['ss_min'], 2)}-"
              f"{ts(lev_blok[100.0]['ss_maks'], 2)} mg/g'a çıkıyor.",
              "Yani varyans eşitsizliği karşılaştırdığımız gruplar arasında",
              "değil, derişim düzeyleri arasında. Nedeni ölçüm hatasının",
              "çarpımsal olması: spektrofotometre okuması yüzde cinsinden",
              "sapar, mutlak cinsten değil. Yüksek derişimde aynı yüzde",
              "daha büyük bir mg/g farkı demektir.", "",
              "Bu, modeli kurma biçimimizi doğruluyor: derişim modelde",
              "blok olarak duruyor, dolayısıyla her derişim düzeyi kendi",
              "içinde karşılaştırılıyor. Blok içi Levene sınamaları üç",
              "düzeyde de ya anlamsız ya sınırda; karşılaştırmaların",
              "yapıldığı yerde varyanslar yeterince benzer.", ""]

    sonuc["varsayim"] = {
        "shapiro_W": float(sw.statistic), "shapiro_p": float(sw.pvalue),
        "shapiro_W_haric": float(sw_alt.statistic),
        "shapiro_p_haric": float(sw_alt.pvalue),
        "levene_W": float(lev.statistic), "levene_p": float(lev.pvalue),
        "levene_blok_ici": lev_blok,
        "ortalama_ss_korelasyon_r": float(r_ms.statistic),
        "ortalama_ss_korelasyon_p": float(r_ms.pvalue),
        "model_R2": float(model.rsquared)}

    # --- Adım 2-3: ANOVA ------------------------------------------------
    satir += ["", "ADIM 2-3 — BLOKLANMIŞ ANOVA ve ETKİ BÜYÜKLÜĞÜ",
              "-" * 74, "",
              "Neden bu test: üç faktörün etkisini ayrı ayrı VE birlikte",
              "sınamak gerekiyor. Üç ayrı t testi etkileşimi göremez;",
              "oysa 'ticari kömürün üstünlüğü pH'a bağlı mı' sorusu tam",
              "olarak bir etkileşim sorusudur.", "",
              f"Model: {FORMUL}",
              f"Açıklanan varyans: R² = {ts(model.rsquared, 4)}", ""]
    tablo_yaz(satir, tablo)
    satir += ["", "Kısmi eta kare eşikleri (Cohen 1988): 0,01 küçük · "
              "0,06 orta · 0,14 büyük", ""]
    # Anlamlı terimleri okunur biçimde özetle
    anlamli = tablo[(tablo["PR(>F)"] < 0.05)
                    & (~tablo["kaynak_ham"].str.contains("baslangic|temas"))]
    satir += ["Anlamlı bulunan terimler (bloklar hariç):"]
    for _, s in anlamli.iterrows():
        satir.append(f"  {s['kaynak']}: F({int(s['df'])}, "
                     f"{int(tablo.loc[tablo['kaynak'] == 'Hata', 'df'].iloc[0])})"
                     f" = {ts(s['F'], 2)}, "
                     f"p {'< 0,001' if s['PR(>F)'] < 0.001 else '= ' + ts(s['PR(>F)'], 3)}"
                     f", η²p = {ts(s['kismi_eta_kare'], 3)}")
    satir += ["",
              "Etkileşim terimi anlamlı çıktığında ana etkiler tek başına",
              "yorumlanmaz. adsorban × pH anlamlı olduğu için 'ticari",
              "kömür daha iyidir' demek eksik kalır; doğru ifade 'ticari",
              "kömürün üstünlüğü pH düzeyine göre değişir'.", ""]
    sonuc["anova"] = tablo[
        ["kaynak", "sum_sq", "df", "F", "PR(>F)", "kismi_eta_kare"]
    ].to_dict("records")

    # Etkileşimi sayıyla göster: her pH'ta iki adsorban arasındaki fark
    satir += ["Etkileşimin okunuşu — pH düzeyine göre adsorban farkı:", ""]
    etkilesim = []
    for ph, g in df.groupby("pH", observed=True):
        a = g[g["adsorban"] == "cay_posasi"]["q_mgG"].mean()
        b = g[g["adsorban"] == "ticari"]["q_mgG"].mean()
        satir.append(f"  pH {ts(ph, 0)}: çay posası {ts(a, 2)} mg/g · "
                     f"ticari {ts(b, 2)} mg/g · fark {ts(b - a, 2)} mg/g")
        etkilesim.append({"pH": float(ph), "cay_posasi": float(a),
                          "ticari": float(b), "fark": float(b - a)})
    satir += ["",
              "Farkın pH 3'te 0,04 mg/g'dan pH 10'da 0,94 mg/g'a çıkması",
              "etkileşimin yönünü gösteriyor: ticari kömürün üstünlüğü",
              "yalnız yüksek pH'ta belirginleşiyor. Ortalamalar üç",
              "derişim ve iki süre üzerinden alındığı için mutlak",
              "büyüklükler bastırılmış görünür; sınamanın kendisi",
              "bloklanmış modelde yapıldı.", ""]
    sonuc["etkilesim_pH_adsorban"] = etkilesim

    mse_model = float(model.mse_resid)
    sd_hata_model = int(model.df_resid)
    tk = tukey_hsd(df, "pH", mse_model, sd_hata_model)
    satir += ["Post hoc — pH düzeyleri arası Tukey HSD:",
              "(pH üç düzeyli; ANOVA 'bir fark var' der, hangi ikilinin",
              " farklı olduğunu söylemez. Hata terimi bloklanmış modelden",
              f" alındı: KO_hata = {ts(mse_model, 4)}, sd = {sd_hata_model}.)",
              ""]
    for _, s in tk.iterrows():
        p_m = ("<0,001" if s["p_duzeltilmis"] < 0.001
               else ts(s["p_duzeltilmis"], 3))
        satir.append(f"  pH {s['grup_1']} - pH {s['grup_2']}: "
                     f"fark = {ts(s['ortalama_fark'], 2)} mg/g, "
                     f"q = {ts(s['q'], 2)}, p = {p_m}")
    satir.append("")
    sonuc["tukey_pH"] = tk.to_dict("records")

    # --- Adım 4: izotermler ---------------------------------------------
    satir += ["", "ADIM 4 — İZOTERM MODELLERİ", "-" * 74, "",
              "Neden bu adım: ANOVA 'fark var mı' sorusunu yanıtlar ama",
              "mekanizma hakkında bir şey söylemez. İzoterm uyumu,",
              "tutunmanın tek katmanlı mı (Langmuir) yoksa heterojen",
              "yüzeyde mi (Freundlich) olduğuna dair kanıt sunar.", "",
              "Her iki model pH 7, 45 °C, 120 dk koşulunda uyduruldu;",
              "izoterm tanımı gereği tek sıcaklık ve tek pH gerektirir.",
              ""]
    sonuc["izoterm"] = {}
    for ads, ad_g in (("cay_posasi", "Çay posası"), ("ticari", "Ticari kömür")):
        a = df[(df["adsorban"] == ads) & (df["pH"] == 7)
               & (df["sicaklik_C"] == 45) & (df["temas_suresi_dk"] == 120)]
        iz = izoterm_uyumu(a)
        sonuc["izoterm"][ads] = iz
        d = iz["dogrusallastirilmis"]
        satir += [f"{ad_g} (n = {iz['n_nokta']} nokta):",
                  f"  Langmuir  : qmax = {ts(iz['langmuir']['qmax_mgG'], 1)}"
                  f" mg/g · KL = {ts(iz['langmuir']['KL_Lmg'], 4)} L/mg",
                  f"              R² = {ts(iz['langmuir']['R2'], 4)} · "
                  f"AIC = {ts(iz['langmuir']['AIC'], 1)} · "
                  f"RMSE = {ts(iz['langmuir']['RMSE'], 2)} mg/g",
                  f"  Freundlich: KF = {ts(iz['freundlich']['KF'], 2)} · "
                  f"n = {ts(iz['freundlich']['n'], 2)}",
                  f"              R² = {ts(iz['freundlich']['R2'], 4)} · "
                  f"AIC = {ts(iz['freundlich']['AIC'], 1)} · "
                  f"RMSE = {ts(iz['freundlich']['RMSE'], 2)} mg/g",
                  f"  Daha iyi uyan: {iz['daha_iyi']} "
                  f"(AIC farkı {ts(iz['AIC_farki'], 1)})", ""]

    satir += ["", "Doğrusallaştırma neden önerilmedi", "", ]
    # (a) Ölçek karışıklığı
    satir += ["(a) Dönüştürülmüş ölçekteki R² karşılaştırılamaz.", "",
              "Doğrusallaştırılmış uyumun R²'si, dönüştürülmüş değişken",
              "üzerinde hesaplanır: Langmuir için Ce/q, Freundlich için",
              "ln q. Bunlar farklı şeyleri ölçer; iki R² aynı tabloda",
              "yan yana konamaz. Aynı parametrelerle özgün ölçekte",
              "(mg/g) yeniden hesaplandığında tablo şöyle:", "",
              f"{'Adsorban':<14}{'yöntem':<22}{'Langmuir R²':>13}"
              f"{'Freundlich R²':>15}{'seçim':>13}"]
    for ads, ad_g in (("cay_posasi", "Çay posası"), ("ticari", "Ticari")):
        iz = sonuc["izoterm"][ads]
        d = iz["dogrusallastirilmis"]
        satir.append(f"{ad_g:<14}{'doğrusal olmayan':<22}"
                     f"{ts(iz['langmuir']['R2'], 4):>13}"
                     f"{ts(iz['freundlich']['R2'], 4):>15}"
                     f"{iz['daha_iyi']:>13}")
        satir.append(f"{'':<14}{'doğrusallaştırılmış':<22}"
                     f"{ts(d['langmuir_R2_ozgun'], 4):>13}"
                     f"{ts(d['freundlich_R2_ozgun'], 4):>15}"
                     f"{d['daha_iyi']:>13}")
    satir += ["",
              "Özgün ölçeğe getirildiğinde iki yöntem de Langmuir'i",
              "seçiyor. Dönüştürülmüş ölçekteki R² ile bakılsaydı",
              "Freundlich kazanıyordu — yani sonucu değiştiren şey",
              "modelin kendisi değil, R²'nin hangi ölçekte",
              "hesaplandığıydı.", ""]

    # (b) Parametre yanlılığı
    satir += ["(b) Doğrusallaştırma parametreleri kaydırıyor.", "",
              f"{'Adsorban':<14}{'Parametre':<12}{'doğ. olmayan':>14}"
              f"{'doğrusallaş.':>14}{'fark':>9}"]
    for ads, ad_g in (("cay_posasi", "Çay posası"), ("ticari", "Ticari")):
        iz = sonuc["izoterm"][ads]
        d = iz["dogrusallastirilmis"]
        for ad_p, dogru, lin in (
                ("qmax (mg/g)", iz["langmuir"]["qmax_mgG"], d["langmuir_qmax"]),
                ("KL (L/mg)", iz["langmuir"]["KL_Lmg"], d["langmuir_KL"]),
                ("KF", iz["freundlich"]["KF"], d["freundlich_KF"]),
                ("n", iz["freundlich"]["n"], d["freundlich_n"])):
            satir.append(f"{ad_g if ad_p.startswith('qmax') else '':<14}"
                         f"{ad_p:<12}{ts(dogru, 3):>14}{ts(lin, 3):>14}"
                         f"{'%' + ts((lin - dogru) / dogru * 100, 1):>9}")
    satir += ["",
              "q'daki eşit dağılmış ölçüm hatası Ce/q'ya taşındığında",
              "küçük q değerlerinde büyür. En küçük kareler her noktaya",
              "eşit ağırlık verdiği için düşük derişimli noktalar hak",
              "ettiğinden fazla ağırlık kazanır.", ""]

    # (c) Sentetik verinin sağladığı denetim
    satir += ["(c) Tahminler gerçek değerlere ne kadar yakın?", "",
              "Bu veri sentetik olduğu için üretim modelinin gerçek",
              "parametrelerini biliyoruz. Gerçek bir çalışmada bu denetim",
              "yapılamaz; burada yapılabiliyor ve öğretici bir şey",
              "gösteriyor.", "",
              f"{'Adsorban':<14}{'Parametre':<12}{'gerçek':>10}"
              f"{'tahmin':>10}{'%95 güven aralığı':>24}{'kapsıyor mu':>13}"]
    kapsama = []
    for ads, ad_g in (("cay_posasi", "Çay posası"), ("ticari", "Ticari")):
        iz = sonuc["izoterm"][ads]
        for ad_p, anahtar, ga_anahtar in (
                ("qmax (mg/g)", "qmax", "qmax_GA"), ("KL (L/mg)", "KL", "KL_GA")):
            gercek = GERCEK[ads][anahtar]
            tahmin = iz["langmuir"]["qmax_mgG" if anahtar == "qmax"
                                    else "KL_Lmg"]
            alt_s, ust_s = iz["langmuir"][ga_anahtar]
            icinde = alt_s <= gercek <= ust_s
            kapsama.append({"adsorban": ads, "parametre": ad_p,
                            "gercek": gercek, "tahmin": tahmin,
                            "ga": [alt_s, ust_s], "kapsiyor": icinde})
            b = 1 if anahtar == "qmax" else 4
            satir.append(
                f"{ad_g if anahtar == 'qmax' else '':<14}{ad_p:<12}"
                f"{ts(gercek, b):>10}{ts(tahmin, b):>10}"
                f"{'[' + ts(alt_s, b) + ' – ' + ts(ust_s, b) + ']':>24}"
                f"{('evet' if icinde else 'HAYIR'):>13}")
    sonuc["gercek_karsilastirma"] = kapsama
    # Çay posasının gözlenen denge derişimi aralığı ve qmax güven
    # aralığının göreli genişliği — iddia metne elle yazılmıyor.
    cp = df[(df["adsorban"] == "cay_posasi") & (df["pH"] == 7)
            & (df["sicaklik_C"] == 45) & (df["temas_suresi_dk"] == 120)]
    ce_alt, ce_ust = cp["denge_derisim_mgL"].min(), cp["denge_derisim_mgL"].max()
    iz_cp = sonuc["izoterm"]["cay_posasi"]["langmuir"]
    ga_genislik = ((iz_cp["qmax_GA"][1] - iz_cp["qmax_GA"][0])
                   / iz_cp["qmax_mgG"] * 100)
    # Doygunluğun ne kadarına ulaşıldığı: KL·Ce / (1 + KL·Ce)
    doyma = (iz_cp["KL_Lmg"] * ce_ust) / (1 + iz_cp["KL_Lmg"] * ce_ust) * 100
    satir += ["",
              "Ticari kömürde tahminler gerçeğe çok yakın. Çay posasında",
              "qmax tahmini gerçeğin epey altında ve güven aralığı",
              "gerçek değeri KAPSAMIYOR. Nedeni yöntem değil, deney",
              f"aralığı: çay posasının denge derişimleri {ts(ce_alt, 1)}-"
              f"{ts(ce_ust, 1)} mg/L",
              "arasında kalıyor. En yüksek derişimde bile kapasitenin",
              f"ancak %{ts(doyma, 0)} kadarı doluyor; izoterm doygunluk",
              "bölgesine girmiyor. qmax doygunluk düzeyidir, ulaşılmamış",
              "bir düzey veriden güvenilir biçimde çıkarılamaz.", "",
              "Pratik sonuç: qmax raporlanacaksa, derişim aralığının",
              "doygunluk bölgesini kapsadığı gösterilmelidir. Geniş",
              "güven aralığı bu uyarıyı zaten veriyor — çay posasında",
              f"qmax aralığının genişliği, tahminin %{ts(ga_genislik, 0)}",
              "kadarı.", ""]
    satir += ["Not: n = 8-9 nokta, izoterm uyumu için az. Yayımlanacak",
              "bir çalışmada derişim basamağı sayısı artırılır.", ""]

    # --- Adım 5: duyarlılık ---------------------------------------------
    satir += ["", "ADIM 5 — ŞÜPHELİ DÖNEM DUYARLILIK ANALİZİ", "-" * 74, "",
              "Neden bu adım: 12-18 Mart ölçümleri cihaz bakım kaydı",
              "nedeniyle kuşkulu. Onları atmak da tutmak da bir karar;",
              "hangisinin sonucu değiştirdiğini göstermek, kararı okurun",
              "denetlemesine açar.", "",
              f"Şüpheli dönem dışarıda bırakıldığında (n = {len(alt)}):", "",
              f"{'Kaynak':<28}{'F (tümü)':>12}{'F (hariç)':>12}"
              f"{'η²p (tümü)':>12}{'η²p (hariç)':>13}"]
    karsilastirma = []
    for (_, a), (_, b) in zip(tablo.iterrows(), tablo_alt.iterrows()):
        if pd.isna(a["F"]):
            continue
        satir.append(f"{a['kaynak']:<28}{ts(a['F'], 2):>12}"
                     f"{ts(b['F'], 2):>12}{ts(a['kismi_eta_kare'], 3):>12}"
                     f"{ts(b['kismi_eta_kare'], 3):>13}")
        karsilastirma.append({
            "kaynak": a["kaynak"], "F_tumu": float(a["F"]),
            "F_haric": float(b["F"]),
            "eta_tumu": float(a["kismi_eta_kare"]),
            "eta_haric": float(b["kismi_eta_kare"]),
            "p_tumu": float(a["PR(>F)"]), "p_haric": float(b["PR(>F)"])})
    donen = [k["kaynak"] for k in karsilastirma
             if (k["p_tumu"] < 0.05) != (k["p_haric"] < 0.05)]
    satir += ["",
              ("Anlamlılık kararı değişen terim yok; bulgular şüpheli "
               "döneme duyarlı değil."
               if not donen else
               "Anlamlılık kararı değişen terim(ler): " + ", ".join(donen)
               + ". Bu terimler sonuç bölümünde şüpheli dönem belirtilerek "
                 "raporlanmalı."),
              ""]
    sonuc["duyarlilik"] = {"n_haric": len(alt),
                           "karsilastirma": karsilastirma,
                           "karari_degisen": donen}

    # --- Betimsel özet --------------------------------------------------
    ozet = (df.groupby(["adsorban", "pH"], observed=True)
            .agg(n=("q_mgG", "size"), q_ortalama=("q_mgG", "mean"),
                 q_ss=("q_mgG", "std"),
                 giderim_ortalama=("giderim_yuzde", "mean"))
            .round(3).reset_index())
    ozet.to_csv(hedef / "adsorpsiyon_ozet.csv", index=False,
                encoding="utf-8-sig")
    tablo[["kaynak", "sum_sq", "df", "F", "PR(>F)", "kismi_eta_kare"]].to_csv(
        hedef / "adsorpsiyon_anova.csv", index=False, encoding="utf-8-sig")

    satir += ["", "BETİMSEL ÖZET", "-" * 74, "",
              f"{'Adsorban':<14}{'pH':>5}{'n':>5}{'q ort.':>10}"
              f"{'q SS':>9}{'giderim %':>12}"]
    for _, s in ozet.iterrows():
        ad_g = "Çay posası" if s["adsorban"] == "cay_posasi" else "Ticari"
        satir.append(f"{ad_g:<14}{ts(s['pH'], 0):>5}{int(s['n']):>5}"
                     f"{ts(s['q_ortalama'], 2):>10}{ts(s['q_ss'], 2):>9}"
                     f"{ts(s['giderim_ortalama'], 1):>12}")
    satir.append("")

    (hedef / "adsorpsiyon_analiz.txt").write_text(
        "\n".join(satir) + "\n", encoding="utf-8-sig")
    (hedef / "adsorpsiyon_analiz.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=2, default=json_cevir),
        encoding="utf-8")
    print("\n".join(satir))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
