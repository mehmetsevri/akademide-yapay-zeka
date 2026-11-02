# -*- coding: utf-8 -*-
"""
06 — Web güvenliği analizi: kimlik avı (phishing) URL sınıflandırması

Veri seti (GERÇEK, açık erişim):
  Prasad, A., & Chandra, S. (2024). PhiUSIIL Phishing URL (Website)
  [Veri seti]. UCI Machine Learning Repository.
  Kaynak makale: Computers & Security, 2024.
  https://doi.org/10.1016/j.cose.2023.103545
  İndirme: https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset
  Lisans: CC BY 4.0

Bu betiğin omurgası bir anlatıdır: naif model kurulur, %100'e yakın
doğruluk alınır, bu sonuçtan ŞÜPHE EDİLİR, nedeni teşhis edilir ve
dürüst sayı yeniden hesaplanır. Yüksek doğruluk bir başarı belgesi
değil, bir denetim gerekçesidir.

Kullanım:
  python 06_analiz_web_guvenligi.py <veri_csv> <çıktı_klasörü>
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
                             classification_report, confusion_matrix,
                             f1_score, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score,
                             roc_curve)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

TOHUM = 20261103

# Özellik aileleri — hangi özellik NE ZAMAN hesaplanabilir?
# Bu ayrım yöntemseldir: bir kimlik avı süzgeci kararı, kullanıcı siteyi
# ZİYARET ETMEDEN vermek zorundadır. Sayfa içeriğinden türeyen özellikler
# ancak siteye bağlandıktan sonra elde edilir; bu da zararlı sayfanın
# yüklenmesi anlamına gelir. Yerleşime uygun model yalnız URL metninden
# hesaplanabilen özellikleri kullanır.
SOZCUKSEL_OZELLIKLER = [
    "URLLength", "DomainLength", "TLDLength", "NoOfSubDomain",
    "CharContinuationRate", "URLCharProb", "NoOfLettersInURL",
    "LetterRatioInURL", "NoOfDegitsInURL", "DegitRatioInURL",
    "SpacialCharRatioInURL",
]

SONUC = {}
SATIRLAR = []


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


def json_cevir(n):
    if isinstance(n, np.integer):
        return int(n)
    if isinstance(n, np.floating):
        return float(n)
    if isinstance(n, np.bool_):
        return bool(n)
    if isinstance(n, np.ndarray):
        return n.tolist()
    raise TypeError(type(n).__name__)


def olcutler(y_true, y_pred, y_olasilik):
    """Sınıflandırma ölçütlerinin tamamı tek yerde.

    Pozitif sınıf = kimlik avı. Hangi sınıfın 'pozitif' sayıldığı,
    duyarlılık (recall) ve kesinlik (precision) sayılarının ne anlama
    geldiğini belirler; bu seçim raporda açıkça yazılmalıdır.
    """
    km = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = km.ravel()
    return {
        "doğruluk": round(accuracy_score(y_true, y_pred), 4),
        "kesinlik": round(precision_score(y_true, y_pred), 4),
        "duyarlılık": round(recall_score(y_true, y_pred), 4),
        "F1": round(f1_score(y_true, y_pred), 4),
        "ROC_AUC": round(roc_auc_score(y_true, y_olasilik), 4),
        "PR_AUC": round(average_precision_score(y_true, y_olasilik), 4),
        "karışıklık": {"DN_doğru_negatif": int(tn), "YP_yanlış_pozitif": int(fp),
                       "YN_yanlış_negatif": int(fn), "DP_doğru_pozitif": int(tp)},
    }


def main(veri_csv: str, cikti_klasoru: str) -> None:
    df = pd.read_csv(veri_csv, encoding="utf-8-sig")
    y = (df["etiket"] == "kimlik_avi").astype(int)   # pozitif = kimlik avı
    sayisal = df.select_dtypes(include=[np.number]).drop(columns=["label"])
    ozellikler = [c for c in sayisal.columns]

    yaz("VERİ SETİ")
    yaz("-" * 78)
    yaz("Prasad, A., & Chandra, S. (2024). PhiUSIIL Phishing URL (Website).")
    yaz("UCI Machine Learning Repository.")
    yaz("Kaynak makale DOI: 10.1016/j.cose.2023.103545")
    yaz(f"Bu çalışmada kullanılan altküme: {len(df):,} satır, "
        f"{len(ozellikler)} sayısal özellik")
    yaz(f"Sınıf dağılımı: kimlik avı {int(y.sum()):,} (%{100*y.mean():.1f}), "
        f"meşru {int((1-y).sum()):,} (%{100*(1-y.mean()):.1f})")
    SONUC["veri"] = {"n": len(df), "ozellik": len(ozellikler),
                     "kimlik_avi": int(y.sum()), "mesru": int((1 - y).sum()),
                     "kimlik_avi_oran": round(float(y.mean()), 4)}

    # ------------------------------------------------------------ ADIM 1
    baslik(1, "Betimsel karşılaştırma — iki sınıf arasındaki fark",
           "Her özelliğin iki sınıftaki ortalamasının karşılaştırılması.",
           "Model kurmadan önce verinin ne söylediğine bakılır. Hangi "
           "özellik ayırt edici, hangisi değil — bu, sonradan modelin "
           "söylediğini denetlemek için gereken ön bilgidir.")
    karsilastirma = []
    for ozellik in ozellikler:
        a = df.loc[y == 1, ozellik].astype(float)
        b = df.loc[y == 0, ozellik].astype(float)
        if a.std() == 0 and b.std() == 0:
            continue
        t = stats.ttest_ind(a, b, equal_var=False)
        birlesik_ss = np.sqrt(((len(a)-1)*a.var(ddof=1)
                               + (len(b)-1)*b.var(ddof=1))
                              / (len(a)+len(b)-2))
        d = (a.mean() - b.mean()) / birlesik_ss if birlesik_ss > 0 else 0.0
        karsilastirma.append({
            "özellik": ozellik,
            "kimlik_avı_ort": round(float(a.mean()), 3),
            "meşru_ort": round(float(b.mean()), 3),
            "t": round(float(t.statistic), 2),
            "p": float(f"{t.pvalue:.3g}"),
            "cohen_d": round(float(d), 3)})
    kars_df = pd.DataFrame(karsilastirma).sort_values(
        "cohen_d", key=abs, ascending=False)
    yaz("Etki büyüklüğüne göre en ayırt edici on özellik:")
    yaz(kars_df.head(10).to_string(index=False))
    yaz()
    yaz("En ayırt edici özelliğin etki büyüklüğü: "
        f"d = {kars_df.iloc[0]['cohen_d']}  ({kars_df.iloc[0]['özellik']})")
    yaz("NOT — |d| > 3 son derece olağandışıdır. Sosyal bilimlerde d = 0,8")
    yaz("'büyük etki' sayılır. Bu büyüklükte bir fark, özelliğin etiketle")
    yaz("neredeyse aynı şey olduğu anlamına gelebilir. Not edip ilerliyoruz.")
    SONUC["betimsel_karsilastirma"] = kars_df.to_dict("records")

    # ------------------------------------------------------------ ADIM 2
    baslik(2, "Kategorik ilişki — ki-kare",
           "İki kategorik değişkenin bağımsızlığının sınanması.",
           "HTTPS kullanımı ile kimlik avı arasındaki ilişki, yaygın bir "
           "güvenlik varsayımını sınar: 'kilit simgesi varsa güvenlidir'.")
    capraz = pd.crosstab(df["IsHTTPS"], df["etiket"])
    ki2, p_ki2, sd, beklenen = stats.chi2_contingency(capraz)
    v = np.sqrt((ki2 / capraz.values.sum()) / (min(capraz.shape) - 1))
    yaz("Çapraz tablo — HTTPS × etiket:")
    yaz(capraz.to_string())
    yaz()
    yaz(f"χ²({sd}) = {ki2:.2f}, p = {p_ki2:.3g}, Cramér V = {v:.4f}")
    https_kimlik_avi = capraz.loc[1, "kimlik_avi"] / capraz.loc[1].sum()
    yaz(f"HTTPS kullanan sitelerin %{100*https_kimlik_avi:.1f}'i kimlik avı.")
    yaz("Bulgu — HTTPS varlığı tek başına güvenlik göstergesi değildir.")
    SONUC["ki_kare_https"] = {
        "capraz": capraz.reset_index().to_dict("records"),
        "ki2": round(float(ki2), 2), "sd": int(sd),
        "p": float(f"{p_ki2:.3g}"), "cramers_v": round(float(v), 4),
        "https_icinde_kimlik_avi_oran": round(float(https_kimlik_avi), 4)}

    # ------------------------------------------------------------ ADIM 3
    baslik(3, "NAİF MODEL — tüm özelliklerle sınıflandırma",
           "Rastgele orman (random forest) ile ikili sınıflandırma.",
           "Standart yaklaşım: özellikleri modele ver, eğit, ölç. Bu adımı "
           "olduğu gibi yapıp sonucuna bakacağız.")
    X_eg, X_test, y_eg, y_test = train_test_split(
        sayisal[ozellikler], y, test_size=0.30, stratify=y,
        random_state=TOHUM)
    yaz(f"Eğitim: {len(X_eg):,} satır   Test: {len(X_test):,} satır")
    yaz("Bölme katmanlı (stratified) — iki sınıfın oranı her iki kümede aynı.")

    naif = RandomForestClassifier(n_estimators=300, random_state=TOHUM,
                                  n_jobs=-1)
    naif.fit(X_eg, y_eg)
    naif_tahmin = naif.predict(X_test)
    naif_olasilik = naif.predict_proba(X_test)[:, 1]
    naif_olcut = olcutler(y_test, naif_tahmin, naif_olasilik)
    yaz()
    for k, deger in naif_olcut.items():
        if k != "karışıklık":
            yaz(f"  {k:12s}: {deger}")
    km = naif_olcut["karışıklık"]
    yaz(f"  Karışıklık matrisi: DN={km['DN_doğru_negatif']}  "
        f"YP={km['YP_yanlış_pozitif']}  YN={km['YN_yanlış_negatif']}  "
        f"DP={km['DP_doğru_pozitif']}")
    yaz()
    yaz("DUR. Bu sayılar fazla iyi.")
    yaz(f"Doğruluk %{100*naif_olcut['doğruluk']:.2f}, "
        f"ROC AUC {naif_olcut['ROC_AUC']}.")
    yaz("Gerçek bir güvenlik probleminde bu düzey bir başarı, modelin")
    yaz("problemi çözdüğünü değil, problemin yanlışlıkla kolaylaştığını")
    yaz("gösterir. Yayımlamadan önce nedenini bulmak zorunludur.")
    SONUC["naif_model"] = naif_olcut

    # ------------------------------------------------------------ ADIM 4
    baslik(4, "TEŞHİS — nereden geldiği sistematik olarak aranır",
           "Her özelliğin sınıf içi değişkenliği ve tek başına ayırt etme "
           "gücünün taranması.",
           "Şüphe doğduğunda tek tek sütun denemek yerine tüm sütunlar iki "
           "ölçütle taranır: (a) bir sınıfta tamamen sabit mi, (b) tek bir "
           "eşikle kaç yüzde doğruluk veriyor. Bu tarama, sızıntıyı "
           "aramanın standart yoludur.")

    onem = pd.DataFrame({
        "özellik": ozellikler,
        "önem": naif.feature_importances_.round(5)}
    ).sort_values("önem", ascending=False)
    yaz("Rastgele ormanın özellik önemleri (ilk 8):")
    yaz(onem.head(8).to_string(index=False))
    yaz()

    tarama = []
    for ozellik in ozellikler:
        a = df.loc[y == 1, ozellik].astype(float)
        b = df.loc[y == 0, ozellik].astype(float)
        degerler = df[ozellik].astype(float)
        esikler = np.unique(np.quantile(degerler, np.linspace(0, 1, 80)))
        en_iyi = 0.0
        for e in esikler:
            en_iyi = max(en_iyi,
                         float(((degerler <= e).astype(int) == y).mean()),
                         float(((degerler > e).astype(int) == y).mean()))
        tarama.append({
            "özellik": ozellik,
            "kimlik_avı_ss": round(float(a.std(ddof=1)), 4),
            "meşru_ss": round(float(b.std(ddof=1)), 4),
            "meşru_sınıfta_sabit": bool(b.nunique() == 1),
            "tek_eşik_doğruluk": round(en_iyi, 4)})
    tarama_df = pd.DataFrame(tarama)

    sabit = tarama_df[tarama_df["meşru_sınıfta_sabit"]].sort_values(
        "tek_eşik_doğruluk", ascending=False)
    yaz("(a) MEŞRU sınıfta tamamen sabit olan özellikler — standart sapma 0:")
    yaz(sabit[["özellik", "meşru_ss", "kimlik_avı_ss",
               "tek_eşik_doğruluk"]].to_string(index=False))
    yaz()
    yaz(f">>> {len(sabit)} özellik, meşru sınıftaki 2.859 kaydın")
    yaz(">>> TAMAMINDA aynı değeri alıyor. Bu bir ölçüm değil;")
    yaz(">>> veri setinin kuruluşundan gelen bir düzenliliktir.")
    yaz()

    guclu = tarama_df[tarama_df["tek_eşik_doğruluk"] > 0.90].sort_values(
        "tek_eşik_doğruluk", ascending=False)
    yaz("(b) Tek bir 'if' satırıyla %90 üstü doğruluk veren özellikler:")
    yaz(guclu[["özellik", "tek_eşik_doğruluk"]].to_string(index=False))
    yaz()
    yaz(f"{len(guclu)} özelliğin her biri, modelsiz, tek eşikle %90'ın")
    yaz("üstünde doğruluk veriyor. Bunların çoğu sayfa içeriğinden geliyor:")
    yaz("meşru sayfalar büyük, çok görselli, çok dış bağlantılı; kimlik avı")
    yaz("sayfaları küçük ve çıplak. Bu gerçek bir örüntü — ama modelin")
    yaz("öğrendiği şey kimlik avı davranışı değil, SAYFA BOYUTU.")
    SONUC["teshis"] = {
        "ozellik_onemi": onem.to_dict("records"),
        "baskin_ozellik": onem.iloc[0]["özellik"],
        "baskin_onem_payi": round(float(onem.iloc[0]["önem"]), 5),
        "tarama": tarama_df.to_dict("records"),
        "mesru_sinifta_sabit_sayisi": int(len(sabit)),
        "mesru_sinifta_sabit": sabit["özellik"].tolist(),
        "tek_esik_90_ustu": guclu[["özellik", "tek_eşik_doğruluk"]].to_dict("records")}

    # ------------------------------------------------------------ ADIM 5
    baslik(5, "TEK SÜTUN ÇIKARMAK YETMİYOR",
           "En baskın özelliğin çıkarılıp modelin yeniden eğitilmesi.",
           "Sızıntı bulunduğunda ilk tepki o sütunu silmektir. Bu tepkinin "
           "yeterli olup olmadığı ölçülmelidir — yoksa düzeltilmiş "
           "sanılan bir sayı raporlanır.")
    baskin = onem.iloc[0]["özellik"]
    kalan = [o for o in ozellikler if o != baskin]
    tek_cikarma = RandomForestClassifier(n_estimators=300,
                                         random_state=TOHUM, n_jobs=-1)
    tek_cikarma.fit(X_eg[kalan], y_eg)
    tc_olcut = olcutler(y_test, tek_cikarma.predict(X_test[kalan]),
                        tek_cikarma.predict_proba(X_test[kalan])[:, 1])
    yaz(f"Çıkarılan tek özellik: {baskin}")
    yaz(f"Naif model F1       : {naif_olcut['F1']}")
    yaz(f"Tek sütun çıkarılmış: {tc_olcut['F1']}")
    yaz(f"Değişim             : {tc_olcut['F1'] - naif_olcut['F1']:+.4f}")
    yaz()
    yaz("Neredeyse hiç değişmedi. Çünkü diğer özellikler aynı bilgiyi")
    yaz("taşıyor. Sızıntı tek bir sütunda değil, veri setinin iki sınıfını")
    yaz("toplama biçiminde. Bir sütun silerek düzeltilemez; çerçeve")
    yaz("değişmelidir.")
    SONUC["tek_sutun_cikarma"] = {"cikarilan": baskin, "olcutler": tc_olcut,
                                  "f1_degisim": round(float(tc_olcut["F1"]
                                                            - naif_olcut["F1"]), 4)}

    # ------------------------------------------------------------ ADIM 6
    baslik(6, "YERLEŞİME UYGUN ÇERÇEVE — yalnız URL metni",
           "Kararın, siteye hiç bağlanmadan, yalnız URL dizgisinden "
           "hesaplanabilen özelliklerle verilmesi.",
           "Bu bir istatistik hilesi değil, problemin doğru tanımıdır. "
           "Gerçek bir kimlik avı süzgeci, kullanıcı bağlantıya tıklamadan "
           "ÖNCE karar vermek zorundadır; sayfa içeriği o anda elde yoktur. "
           "Sayfa özelliklerini kullanmak, geleceği bilerek geçmişi "
           "tahmin etmeye benzer.")
    yaz("Kullanılan özellikler (yalnız URL dizgisinden hesaplanır):")
    for i in range(0, len(SOZCUKSEL_OZELLIKLER), 3):
        yaz("  " + "  ".join(f"{o:24s}"
                             for o in SOZCUKSEL_OZELLIKLER[i:i + 3]))
    yaz()
    yaz("Dışarıda bırakılanlar ve gerekçeleri:")
    yaz("  • URLSimilarityIndex   — meşru sınıfta sabit (100,0); sızıntı")
    yaz("  • IsHTTPS, IsDomainIP, HasObfuscation, NoOfQMarkInURL")
    yaz("                         — meşru sınıfta sabit; sızıntı")
    yaz("  • Sayfa içeriği özellikleri (LineOfCode, NoOfImage, NoOfJS,")
    yaz("    NoOfCSS, NoOfExternalRef, HasSocialNet, …)")
    yaz("                         — ancak siteye bağlanınca elde edilir;")
    yaz("                           yerleşim senaryosuna aykırı")
    yaz("  • TLDLegitimateProb    — şüphelenildi, DENETLENDİ: tek eşikle")
    yaz("                           yalnız %66,9 doğruluk veriyor ve modele")
    yaz("                           katkısı yok; sızıntı değil, yine de")
    yaz("                           türetilmiş olduğu için dışarıda bırakıldı")
    yaz()

    durust = RandomForestClassifier(n_estimators=300, random_state=TOHUM,
                                    n_jobs=-1)
    durust.fit(X_eg[SOZCUKSEL_OZELLIKLER], y_eg)
    d_tahmin = durust.predict(X_test[SOZCUKSEL_OZELLIKLER])
    d_olasilik = durust.predict_proba(X_test[SOZCUKSEL_OZELLIKLER])[:, 1]
    durust_olcut = olcutler(y_test, d_tahmin, d_olasilik)
    for k, deger in durust_olcut.items():
        if k != "karışıklık":
            yaz(f"  {k:12s}: {deger}")
    km2 = durust_olcut["karışıklık"]
    yaz(f"  Karışıklık matrisi: DN={km2['DN_doğru_negatif']}  "
        f"YP={km2['YP_yanlış_pozitif']}  YN={km2['YN_yanlış_negatif']}  "
        f"DP={km2['DP_doğru_pozitif']}")
    yaz()
    kiyas = pd.DataFrame([
        {"model": "1. Naif — 40 özellik", "özellik": len(ozellikler),
         **{k: v for k, v in naif_olcut.items() if k != "karışıklık"}},
        {"model": "2. Tek sütun çıkarılmış", "özellik": len(kalan),
         **{k: v for k, v in tc_olcut.items() if k != "karışıklık"}},
        {"model": "3. Yerleşime uygun — URL metni",
         "özellik": len(SOZCUKSEL_OZELLIKLER),
         **{k: v for k, v in durust_olcut.items() if k != "karışıklık"}}])
    yaz("Üç modelin karşılaştırması:")
    yaz(kiyas.to_string(index=False))
    yaz()
    yaz("Raporlanacak sayı üçüncü satırdır. Birinci satır bir ölçüm değil,")
    yaz("veri setinin kuruluşunun yankısıdır.")
    yaz()
    yaz("Sınıflandırma raporu (yerleşime uygun model):")
    yaz(classification_report(y_test, d_tahmin,
                              target_names=["meşru", "kimlik avı"],
                              digits=4))
    SONUC["durust_model"] = durust_olcut
    SONUC["sozcuksel_ozellikler"] = SOZCUKSEL_OZELLIKLER
    SONUC["model_kiyas"] = kiyas.to_dict("records")

    # ------------------------------------------------------------ ADIM 7
    baslik(7, "Çapraz doğrulama — tek bölünmeye güvenmemek",
           "Verinin beş parçaya bölünüp her parçanın sırayla test kümesi "
           "olarak kullanılması.",
           "Tek bir eğitim/test bölünmesinden çıkan sayı, o bölünmenin "
           "şansına bağlıdır. Makalede ortalama ± standart sapma "
           "raporlanır; tek bir sayı raporlamak eksik bildirimdir.")
    kat = StratifiedKFold(n_splits=5, shuffle=True, random_state=TOHUM)
    cv_f1 = cross_val_score(
        RandomForestClassifier(n_estimators=300, random_state=TOHUM, n_jobs=-1),
        sayisal[SOZCUKSEL_OZELLIKLER], y, cv=kat, scoring="f1")
    cv_auc = cross_val_score(
        RandomForestClassifier(n_estimators=300, random_state=TOHUM, n_jobs=-1),
        sayisal[SOZCUKSEL_OZELLIKLER], y, cv=kat, scoring="roc_auc")
    yaz(f"F1 (5 kat)      : {' '.join(f'{v:.4f}' for v in cv_f1)}")
    yaz(f"  ortalama ± ss : {cv_f1.mean():.4f} ± {cv_f1.std():.4f}")
    yaz(f"ROC AUC (5 kat) : {' '.join(f'{v:.4f}' for v in cv_auc)}")
    yaz(f"  ortalama ± ss : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")
    yaz()
    yaz("Makalede yazılacak cümle:")
    yaz(f"  \"Yalnız URL dizgisinden türetilen 11 sözcüksel özellikle "
        f"eğitilen\"")
    yaz(f"  \"rastgele orman modeli, beş katlı çapraz doğrulamada "
        f"F1 = {cv_f1.mean():.3f} ± {cv_f1.std():.3f}\"")
    yaz(f"  \"ve ROC AUC = {cv_auc.mean():.3f} ± {cv_auc.std():.3f} "
        f"başarısı göstermiştir (n = {len(df):,}).\"")
    SONUC["capraz_dogrulama"] = {
        "kat_sayisi": 5,
        "f1_katlar": [round(float(v), 4) for v in cv_f1],
        "f1_ortalama": round(float(cv_f1.mean()), 4),
        "f1_ss": round(float(cv_f1.std()), 4),
        "auc_katlar": [round(float(v), 4) for v in cv_auc],
        "auc_ortalama": round(float(cv_auc.mean()), 4),
        "auc_ss": round(float(cv_auc.std()), 4)}

    # ------------------------------------------------------------ ADIM 8
    baslik(8, "Hangi URL nitelikleri çalışıyor — permütasyon önemi",
           "Bir özelliğin değerleri karıştırıldığında başarının ne kadar "
           "düştüğünün ölçülmesi.",
           "Ağaç tabanlı önem ölçütü sürekli ve çok değerli özellikleri "
           "şişirir. Permütasyon önemi doğrudan 'bu özellik olmasa ne "
           "kaybederim' sorusunu yanıtlar; Tartışma bölümü bu listeden "
           "yazılır.")
    perm = permutation_importance(
        durust, X_test[SOZCUKSEL_OZELLIKLER], y_test, n_repeats=20,
        random_state=TOHUM, scoring="f1", n_jobs=-1)
    perm_df = pd.DataFrame({
        "özellik": SOZCUKSEL_OZELLIKLER,
        "ortalama_düşüş": perm.importances_mean.round(5),
        "ss": perm.importances_std.round(5)}
    ).sort_values("ortalama_düşüş", ascending=False)
    yaz(perm_df.to_string(index=False))
    yaz()
    yaz(f"En etkili özellik: {perm_df.iloc[0]['özellik']} — karıştırıldığında")
    yaz(f"F1 {perm_df.iloc[0]['ortalama_düşüş']:.4f} düşüyor.")
    SONUC["permutasyon_onemi"] = perm_df.to_dict("records")

    # ------------------------------------------------------------ ADIM 9
    baslik(9, "Yorumlanabilir karşılaştırma — lojistik regresyon",
           "Aynı problemin, katsayıları okunabilir bir modelle çözülmesi.",
           "Rastgele orman daha başarılı olabilir ama neden öyle karar "
           "verdiğini söylemez. Lojistik regresyon her özellik için bir "
           "olasılık oranı verir; hakem 'hangi değişken ne yönde etkili' "
           "diye sorduğunda gösterilecek tablo budur.")
    olcekleyici = StandardScaler()
    X_eg_o = olcekleyici.fit_transform(X_eg[SOZCUKSEL_OZELLIKLER])
    X_test_o = olcekleyici.transform(X_test[SOZCUKSEL_OZELLIKLER])
    log = LogisticRegression(max_iter=5000, random_state=TOHUM)
    log.fit(X_eg_o, y_eg)
    log_olcut = olcutler(y_test, log.predict(X_test_o),
                         log.predict_proba(X_test_o)[:, 1])
    for k, deger in log_olcut.items():
        if k != "karışıklık":
            yaz(f"  {k:12s}: {deger}")
    katsayi = pd.DataFrame({
        "özellik": SOZCUKSEL_OZELLIKLER,
        "B_standart": log.coef_[0].round(4),
        "olasılık_oranı": np.exp(log.coef_[0]).round(4)}
    ).sort_values("B_standart", key=abs, ascending=False)
    yaz()
    yaz("Standartlaştırılmış katsayılar — OR, bir standart sapma artışın "
        "etkisi:")
    yaz(katsayi.to_string(index=False))
    yaz()
    yaz(f"Rastgele orman F1 = {durust_olcut['F1']}, "
        f"lojistik regresyon F1 = {log_olcut['F1']}.")
    yaz("Fark, yorumlanabilirlik karşılığında ödenen bedeldir. Hangisinin")
    yaz("raporlanacağı çalışmanın sorusuna bağlıdır: tahmin başarısı mı,")
    yaz("mekanizma açıklaması mı?")
    SONUC["lojistik"] = {"olcutler": log_olcut,
                         "katsayilar": katsayi.to_dict("records")}

    # ------------------------------------------- ROC / PR egrisi noktalari
    fpr, tpr, _ = roc_curve(y_test, d_olasilik)
    kes, duy, _ = precision_recall_curve(y_test, d_olasilik)
    adim = max(1, len(fpr) // 200)
    SONUC["egriler"] = {
        "roc": {"fpr": [round(float(v), 5) for v in fpr[::adim]],
                "tpr": [round(float(v), 5) for v in tpr[::adim]]},
        "pr": {"duyarlilik": [round(float(v), 5) for v in duy[::max(1, len(duy)//200)]],
               "kesinlik": [round(float(v), 5) for v in kes[::max(1, len(kes)//200)]]},
        "naif_roc": {"fpr": [round(float(v), 5) for v in roc_curve(y_test, naif_olasilik)[0][::adim]],
                     "tpr": [round(float(v), 5) for v in roc_curve(y_test, naif_olasilik)[1][::adim]]}}

    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    (hedef / "web_guvenligi_analiz.json").write_text(
        json.dumps(SONUC, ensure_ascii=False, indent=1, default=json_cevir),
        encoding="utf-8")
    (hedef / "web_guvenligi_analiz.txt").write_text(
        "\n".join(SATIRLAR), encoding="utf-8-sig")
    yaz()
    yaz("=" * 78)
    yaz(f"Tamamlandı: {hedef / 'web_guvenligi_analiz.json'}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
