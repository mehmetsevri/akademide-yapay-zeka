# -*- coding: utf-8 -*-
"""
01 — Web güvenliği örneği: veri hazırlama

Kaynak veri seti:
  PhiUSIIL Phishing URL Dataset
  Prasad, A. & Chandra, S. (2024). UCI Machine Learning Repository.
  https://doi.org/10.24432/C5FQ8D   (235.795 satir, 56 sutun)

Bu betik tam veri setinden, egitim amacli, katmanli (stratified) rastgele
bir altkume cikarir. Tam veri seti 57 MB; web sitesiyle dagitilamaz.
Altkume tohumu sabittir, boylece sonuclar yeniden uretilebilir.

Kullanim:
  python 01_web_guvenligi_veri_hazirla.py <tam_veri.csv> <cikti_klasoru>
"""
import sys
import pathlib
import pandas as pd

TOHUM = 20261103          # egitim tarihi — sabit tohum, yeniden uretilebilirlik icin
ORNEK_BOYUTU = 5000

# Egitim icin secilen sutunlar. Tam veri setindeki 56 sutunun tamami
# gerekli degil; bu 32 sutun URL yapisi + sayfa icerigi + etiketi kapsiyor.
SUTUNLAR = [
    # --- URL yapisal ozellikleri ---
    "URLLength", "DomainLength", "IsDomainIP", "TLD", "TLDLength",
    "NoOfSubDomain", "CharContinuationRate", "TLDLegitimateProb",
    "URLCharProb", "HasObfuscation", "NoOfLettersInURL", "LetterRatioInURL",
    "NoOfDegitsInURL", "DegitRatioInURL", "NoOfQMarkInURL",
    "SpacialCharRatioInURL", "IsHTTPS",
    # --- sayfa icerigi ozellikleri ---
    "LineOfCode", "LargestLineLength", "HasTitle", "DomainTitleMatchScore",
    "URLTitleMatchScore", "HasFavicon", "IsResponsive", "NoOfURLRedirect",
    "HasDescription", "NoOfPopup", "NoOfiFrame", "HasExternalFormSubmit",
    "HasSocialNet", "HasHiddenFields", "HasPasswordField",
    "Bank", "Pay", "Crypto", "HasCopyrightInfo",
    "NoOfImage", "NoOfCSS", "NoOfJS", "NoOfExternalRef",
    # --- sizinti dersi icin bilerek birakilan sutun ---
    "URLSimilarityIndex",
    # --- etiket ---
    "label",
]


def main(kaynak: str, cikti_klasoru: str) -> None:
    ham = pd.read_csv(kaynak, encoding="utf-8-sig", low_memory=False)
    print(f"Tam veri seti okundu: {ham.shape[0]:,} satir x {ham.shape[1]} sutun")

    alt = ham[SUTUNLAR].copy()

    # Katmanli ornekleme: iki sinifin orani tam veri setindekiyle ayni kalir.
    # Her sinifin indekslerinden ayri ayri ornek cekip birlestiriyoruz;
    # boylece groupby().apply() davranisina bagli kalmadan sonuc deterministik olur.
    oran = ORNEK_BOYUTU / len(alt)
    secilen = []
    for sinif, grup in alt.groupby("label"):
        secilen.append(grup.sample(n=round(len(grup) * oran), random_state=TOHUM))
    ornek = (
        pd.concat(secilen)
        .sample(frac=1, random_state=TOHUM)      # satir sirasini karistir
        .reset_index(drop=True)
    )

    # Etiketi okunur hale getir: kaynak veri setinde 1 = mesru, 0 = kimlik avi.
    ornek["etiket"] = ornek["label"].map({1: "mesru", 0: "kimlik_avi"})

    hedef = pathlib.Path(cikti_klasoru) / "phishing_ornek_5000.csv"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    ornek.to_csv(hedef, index=False, encoding="utf-8-sig")

    print(f"Ornek yazildi: {hedef}")
    print(f"  satir: {len(ornek):,}   sutun: {ornek.shape[1]}")
    print(f"  boyut: {hedef.stat().st_size / 1024:.0f} KB")
    print("  sinif dagilimi:")
    for ad, sayi in ornek["etiket"].value_counts().items():
        print(f"    {ad:12s} {sayi:5,}  (%{100 * sayi / len(ornek):.1f})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
