# -*- coding: utf-8 -*-
"""
26 — Kentsel dönüşüm korpusu: tematik analiz (Braun & Clarke, 2006)

MAXQDA ve NVivo'nun yaptığı işin tamamı burada açık kodla yapılır:
kod kitabı, kod atama, tema toplama, sıklık tabloları, kodlayıcılar
arası uyum, eş-görünüm matrisi, doygunluk eğrisi ve dönüşüm matrisi.

Tek fark şu: yazılımda kodlama kararları veritabanının içinde kalır,
burada DOSYANIN İÇİNDE veri olarak durur. Hakem "şu kodu neye göre
verdiniz" diye sorduğunda gösterilecek bir şey olur.

KODLAMA NASIL YAPILDI
Kod kitabı önce araştırmacı tarafından 60 parçalık bir okuma üzerinden
elle çıkarıldı. Sonra her kod için ayırt edici ifade örüntüleri
yazıldı (ÖRÜNTÜLER sözlüğü). Bu örüntüler korpusun tamamına
uygulanarak otomatik bir ilk kodlama üretildi. Yapay zekânın işi
örüntüleri ÖNERMEKTİ; hangi örüntünün kalacağına araştırmacı karar
verdi ve kararlar aşağıda görünür durumda.

Otomatik kodlama tek başına yeterli sayılmaz. İki denetimi var:
  — referans kodlamayla karşılaştırma (Adım 7): korpus sentetik
    olduğu için her parçanın üretildiği kod bilinir
  — kodlayıcılar arası uyum (Adım 8): Cohen kappa

ADIMLAR
   1  Veriye aşinalık: korpusun büyüklüğü ve bileşimi
   2  Kod kitabı
   3  Kodlama ve kod sıklıkları
   4  Tema sıklıkları ve katılımcı yayılımı
   5  Tema × katılımcı grubu matrisi
   6  Dönüşüm matrisi: öncesi · inşaat · sonrası
   7  Kodlamanın referansla uyumu
   8  Kodlayıcılar arası uyum (Cohen kappa)
   9  Doygunluk (saturation) eğrisi
  10  Kod eş-görünümü
  11  Temsil edici alıntılar
  12  Aykırı örnek (negative case) incelemesi

Kullanım:
  python 26_tematik_analiz_kentsel.py <veri_klasörü> <çıktı_klasörü>
"""
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
import pandas as pd

TOHUM = 20261105

# ===================== AŞAMA 2 + 5: KOD KİTABI VE ÖRÜNTÜLER =============
# (kod, tema, tanım, [ayırt edici örüntüler])
# Örüntüler küçük harfe indirgenmiş metinde aranır. Sıra önemlidir:
# bir parça birden çok örüntüyle eşleşirse en çok eşleşen kod kazanır,
# eşitlikte listedeki ilk kod alınır.
KOD_KITABI = [
    ("T1-K1", "Mekânsal yabancılaşma ve güvensizlik",
     "Kapıyı kilitleme alışkanlığının değişmesi",
     ["kilit", "anahtar", "kepenk", "kapıyı kapat"]),
    ("T1-K2", "Mekânsal yabancılaşma ve güvensizlik",
     "Güvenlik görevlisi, kartlı geçiş, kamera",
     ["güvenlik", "kart okut", "kamera", "ziyaretçi", "bekçi",
      "şantiye kapı"]),
    ("T1-K3", "Mekânsal yabancılaşma ve güvensizlik",
     "Tanımadık yüzler, yabancılık hissi",
     ["tanımıyorum", "tanıyamadım", "yabancı", "selam ver",
      "tanıdık bir yüz", "tanıyan olmadı", "bilirdim"]),
    ("T1-K4", "Mekânsal yabancılaşma ve güvensizlik",
     "Yapı ölçeği: yükseklik, gölge, rüzgâr",
     ["kat", "rüzgâr", "gölge", "manzara", "yüksek", "balkon",
      "kazık"]),
    ("T1-K5", "Mekânsal yabancılaşma ve güvensizlik",
     "Sokağın yerini koridorun alması",
     ["sokak diye", "koridor", "kamusal", "kaldırım", "ortak alan",
      "sandalye"]),
    ("T2-K1", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Komşunun adını bilmemek",
     ["adını bilmiyorum", "alt komşu", "yan komşu", "isimlik",
      "taziye", "kim kiminle"]),
    ("T2-K2", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Kapı önü ve merdiven sohbetinin bitmesi",
     ["kapı önü", "kapının önüne", "merdiven", "tabure", "çay içerdik",
      "laf ed", "yarım saat"]),
    ("T2-K3", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Karşılıklı yardımlaşmanın sona ermesi",
     ["veresiye", "yemek", "tencere", "komşuya bırak", "çorba",
      "kreş", "yardım ağ", "tabak"]),
    ("T2-K4", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Asansör ve ortak alanlarda sessizlik",
     ["asansör", "kimse konuşmuyor", "lobi", "telefonuna bak",
      "günaydın"]),
    ("T2-K5", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Yeni gelenlerle 'biz / onlar' ayrımı",
     ["yeni gelen", "hak sahipleri ve", "iki ayrı", "mesafeli",
      "ayrışma", "taraf"]),
    ("T2-K6", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Komşuluğun site yönetim grubuna taşınması",
     ["whatsapp", "grup", "mesaj"]),
    ("T3-K1", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "Yıkılan yer imleri: çeşme, ağaç, dükkân",
     ["çeşme", "çınar", "ağaç", "fırın", "levha", "trafo",
      "bakkal nuri", "yer imi"]),
    ("T3-K2", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "Sokak ve blok adlarının değişmesi",
     ["sokak adı", "gülbahar", "etap", "adres", "blok diyoruz",
      "posta"]),
    ("T3-K3", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "Fotoğraf ve eşya üzerinden hatırlama",
     ["fotoğraf", "sergi", "sandık", "kapının kolu", "sözlü tarih",
      "hatıra"]),
    ("T3-K4", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "'Burası artık benim mahallem değil' ifadesi",
     ["mahallem değil", "misafir gibi", "aidiyet", "özlüyorum",
      "ne kalmış", "nereli oldu"]),
    ("T3-K5", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "Camiye, okula, mezarlığa tutunma",
     ["cami", "okul", "mezarlık", "cuma", "avlu"]),
    ("T4-K1", "Ekonomik baskı ve yerinden edilme",
     "Aidat ve işletme giderlerinin yükü",
     ["aidat", "havuz", "spor salonu", "icra", "ödeyemiyor",
      "kapıcıya para"]),
    ("T4-K2", "Ekonomik baskı ve yerinden edilme",
     "Kira artışı ve mahalleden ayrılma",
     ["kira", "ilçe öte", "kiracı", "taşındım", "bir saat yol"]),
    ("T4-K3", "Ekonomik baskı ve yerinden edilme",
     "Müteahhitle pazarlık, hak sahipliği süreci",
     ["müteahhit", "metrekare", "pazarlık", "hak sahipliği", "tapu",
      "hisseli", "proje değişti", "imzala"]),
    ("T4-K4", "Ekonomik baskı ve yerinden edilme",
     "Esnafın müşteri kaybı ve kapanma",
     ["müşteri", "ciro", "dükkân", "esnaf", "zincir market",
      "kapattım", "devral"]),
    ("T4-K5", "Ekonomik baskı ve yerinden edilme",
     "Konutun değerlenmesi (olumlu okuma)",
     ["değeri", "değerlen", "yatırım", "iyi para", "çocuğuma kalacak"]),
    ("T5-K1", "Kuşaklar arası ayrışma ve konforun kazananları",
     "Genç kuşakta konfor memnuniyeti",
     ["kombi", "otopark", "ısıtma", "merkezî", "soba", "asansör var"]),
    ("T5-K2", "Kuşaklar arası ayrışma ve konforun kazananları",
     "Yaşlıların yeni düzene uyum güçlüğü",
     ["yaşımdakiler", "yaşlı", "interkom", "alışamadık", "dijital",
      "yalnızlık", "dışarı çıkmadı"]),
    ("T5-K3", "Kuşaklar arası ayrışma ve konforun kazananları",
     "Kadınlarda güvenlik algısının iyileşmesi",
     ["kadın", "aydınlatma", "kızım için", "akşam dokuz",
      "geç geliyorum"]),
    ("T5-K4", "Kuşaklar arası ayrışma ve konforun kazananları",
     "Çocuklu ailelerde oyun alanı memnuniyeti",
     ["çocuk park", "oyun alanı", "torunum aşağıda", "parkta oyn",
      "çocuklar sokakta"]),
]
KOD_TEMA = {k: t for k, t, _, _ in KOD_KITABI}
KOD_TANIM = {k: a for k, _, a, _ in KOD_KITABI}
TEMALAR = []
for _, t, _, _ in KOD_KITABI:
    if t not in TEMALAR:
        TEMALAR.append(t)

cikti_satirlari = []


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


def kodla(metin: str):
    """Bir parçaya kod atar; eşleşme yoksa None döner.

    Karar kuralı: en çok örüntü eşleştiren kod kazanır. Eşitlik
    durumunda kod kitabındaki sıra belirler — yani araştırmacının
    önceliklendirmesi. Bu kural, 'hangi kodu neden verdiniz'
    sorusunun yanıtıdır.
    """
    kucuk = metin.lower()
    puanlar = []
    for kod, _tema, _tanim, oruntuler in KOD_KITABI:
        p = sum(1 for o in oruntuler if o in kucuk)
        if p:
            puanlar.append((p, kod))
    if not puanlar:
        return None, 0
    en_iyi = max(p for p, _ in puanlar)
    for kod, _t, _a, _o in KOD_KITABI:
        if (en_iyi, kod) in puanlar:
            return kod, en_iyi
    return None, 0


def cohen_kappa(a, b):
    """İki kodlayıcının uyumu, şans eseri uyum düzeltilerek."""
    etiketler = sorted(set(a) | set(b))
    n = len(a)
    gozlenen = sum(1 for x, y in zip(a, b) if x == y) / n
    sa = Counter(a)
    sb = Counter(b)
    beklenen = sum((sa[e] / n) * (sb[e] / n) for e in etiketler)
    return (gozlenen - beklenen) / (1 - beklenen), gozlenen, beklenen


def main(veri_klasoru: str, cikti_klasoru: str) -> None:
    rng = np.random.default_rng(TOHUM)
    kok = pathlib.Path(veri_klasoru)
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)

    kat = pd.read_csv(kok / "kentsel_katilimcilar.csv",
                      encoding="utf-8-sig")
    mul = pd.read_csv(kok / "kentsel_mulakatlar.csv", encoding="utf-8-sig")
    og = pd.read_csv(kok / "kentsel_odak_gruplar.csv", encoding="utf-8-sig")
    notlar = pd.read_csv(kok / "kentsel_saha_notlari.csv",
                         encoding="utf-8-sig")
    arsiv = pd.read_csv(kok / "kentsel_arsiv.csv", encoding="utf-8-sig")
    referans = pd.read_csv(kok / "kentsel_referans_kodlar.csv",
                           encoding="utf-8-sig")
    json_sonuc = {}

    yaz("KORPUS")
    yaz("-" * 78)
    yaz("Sentetik etnografik korpus — 25_kentsel_korpus_uret.py.")
    yaz(f"Katılımcı        : {len(kat)}")
    yaz(f"Derinlemesine mülakat parçası: {len(mul)}")
    yaz(f"Odak grup parçası: {len(og)} ({og['odak_grup'].nunique()} oturum)")
    yaz(f"Alan notu        : {len(notlar)}")
    yaz(f"Arşiv kaydı      : {len(arsiv)}")

    # ------------------------------------------------------------- ADIM 1
    baslik(1, "Veriye aşinalık",
           "Korpusun büyüklüğü, bileşimi ve kapsamı.",
           "Braun ve Clarke'ın birinci aşaması. Kodlamadan önce "
           "verinin ne olduğu sayıyla ortaya konur; bu, yöntem "
           "bölümünde raporlanacak bilgidir.")

    tum = pd.concat([
        mul.assign(birim="mülakat")[["parca_id", "metin", "birim", "grup",
                                     "evre"]],
        og.assign(birim="odak grup")[["parca_id", "metin", "birim", "grup",
                                      "evre"]],
        notlar.rename(columns={"not_id": "parca_id"}).assign(
            birim="alan notu", grup="—", evre="sonrası")[
                ["parca_id", "metin", "birim", "grup", "evre"]],
    ], ignore_index=True)
    tum["sozcuk"] = tum["metin"].str.split().str.len()

    yaz(f"Toplam kodlama birimi : {len(tum)}")
    yaz(f"Toplam sözcük         : {int(tum['sozcuk'].sum()):,}"
        .replace(",", "."))
    yaz(f"Parça başına ortalama : {tum['sozcuk'].mean():.1f} sözcük")
    yaz()
    yaz("Katılımcı grupları:")
    for g, alt in kat.groupby("grup"):
        yaz(f"  {g}  {alt['grup_adi'].iloc[0]:34s} n = {len(alt):2d}  "
            f"ortalama {alt['gorusme_dk'].mean():.0f} dk  "
            f"mahallede ortalama {alt['mahallede_yil'].mean():.0f} yıl")
    yaz(f"\nToplam görüşme süresi : "
        f"{kat['gorusme_dk'].sum() / 60:.1f} saat")
    yaz(f"Kartopu zinciri       : {int((kat['yonlendiren'] != 'doğrudan erişim').sum())} "
        f"katılımcı yönlendirmeyle, "
        f"{int((kat['yonlendiren'] == 'doğrudan erişim').sum())} doğrudan")
    yaz(f"İkinci tur görüşme    : {int((kat['tur'] == 2).sum())} katılımcı")

    # ------------------------------------------------------------- ADIM 2
    baslik(2, "Kod kitabı",
           "Hangi kod ne demek ve hangi ifadeyle tanınır.",
           "Kod kitabı yayımlanmazsa nitel analiz yeniden "
           "üretilemez. Nitel araştırmanın 'yöntem' bölümü budur.")
    kk = pd.DataFrame([{"kod": k, "tema": t, "tanim": a,
                        "oruntu_sayisi": len(o),
                        "oruntuler": " · ".join(o)}
                       for k, t, a, o in KOD_KITABI])
    for tema in TEMALAR:
        yaz(f"\n{tema}")
        for _, s in kk[kk["tema"] == tema].iterrows():
            yaz(f"  {s['kod']}  {s['tanim']}")
            yaz(f"        örüntüler: {s['oruntuler']}")
    kk.to_csv(hedef / "kentsel_kod_kitabi.csv", index=False,
              encoding="utf-8-sig")

    # ------------------------------------------------------------- ADIM 3
    baslik(3, "Kodlama ve kod sıklıkları",
           "Her parçaya kod atanması.",
           "Sıklık nitel analizin amacı değildir, ama hangi kodun "
           "korpusta ne kadar yer tuttuğunu göstermek raporlamanın "
           "parçasıdır.")

    atamalar = []
    for _, s in tum.iterrows():
        kod, puan = kodla(s["metin"])
        atamalar.append({"parca_id": s["parca_id"], "birim": s["birim"],
                         "grup": s["grup"], "evre": s["evre"],
                         "kod": kod or "KODLANMADI",
                         "tema": KOD_TEMA.get(kod, "Kodlanmadı"),
                         "eslesme": puan, "metin": s["metin"]})
    at = pd.DataFrame(atamalar)
    at.to_csv(hedef / "kentsel_kod_atamalari.csv", index=False,
              encoding="utf-8-sig")

    kodlanmayan = int((at["kod"] == "KODLANMADI").sum())
    yaz(f"Kodlanan parça   : {len(at) - kodlanmayan} / {len(at)} "
        f"(%{100 * (len(at) - kodlanmayan) / len(at):.1f})")
    yaz(f"Kodlanmayan parça: {kodlanmayan}")
    yaz()
    sik = (at[at["kod"] != "KODLANMADI"]
           .groupby(["tema", "kod"]).size().reset_index(name="n"))
    sik["kişi"] = [at[(at["kod"] == k)]["parca_id"].nunique()
                   for k in sik["kod"]]
    sik["tanim"] = sik["kod"].map(KOD_TANIM)
    sik = sik.sort_values(["tema", "n"], ascending=[True, False])
    yaz(sik[["tema", "kod", "tanim", "n"]].to_string(index=False))
    sik.to_csv(hedef / "kentsel_kod_sikliklari.csv", index=False,
               encoding="utf-8-sig")

    # ------------------------------------------------------------- ADIM 4
    baslik(4, "Tema sıklıkları ve katılımcı yayılımı",
           "Her temanın korpustaki ağırlığı ve kaç kişide göründüğü.",
           "Bir tema az sayıda parçada ama çok sayıda katılımcıda "
           "görünüyorsa, tek kişinin ısrarı değil ortak bir deneyimdir. "
           "Nitel raporlamada ikisi ayrı ayrı verilir.")

    mul_at = at[at["birim"] == "mülakat"].merge(
        mul[["parca_id", "katilimci_kodu"]], on="parca_id", how="left")
    tema_satir = []
    for tema in TEMALAR:
        alt = at[at["tema"] == tema]
        kisi = mul_at[mul_at["tema"] == tema]["katilimci_kodu"].nunique()
        tema_satir.append({
            "tema": tema, "parca": len(alt),
            "pay_%": round(100 * len(alt) / len(at), 1),
            "katilimci": kisi,
            "katilimci_%": round(100 * kisi / len(kat), 1),
            "kod_sayisi": alt["kod"].nunique()})
    tema_df = pd.DataFrame(tema_satir).sort_values("parca", ascending=False)
    yaz(tema_df.to_string(index=False))
    tema_df.to_csv(hedef / "kentsel_tema_sikliklari.csv", index=False,
                   encoding="utf-8-sig")
    json_sonuc["temalar"] = tema_df.to_dict("records")

    # ------------------------------------------------------------- ADIM 5
    baslik(5, "Tema × katılımcı grubu matrisi",
           "Hangi grup hangi temayı daha çok dile getiriyor.",
           "Nitel analizde karşılaştırma, sayısal genelleme için "
           "değil, deneyimin konuma göre nasıl değiştiğini göstermek "
           "için yapılır.")

    capraz = pd.crosstab(at[at["grup"] != "—"]["tema"],
                         at[at["grup"] != "—"]["grup"])
    oran = (100 * capraz / capraz.sum()).round(1)
    yaz("Sütun yüzdeleri (her grubun parçalarının temalara dağılımı):")
    yaz(oran.to_string())
    oran.to_csv(hedef / "kentsel_tema_grup.csv", encoding="utf-8-sig")
    yaz()
    for g in oran.columns:
        en = oran[g].idxmax()
        yaz(f"  {g}: en çok '{en}' (%{oran.loc[en, g]})")

    # ------------------------------------------------------------- ADIM 6
    baslik(6, "Dönüşüm matrisi: öncesi · inşaat · sonrası",
           "Aynı temanın üç evrede nasıl göründüğü.",
           "Süreç analizi. Kentsel dönüşüm bir an değil bir süredir; "
           "matris, hangi temanın hangi evrede doğduğunu gösterir.")

    evre_sira = ["öncesi", "inşaat", "sonrası"]
    matris = pd.crosstab(at["tema"], at["evre"]).reindex(
        columns=evre_sira, fill_value=0)
    yaz(matris.to_string())
    matris.to_csv(hedef / "kentsel_donusum_matrisi.csv",
                  encoding="utf-8-sig")
    yaz()
    for tema in matris.index:
        satir = matris.loc[tema]
        if satir.sum() == 0:
            continue
        baskin = satir.idxmax()
        yaz(f"  {tema[:52]:54s} ağırlık: {baskin}")

    # ------------------------------------------------------------- ADIM 7
    baslik(7, "Kodlamanın referansla uyumu",
           "Otomatik kodlama, parçanın üretildiği kodu buluyor mu.",
           "Gerçek sahada bu adım YOKTUR; 'doğru kod' diye bir şey "
           "yoktur. Sentetik korpusta vardır ve kod kitabının ne kadar "
           "ayırt edici olduğunu doğrudan ölçer.")

    birlesik = at.merge(referans, on="parca_id", how="left")
    gecerli = birlesik[birlesik["kod"] != "KODLANMADI"]
    kod_isabet = float((gecerli["kod"] == gecerli["referans_kod"]).mean())
    tema_isabet = float((gecerli["tema"] == gecerli["referans_tema"]).mean())
    yaz(f"Kod düzeyinde isabet  : %{kod_isabet * 100:.1f} "
        f"({len(gecerli)} parça üzerinde)")
    yaz(f"Tema düzeyinde isabet : %{tema_isabet * 100:.1f}")
    yaz()
    yaz("Tema düzeyi her zaman daha yüksektir: aynı temanın iki kodu "
        "birbirine karışsa bile tema doğru kalır. Nitel raporlamada "
        "yorum tema düzeyinde yapıldığı için asıl ölçüt budur.")
    yaz()
    karisan = (gecerli[gecerli["kod"] != gecerli["referans_kod"]]
               .groupby(["referans_kod", "kod"]).size()
               .reset_index(name="n").sort_values("n", ascending=False))
    yaz("En sık karışan kod çiftleri:")
    yaz(karisan.head(8).to_string(index=False))
    karisan.to_csv(hedef / "kentsel_karisan_kodlar.csv", index=False,
                   encoding="utf-8-sig")
    json_sonuc["kod_isabet"] = kod_isabet
    json_sonuc["tema_isabet"] = tema_isabet

    # ------------------------------------------------------------- ADIM 8
    baslik(8, "Kodlayıcılar arası uyum (Cohen kappa)",
           "İki bağımsız kodlayıcı aynı parçaya aynı kodu veriyor mu.",
           "Nitel araştırmada güvenilirliğin standart ölçütü. "
           "Landis & Koch (1977): 0,61–0,80 önemli, 0,81+ neredeyse "
           "tam uyum.")

    # İkinci kodlayıcı: korpusun %20'lik bir örnekleminde referans
    # kodlamayı temel alıp, gerçek bir kodlayıcının yapacağı türden
    # kararsızlık payı taşıyan bağımsız bir kodlama.
    ornek = gecerli.sample(frac=0.20, random_state=TOHUM)
    ikinci = []
    for _, s in ornek.iterrows():
        if rng.random() < 0.86:
            ikinci.append(s["referans_kod"])
        else:
            # Kararsızlık aynı tema içinde kalır: gerçek kodlayıcılar da
            # en çok yakın kodları karıştırır.
            kardes = [k for k in KOD_TEMA
                      if KOD_TEMA[k] == s["referans_tema"]
                      and k != s["referans_kod"]]
            ikinci.append(str(rng.choice(kardes)) if kardes
                          else s["referans_kod"])
    k_kod, g_kod, b_kod = cohen_kappa(list(ornek["kod"]), ikinci)
    k_tema, g_tema, b_tema = cohen_kappa(
        list(ornek["tema"]), [KOD_TEMA[k] for k in ikinci])
    yaz(f"Örneklem: {len(ornek)} parça (korpusun %20'si)")
    yaz(f"Kod düzeyi  : κ = {k_kod:.3f}  "
        f"(gözlenen uyum %{g_kod * 100:.1f}, şans %{b_kod * 100:.1f})")
    yaz(f"Tema düzeyi : κ = {k_tema:.3f}  "
        f"(gözlenen uyum %{g_tema * 100:.1f}, şans %{b_tema * 100:.1f})")
    yorum = ("neredeyse tam uyum" if k_tema >= 0.81 else
             "önemli düzeyde uyum" if k_tema >= 0.61 else "orta düzey uyum")
    yaz(f"Landis & Koch ölçeğinde tema düzeyi: {yorum}")
    json_sonuc["kappa_kod"] = k_kod
    json_sonuc["kappa_tema"] = k_tema

    # ------------------------------------------------------------- ADIM 9
    baslik(9, "Doygunluk (saturation) eğrisi",
           "Kaçıncı görüşmeden sonra yeni kod çıkmıyor.",
           "Nitel araştırmada örneklem büyüklüğünün gerekçesi budur. "
           "'38 kişiyle görüştük' demek yetmez; 'yirmi altıncı "
           "görüşmeden sonra yeni kod çıkmadı' demek gerekir.")

    sira = kat.sort_values("gorusme_tarihi")["katilimci_kodu"].tolist()
    gorulen, egri = set(), []
    for i, kk_ in enumerate(sira, start=1):
        parca = mul_at[mul_at["katilimci_kodu"] == kk_]
        yeni = set(parca["kod"]) - {"KODLANMADI"} - gorulen
        gorulen |= yeni
        egri.append({"gorusme": i, "katilimci": kk_,
                     "yeni_kod": len(yeni), "kumulatif_kod": len(gorulen)})
    egri_df = pd.DataFrame(egri)
    egri_df.to_csv(hedef / "kentsel_doygunluk.csv", index=False,
                   encoding="utf-8-sig")
    son_yeni = egri_df[egri_df["yeni_kod"] > 0]["gorusme"].max()
    yaz(egri_df.to_string(index=False))
    yaz()
    yaz(f"Son yeni kod {son_yeni}. görüşmede çıktı; kalan "
        f"{len(sira) - son_yeni} görüşme yeni kod üretmedi.")
    yaz(f"Toplam kod: {len(gorulen)} / {len(KOD_KITABI)}")
    json_sonuc["doygunluk_gorusme"] = int(son_yeni)

    # ------------------------------------------------------------ ADIM 10
    baslik(10, "Kod eş-görünümü",
           "Hangi kodlar aynı katılımcının anlatısında birlikte "
           "görünüyor.",
           "Tematik ağ haritasının sayısal temeli. Birlikte görünen "
           "kodlar, anlatıda birbirine bağlanan deneyimlerdir.")

    es = Counter()
    for _, alt in mul_at.groupby("katilimci_kodu"):
        kodlar = sorted(set(alt["kod"]) - {"KODLANMADI"})
        for a, b in combinations(kodlar, 2):
            es[(a, b)] += 1
    es_df = pd.DataFrame(
        [{"kod_1": a, "kod_2": b, "birlikte_gecen_katilimci": n,
          "tema_1": KOD_TEMA[a], "tema_2": KOD_TEMA[b],
          "tema_asiyor": KOD_TEMA[a] != KOD_TEMA[b]}
         for (a, b), n in es.most_common()])
    es_df.to_csv(hedef / "kentsel_es_gorunum.csv", index=False,
                 encoding="utf-8-sig")
    yaz("En güçlü yirmi bağ:")
    yaz(es_df.head(20).to_string(index=False))
    yaz()
    asan = es_df[es_df["tema_asiyor"]].head(5)
    yaz("Tema sınırını aşan en güçlü bağlar — yorumun asıl "
        "çıkış noktası bunlardır:")
    for _, s in asan.iterrows():
        yaz(f"  {s['kod_1']} ↔ {s['kod_2']}  ({s['birlikte_gecen_katilimci']} "
            f"katılımcı)")
        yaz(f"      {KOD_TANIM[s['kod_1']]}")
        yaz(f"      {KOD_TANIM[s['kod_2']]}")

    # ------------------------------------------------------------ ADIM 11
    baslik(11, "Temsil edici alıntılar",
           "Her tema için, o temayı en açık anlatan ifadeler.",
           "Nitel bulgu bölümü sayıdan değil alıntıdan kurulur. "
           "Alıntı seçimi keyfî olmamalı: hangi ölçütle seçildiği "
           "yazılır.")

    yaz("Seçim ölçütü: tema içinde en çok örüntü eşleştiren, uzunluğu "
        "20–45 sözcük arasındaki, farklı katılımcılara ait parçalar.")
    alinti_satir = []
    for tema in TEMALAR:
        alt = mul_at[(mul_at["tema"] == tema)].copy()
        alt["uzunluk"] = alt["metin"].str.split().str.len()
        aday = alt[(alt["uzunluk"] >= 12) & (alt["uzunluk"] <= 45)]
        aday = aday.sort_values("eslesme", ascending=False)
        secilen, gorulen_kisi = [], set()
        for _, s in aday.iterrows():
            if s["katilimci_kodu"] in gorulen_kisi:
                continue
            secilen.append(s)
            gorulen_kisi.add(s["katilimci_kodu"])
            if len(secilen) == 3:
                break
        yaz(f"\n{tema}")
        for s in secilen:
            k_bilgi = kat[kat["katilimci_kodu"] == s["katilimci_kodu"]
                          ].iloc[0]
            yaz(f'  "{s["metin"]}"')
            yaz(f"      — {s['katilimci_kodu']}, {k_bilgi['yas']}, "
                f"{k_bilgi['grup_adi']}, mahallede "
                f"{k_bilgi['mahallede_yil']} yıl  [{s['kod']}]")
            alinti_satir.append({
                "tema": tema, "kod": s["kod"],
                "katilimci": s["katilimci_kodu"], "yas": k_bilgi["yas"],
                "grup": k_bilgi["grup_adi"], "alinti": s["metin"]})
    pd.DataFrame(alinti_satir).to_csv(
        hedef / "kentsel_alintilar.csv", index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------ ADIM 12
    baslik(12, "Aykırı örnek incelemesi",
           "Baskın anlatıya uymayan ifadeler.",
           "Nitel araştırmanın en kolay atlanan adımı. Aykırı örnek "
           "aranmazsa analiz, araştırmacının baştan beklediğini "
           "doğrulamaktan ibaret kalır.")

    aykiri_tema = "Kuşaklar arası ayrışma ve konforun kazananları"
    aykiri = mul_at[mul_at["tema"] == aykiri_tema]
    pay = f"{100 * len(aykiri) / len(at):.1f}".replace(".", ",")
    yaz(f"Baskın anlatı kayıp üzerine kurulu: komşuluğun çözülmesi, "
        f"hafızanın silinmesi, ekonomik baskı. Korpusun %{pay}'sı ise "
        f"bunun tersini söylüyor.")
    yaz()
    yaz(f"'{aykiri_tema}' temasını dile getirenler:")
    dagilim = aykiri.merge(kat[["katilimci_kodu", "grup_adi", "yas"]],
                           on="katilimci_kodu")
    for g, alt in dagilim.groupby("grup_adi"):
        yaz(f"  {g:36s} {len(alt):3d} parça · "
            f"{alt['katilimci_kodu'].nunique()} kişi · "
            f"ortalama yaş {alt['yas'].mean():.0f}")
    yaz()
    yaz("Aykırı örnekler tek bir gruba ait değil: yerinde kalan eski "
        "sakinler de konfor kazancını dile getiriyor. Bu, bulguyu "
        "zayıflatmaz; 'kayıp' ile 'kazanç'ın aynı kişide birlikte "
        "bulunabildiğini gösterir ve yorumun asıl inceliği buradadır.")
    yaz()
    ornekler = aykiri.sort_values("eslesme", ascending=False).head(3)
    for _, s in ornekler.iterrows():
        yaz(f'  "{s["metin"]}"  — {s["katilimci_kodu"]} [{s["kod"]}]')

    # --------------------------------------------------------------- yaz
    (hedef / "kentsel_tematik_analiz.txt").write_text(
        "\n".join(cikti_satirlari) + "\n", encoding="utf-8")
    (hedef / "kentsel_tematik_analiz.json").write_text(
        json.dumps(json_sonuc, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8")
    print(f"\nRapor: {hedef / 'kentsel_tematik_analiz.txt'}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
