# -*- coding: utf-8 -*-
"""
08 — Tematik analiz (Braun & Clarke, 2006 — altı aşama)

Kurs 9. bölümünün çıktısıdır. 116 açık uçlu yanıt üzerinde tam bir
tematik analiz yürütür: kod kitabı, kod atamaları, temalar, sıklıklar,
temsil edici alıntılar ve kodlayıcılar arası uyum (Cohen kappa).

Kodlama kararları bu dosyanın içinde veri olarak durur. Nitel analizde
"kod kitabı" ile "ham veri" ayrı belgelerdir ve ikisi birlikte
yayımlanırsa analiz yeniden üretilebilir olur. Bu betiğin varlık nedeni
budur: kararların görünür olması.

Altı aşama:
  1. Veriye aşinalık      — yanıtların okunması (betikle ölçülemez,
                            süre ve not sayısı raporlanır)
  2. İlk kodların üretimi — KOD_KITABI
  3. Temaların aranması   — kodların temalara toplanması
  4. Temaların gözden
     geçirilmesi          — tema içi tutarlılık, tema arası ayrıklık
  5. Temaların
     tanımlanması         — her temaya ad ve tanım
  6. Raporlama            — sıklık tabloları + alıntılar

Kullanım:
  python 08_tematik_analiz.py <veri_klasörü> <çıktı_klasörü>
"""
import json
import pathlib
import sys
from collections import Counter

import pandas as pd

# ========================= AŞAMA 2 + 5: KOD KİTABI =========================
# (kod, tema, kod tanımı)
KOD_KITABI = [
    # ---- SORU 1 ----
    ("S1-L1", "Literatürle baş etme", "Tarama, ön ayıklama, ilgili kaynağı seçme"),
    ("S1-L2", "Literatürle baş etme", "Makale veya metin özetletme"),
    ("S1-L3", "Literatürle baş etme", "Anahtar kelime üretme, literatür boşluğu arama"),
    ("S1-L4", "Literatürle baş etme", "Alan dışı veya yeni bir konuya giriş yapma"),
    ("S1-D1", "Dil engelini aşma", "İngilizce yazım, dil düzeltme, redaksiyon"),
    ("S1-D2", "Dil engelini aşma", "Türkçeden İngilizceye çeviri"),
    ("S1-D3", "Dil engelini aşma", "Son okuma, yazım hatası, cümle düzeltme"),
    ("S1-D4", "Dil engelini aşma", "Öz, başlık ve anahtar kelime metinleri"),
    ("S1-V1", "Veriyi işler hâle getirme", "Analiz kodu yazma veya hata ayıklama"),
    ("S1-V2", "Veriyi işler hâle getirme", "İstatistiksel yöntem seçimi, hesap doğrulama"),
    ("S1-V3", "Veriyi işler hâle getirme", "Veri temizleme ve biçim birleştirme"),
    ("S1-V4", "Veriyi işler hâle getirme", "Grafik ve tablo üretimi, biçimlendirme"),
    ("S1-Z1", "Düşünme ortağı", "Metin planı, bölüm iskeleti çıkarma"),
    ("S1-Z2", "Düşünme ortağı", "Fikir geliştirme, araştırma sorusunu daraltma"),
    ("S1-Z3", "Düşünme ortağı", "Kendi metnini zayıf nokta için denetletme"),
    ("S1-Y1", "İdari ve yayın yükü", "Hakem cevabı, editör yazışması, idari metinler"),
    ("S1-Y2", "İdari ve yayın yükü", "Öğretim malzemesi, sunum, öğrenci desteği"),
    ("S1-Y3", "İdari ve yayın yükü", "Ölçek maddesi, nitel kodlama gibi yöntem işleri"),
    ("S1-M1", "Mesafeli duranlar", "Fayda görmeme, kullanmama veya kararsızlık"),
    # ---- SORU 2 ----
    ("S2-G1", "Güvenilirlik", "Var olmayan kaynak veya atıf uydurma"),
    ("S2-G2", "Güvenilirlik", "Yanlışı kendinden emin biçimde söyleme"),
    ("S2-G3", "Güvenilirlik", "Hesap, analiz veya yöntem hatası"),
    ("S2-G4", "Güvenilirlik", "Güncel literatürü bilmemesi"),
    ("S2-O1", "Yazarlık ve özgünlük", "Metnin kime ait olduğunun belirsizliği"),
    ("S2-O2", "Yazarlık ve özgünlük", "Katkı ve yazarlık sınırının tanımsızlığı"),
    ("S2-O3", "Yazarlık ve özgünlük", "Metinlerin benzeşmesi, üslup kaybı"),
    ("S2-O4", "Yazarlık ve özgünlük", "Yüzeysellik, derinleşmeme"),
    ("S2-V1", "Veri ve gizlilik", "Hassas veya kişisel verinin araca yüklenmesi"),
    ("S2-V2", "Veri ve gizlilik", "Yayımlanmamış verinin üçüncü tarafa gitmesi"),
    ("S2-V3", "Veri ve gizlilik", "Kullanım sözleşmelerinin bilinmemesi"),
    ("S2-K1", "Kuralsızlık", "Kurumsal politikanın bulunmaması"),
    ("S2-K2", "Kuralsızlık", "Dergi politikalarının dağınık ve farklı olması"),
    ("S2-K3", "Kuralsızlık", "Etik kurul yaklaşımının belirsizliği"),
    ("S2-K4", "Kuralsızlık", "Geri çekilme veya yaptırım riski"),
    ("S2-E1", "Öğretim ve değerlendirme", "Ödev ve tezlerin değerlendirilemezliği"),
    ("S2-E2", "Öğretim ve değerlendirme", "Öğrencinin kullanımı beyan etmemesi"),
    ("S2-E3", "Öğretim ve değerlendirme", "Hakemlik sürecinde kullanılması"),
    ("S2-B1", "Beceri ve erişim", "Kendi yazma veya düşünme becerisinin körelmesi"),
    ("S2-B2", "Beceri ve erişim", "Ücretli araçlara erişim eşitsizliği"),
    ("S2-B3", "Beceri ve erişim", "Türkçe üretim niteliğinin düşüklüğü"),
    ("S2-B4", "Beceri ve erişim", "Kurumsal hesap yokluğu, kişisel hesapla kurum işi"),
    ("S2-N1", "Kaygı duymayanlar", "Kaygı bildirmeme veya önemsememe"),
    # ---- SORU 3 ----
    ("S3-R1", "Eğitim ve rehberlik", "Uygulamalı, kendi verisiyle çalışılan eğitim"),
    ("S3-R2", "Eğitim ve rehberlik", "Alana özgü rehber (nitel, derleme, Türkçe yazım)"),
    ("S3-R3", "Eğitim ve rehberlik", "Akran desteği, deneyimliyle eşleştirme, tartışma ortamı"),
    ("S3-R4", "Eğitim ve rehberlik", "Öğrenmeye ayrılacak zaman"),
    ("S3-A1", "Erişim ve altyapı", "Kurumsal lisans ve kurumsal hesap"),
    ("S3-A2", "Erişim ve altyapı", "Kurum içinde çalışan, veriyi dışarı çıkarmayan sürüm"),
    ("S3-A3", "Erişim ve altyapı", "Veri tabanlarıyla bütünleşme"),
    ("S3-A4", "Erişim ve altyapı", "Kurumsal dil ve redaksiyon hizmeti"),
    ("S3-P1", "Yazılı politika", "Bağlayıcı kurum politikası metni"),
    ("S3-P2", "Yazılı politika", "Beyan cümlesi şablonu"),
    ("S3-P3", "Yazılı politika", "Dergi politikalarını derleyen rehber"),
    ("S3-P4", "Yazılı politika", "Yazarlık ve katkı konusunda kurum görüşü"),
    ("S3-Y1", "Yönetmelik ve denetim", "Etik kurul form ve yönergesinin güncellenmesi"),
    ("S3-Y2", "Yönetmelik ve denetim", "Tez yönetmeliğinde açık hüküm"),
    ("S3-Y3", "Yönetmelik ve denetim", "Öğrenci kullanımına ilişkin düzenleme"),
    ("S3-Y4", "Yönetmelik ve denetim", "Sözleşmelerin hukuki incelenmesi"),
    ("S3-Y5", "Yönetmelik ve denetim", "Kaynak doğrulama zorunluluğu"),
    ("S3-M1", "Yöntem desteği", "İstatistik danışmanlığı"),
    ("S3-M2", "Yöntem desteği", "Şekil ve tablo standartları"),
    ("S3-M3", "Yöntem desteği", "Üretilen kodun gözden geçirilmesi kültürü"),
    ("S3-S1", "Beklentisi olmayanlar", "Kurumdan beklenti bildirmeme"),
]

# ===================== AŞAMA 2: KOD ATAMALARI (Kodlayıcı 1) =================
# (katılımcı, soru, kodlar)
ATAMALAR = [
    ("K004", 1, ["S1-L1"]), ("K007", 1, ["S1-D1"]), ("K011", 1, ["S1-V1"]),
    ("K013", 1, ["S1-M1"]), ("K016", 1, ["S1-Z1"]), ("K019", 1, ["S1-Y1"]),
    ("K022", 1, ["S1-Y2"]), ("K025", 1, ["S1-Z3", "S1-Y1"]),
    ("K028", 1, ["S1-V3"]), ("K031", 1, ["S1-D4"]),
    ("K034", 1, ["S1-L2", "S1-L4"]), ("K037", 1, ["S1-L3"]),
    ("K040", 1, ["S1-V4"]), ("K043", 1, ["S1-Z2"]), ("K046", 1, ["S1-V4"]),
    ("K049", 1, ["S1-Y1"]), ("K052", 1, ["S1-M1"]),
    ("K055", 1, ["S1-L1", "S1-Y3"]), ("K058", 1, ["S1-V4"]),
    ("K061", 1, ["S1-Z3"]), ("K064", 1, ["S1-V2"]), ("K067", 1, ["S1-M1"]),
    ("K070", 1, ["S1-Y2"]), ("K073", 1, ["S1-D2"]), ("K076", 1, ["S1-Y1"]),
    ("K079", 1, ["S1-L3"]), ("K082", 1, ["S1-Y2"]), ("K085", 1, ["S1-Y3"]),
    ("K088", 1, ["S1-D3"]), ("K091", 1, ["S1-Z2"]),
    ("K094", 1, ["S1-L1", "S1-D1"]), ("K097", 1, ["S1-V4"]),
    ("K100", 1, ["S1-Y2"]), ("K103", 1, ["S1-L4"]), ("K106", 1, ["S1-V1"]),
    ("K109", 1, ["S1-Y1"]), ("K112", 1, ["S1-L3"]), ("K115", 1, ["S1-M1"]),
    ("K118", 1, ["S1-Y3"]), ("K121", 1, ["S1-Z2"]), ("K124", 1, ["S1-V2"]),
    ("K127", 1, ["S1-M1"]), ("K130", 1, ["S1-D4"]), ("K133", 1, ["S1-L2"]),

    ("K004", 2, ["S2-G1"]), ("K007", 2, ["S2-O1", "S2-K1"]),
    ("K010", 2, ["S2-V1"]), ("K013", 2, ["S2-O1"]),
    ("K016", 2, ["S2-K1", "S2-K2"]), ("K019", 2, ["S2-E1"]),
    ("K022", 2, ["S2-B1"]), ("K025", 2, ["S2-B2"]),
    ("K028", 2, ["S2-K4"]), ("K031", 2, ["S2-N1"]),
    ("K034", 2, ["S2-G2"]), ("K037", 2, ["S2-E3"]), ("K040", 2, ["S2-B1"]),
    ("K043", 2, ["S2-V2", "S2-V3"]), ("K046", 2, ["S2-O3"]),
    ("K049", 2, ["S2-K3"]), ("K052", 2, ["S2-N1"]),
    ("K055", 2, ["S2-G2", "S2-K1"]), ("K058", 2, ["S2-B3"]),
    ("K061", 2, ["S2-G2"]), ("K064", 2, ["S2-G3"]), ("K067", 2, ["S2-O4"]),
    ("K070", 2, ["S2-E2"]), ("K073", 2, ["S2-G3"]), ("K076", 2, ["S2-B4"]),
    ("K079", 2, ["S2-G4"]), ("K082", 2, ["S2-N1"]),
    ("K085", 2, ["S2-O1"]), ("K088", 2, ["S2-O2"]), ("K091", 2, ["S2-O2"]),
    ("K094", 2, ["S2-K2"]), ("K097", 2, ["S2-G3"]), ("K100", 2, ["S2-E1"]),
    ("K103", 2, ["S2-G2"]), ("K106", 2, ["S2-G3"]), ("K112", 2, ["S2-G1"]),
    ("K118", 2, ["S2-O2"]), ("K124", 2, ["S2-G3"]), ("K127", 2, ["S2-N1"]),
    ("K130", 2, ["S2-G1"]),

    ("K004", 3, ["S3-R1"]), ("K007", 3, ["S3-A1"]), ("K010", 3, ["S3-A2"]),
    ("K013", 3, ["S3-P1"]), ("K016", 3, ["S3-P1"]), ("K019", 3, ["S3-Y3"]),
    ("K022", 3, ["S3-S1"]), ("K025", 3, ["S3-P2"]), ("K028", 3, ["S3-P3"]),
    ("K031", 3, ["S3-A1", "S3-R1"]), ("K034", 3, ["S3-Y5"]),
    ("K037", 3, ["S3-P1"]), ("K040", 3, ["S3-R4"]), ("K043", 3, ["S3-Y4"]),
    ("K046", 3, ["S3-Y1"]), ("K049", 3, ["S3-Y1"]), ("K052", 3, ["S3-R1"]),
    ("K055", 3, ["S3-R2"]), ("K058", 3, ["S3-R2"]), ("K061", 3, ["S3-R3"]),
    ("K064", 3, ["S3-M1"]), ("K070", 3, ["S3-Y2"]), ("K073", 3, ["S3-A4"]),
    ("K076", 3, ["S3-A1"]), ("K079", 3, ["S3-A3"]), ("K082", 3, ["S3-R3"]),
    ("K085", 3, ["S3-R2"]), ("K091", 3, ["S3-P4"]), ("K097", 3, ["S3-M2"]),
    ("K106", 3, ["S3-M3"]), ("K112", 3, ["S3-Y5"]),
    ("K130", 3, ["S3-A1", "S3-R1", "S3-P1"]),
]

# ============ AŞAMA 4: İKİNCİ KODLAYICI (bağımsız ikinci okuma) ============
# Toplam yanıtın %26'sı (30 yanıt) ikinci bir okumayla, birinci okuma
# görülmeden kodlanmıştır. Uyum Cohen kappa ile ölçülür. Her iki okumada
# yanıta atanan BASKIN TEMA karşılaştırılır.
IKINCI_KODLAYICI = {
    ("K004", 1): "Literatürle baş etme",
    ("K011", 1): "Veriyi işler hâle getirme",
    ("K016", 1): "Düşünme ortağı",
    ("K025", 1): "Düşünme ortağı",
    ("K031", 1): "Dil engelini aşma",
    ("K034", 1): "Literatürle baş etme",
    ("K049", 1): "İdari ve yayın yükü",
    ("K055", 1): "Literatürle baş etme",
    ("K064", 1): "Veriyi işler hâle getirme",
    ("K085", 1): "Düşünme ortağı",            # ← farklı (K1: İdari ve yayın yükü)
    ("K094", 1): "Dil engelini aşma",         # ← farklı (K1: Literatürle baş etme)
    ("K121", 1): "Düşünme ortağı",
    ("K007", 2): "Yazarlık ve özgünlük",
    ("K016", 2): "Kuralsızlık",
    ("K022", 2): "Beceri ve erişim",
    ("K034", 2): "Güvenilirlik",
    ("K043", 2): "Veri ve gizlilik",
    ("K055", 2): "Güvenilirlik",
    ("K067", 2): "Yazarlık ve özgünlük",
    ("K070", 2): "Öğretim ve değerlendirme",
    ("K088", 2): "Yazarlık ve özgünlük",
    ("K103", 2): "Güvenilirlik",
    ("K112", 2): "Güvenilirlik",
    ("K130", 2): "Güvenilirlik",
    ("K004", 3): "Eğitim ve rehberlik",
    ("K013", 3): "Yönetmelik ve denetim",     # ← farklı (K1: Yazılı politika)
    ("K031", 3): "Erişim ve altyapı",
    ("K058", 3): "Eğitim ve rehberlik",
    ("K097", 3): "Yöntem desteği",
    ("K130", 3): "Erişim ve altyapı",
}

# Aşama 1 — veriye aşinalık adımının kaydı (betikle ölçülemeyen emek)
ASINALIK_KAYDI = {
    "okuma_turu": 2,
    "not_sayisi": 41,
    "harcanan_sure_dakika": 95,
    "aciklama": "Yanıtların tamamı iki kez okundu; ilk okumada kod "
                "üretilmedi, yalnız kenar notu alındı. Kodlar ikinci "
                "okumada üretildi.",
}


def cohen_kappa(a: list, b: list) -> dict:
    """Cohen kappa — iki kodlayıcının uyumunun rastlantı düzeltilmiş ölçüsü.

    kappa = (gözlenen uyum − beklenen uyum) / (1 − beklenen uyum)

    Yüzde uyum tek başına yetmez: iki kodlayıcı her şeye aynı yaygın
    temayı verse de yüzde uyum yüksek çıkar. Kappa, rastlantıyla
    beklenecek uyumu düşer.
    """
    n = len(a)
    gozlenen = sum(x == y for x, y in zip(a, b)) / n
    sa, sb = Counter(a), Counter(b)
    beklenen = sum((sa[k] / n) * (sb[k] / n) for k in set(a) | set(b))
    kappa = (gozlenen - beklenen) / (1 - beklenen)
    if kappa < 0.40:
        yorum = "zayıf"
    elif kappa < 0.60:
        yorum = "orta"
    elif kappa < 0.75:
        yorum = "iyi"
    else:
        yorum = "çok iyi"
    return {"n": n, "gözlenen_uyum": round(gozlenen, 4),
            "beklenen_uyum": round(beklenen, 4), "kappa": round(kappa, 4),
            "yorum": yorum}


def main(veri_klasoru: str, cikti_klasoru: str) -> None:
    kaynak = pathlib.Path(veri_klasoru)
    yanitlar = pd.read_csv(kaynak / "anket_acik_uclu.csv",
                           encoding="utf-8-sig")
    kod_df = pd.DataFrame(KOD_KITABI, columns=["kod", "tema", "tanim"])
    kod_tema = dict(zip(kod_df["kod"], kod_df["tema"]))

    satirlar = []

    def yaz(m=""):
        satirlar.append(m)
        print(m)

    yaz("=" * 78)
    yaz("TEMATİK ANALİZ — Braun & Clarke (2006) altı aşama")
    yaz("=" * 78)
    yaz(f"Veri: {len(yanitlar)} açık uçlu yanıt, "
        f"{int(yanitlar['kelime'].sum()):,} kelime, "
        f"{yanitlar['katilimci_no'].nunique()} katılımcı")
    yaz("UYARI — Metinler sentetiktir; yöntem göstermek için yazılmıştır.")
    yaz()

    # ---------------------------------------------------------- AŞAMA 1
    yaz("AŞAMA 1 — Veriye aşinalık")
    yaz("-" * 78)
    yaz(f"Okuma turu : {ASINALIK_KAYDI['okuma_turu']}")
    yaz(f"Kenar notu : {ASINALIK_KAYDI['not_sayisi']}")
    yaz(f"Süre       : {ASINALIK_KAYDI['harcanan_sure_dakika']} dakika")
    yaz(ASINALIK_KAYDI["aciklama"])
    yaz()

    # ---------------------------------------------------------- AŞAMA 2
    yaz("AŞAMA 2 — İlk kodların üretimi")
    yaz("-" * 78)
    atama_df = pd.DataFrame(
        [{"katilimci_no": k, "soru_no": s, "kod": kod,
          "tema": kod_tema[kod]}
         for k, s, kodlar in ATAMALAR for kod in kodlar])
    yaz(f"Üretilen kod sayısı      : {len(kod_df)}")
    yaz(f"Yapılan kod ataması      : {len(atama_df)}")
    yaz(f"Yanıt başına ortalama kod: "
        f"{len(atama_df) / len(ATAMALAR):.2f}")
    yaz(f"Çok kodlu yanıt sayısı   : "
        f"{sum(1 for _, _, k in ATAMALAR if len(k) > 1)}")
    yaz()

    # ---------------------------------------------------------- AŞAMA 3
    yaz("AŞAMA 3 — Kodların temalara toplanması")
    yaz("-" * 78)
    for soru in sorted(yanitlar["soru_no"].unique()):
        alt_kod = kod_df[kod_df["kod"].str.startswith(f"S{soru}-")]
        yaz(f"Soru {soru}: {alt_kod['kod'].nunique()} kod → "
            f"{alt_kod['tema'].nunique()} tema")
        for tema in alt_kod["tema"].unique():
            kodlari = alt_kod.loc[alt_kod["tema"] == tema, "kod"].tolist()
            yaz(f"   {tema:30s} ← {', '.join(kodlari)}")
        yaz()

    # ------------------------------------------------- AŞAMA 4 (güvenilirlik)
    yaz("AŞAMA 4 — Temaların gözden geçirilmesi: kodlayıcılar arası uyum")
    yaz("-" * 78)
    # Her yanitin baskin temasi: ilk atanan kodun temasi
    baskin = {(k, s): kod_tema[kodlar[0]] for k, s, kodlar in ATAMALAR}
    anahtar = [a for a in IKINCI_KODLAYICI if a in baskin]
    k1 = [baskin[a] for a in anahtar]
    k2 = [IKINCI_KODLAYICI[a] for a in anahtar]
    uyum = cohen_kappa(k1, k2)
    yaz(f"İkinci okumaya alınan yanıt: {uyum['n']} "
        f"(tüm yanıtların %{100 * uyum['n'] / len(ATAMALAR):.0f}'sı)")
    yaz(f"Gözlenen uyum : %{100 * uyum['gözlenen_uyum']:.1f}")
    yaz(f"Beklenen uyum : %{100 * uyum['beklenen_uyum']:.1f} "
        f"(rastlantıyla)")
    yaz(f"Cohen kappa   : {uyum['kappa']}  → {uyum['yorum']} uyum")
    yaz()
    yaz("Uyuşmayan yanıtlar ve iki okumanın gerekçeleri:")
    for a in anahtar:
        if baskin[a] != IKINCI_KODLAYICI[a]:
            metin = yanitlar.loc[
                (yanitlar["katilimci_no"] == a[0])
                & (yanitlar["soru_no"] == a[1]), "yanit"].iloc[0]
            yaz(f"  {a[0]} / S{a[1]}")
            yaz(f"    1. okuma: {baskin[a]}")
            yaz(f"    2. okuma: {IKINCI_KODLAYICI[a]}")
            yaz(f"    yanıt   : «{metin[:110]}…»")
    yaz()
    yaz("Uyuşmazlıkların üçü de SINIR yanıtlarda. Bu yanıtlar iki temaya")
    yaz("da değiyor; kappa'nın 1,00 olmaması bir hata değil, kodlama")
    yaz("kararının yorum içerdiğinin kanıtıdır. Raporda uyuşmazlıkların")
    yaz("nasıl çözüldüğü yazılır: burada üçü de tartışılıp birinci")
    yaz("okumanın kodu korunmuştur.")
    yaz()

    # ---------------------------------------------------- AŞAMA 5 + 6
    yaz("AŞAMA 5–6 — Tema tanımları, sıklıklar ve alıntılar")
    yaz("=" * 78)
    tema_ozet = []
    for soru in sorted(yanitlar["soru_no"].unique()):
        soru_metni = yanitlar.loc[yanitlar["soru_no"] == soru,
                                  "soru_metni"].iloc[0]
        soru_atama = atama_df[atama_df["soru_no"] == soru]
        soru_yanit_sayisi = int((yanitlar["soru_no"] == soru).sum())
        yaz()
        yaz(f"SORU {soru} — {soru_metni}")
        yaz(f"(yanıt sayısı: {soru_yanit_sayisi})")
        yaz("-" * 78)
        temalar = (soru_atama.groupby("tema")["katilimci_no"]
                   .nunique().sort_values(ascending=False))
        for tema, kisi in temalar.items():
            kod_sayilari = Counter(
                soru_atama.loc[soru_atama["tema"] == tema, "kod"])
            yaz(f"▸ {tema}")
            yaz(f"  katılımcı: {kisi}/{soru_yanit_sayisi} "
                f"(%{100 * kisi / soru_yanit_sayisi:.0f})   "
                f"kod ataması: {sum(kod_sayilari.values())}")
            en_sik = kod_sayilari.most_common(3)
            yaz("  en sık kodlar: " + ", ".join(
                f"{k} ({v})" for k, v in en_sik))
            # temsil edici alinti: temaya ait en uzun yanit
            adaylar = soru_atama.loc[soru_atama["tema"] == tema,
                                     "katilimci_no"].unique()
            alt = yanitlar[(yanitlar["soru_no"] == soru)
                           & (yanitlar["katilimci_no"].isin(adaylar))]
            if len(alt):
                secili = alt.loc[alt["kelime"].idxmax()]
                yaz(f"  alıntı ({secili['katilimci_no']}): "
                    f"«{secili['yanit']}»")
            tema_ozet.append({
                "soru_no": int(soru), "tema": tema,
                "katilimci": int(kisi),
                "soru_yanit_sayisi": soru_yanit_sayisi,
                "yuzde": round(100 * kisi / soru_yanit_sayisi, 1),
                "kod_atamasi": int(sum(kod_sayilari.values())),
                "kodlar": [{"kod": k, "sıklık": v}
                           for k, v in kod_sayilari.most_common()],
                "alinti_katilimci": secili["katilimci_no"] if len(alt) else "",
                "alinti": secili["yanit"] if len(alt) else ""})
            yaz()

    # --------------------------------------------------------------- kayıt
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    sonuc = {
        "veri": {"yanit": len(yanitlar),
                 "kelime": int(yanitlar["kelime"].sum()),
                 "katilimci": int(yanitlar["katilimci_no"].nunique()),
                 "sentetik": True},
        "asinalik": ASINALIK_KAYDI,
        "kod_kitabi": kod_df.to_dict("records"),
        "atamalar": atama_df.to_dict("records"),
        "kod_sayisi": len(kod_df),
        "atama_sayisi": len(atama_df),
        "cok_kodlu_yanit": sum(1 for _, _, k in ATAMALAR if len(k) > 1),
        "kodlayici_uyumu": uyum,
        "uyusmazliklar": [
            {"katilimci": a[0], "soru": a[1], "okuma_1": baskin[a],
             "okuma_2": IKINCI_KODLAYICI[a]}
            for a in anahtar if baskin[a] != IKINCI_KODLAYICI[a]],
        "temalar": tema_ozet,
    }
    (hedef / "tematik_analiz.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    (hedef / "tematik_analiz.txt").write_text(
        "\n".join(satirlar), encoding="utf-8-sig")
    kod_df.to_csv(hedef / "tematik_kod_kitabi.csv", index=False,
                  encoding="utf-8-sig")
    atama_df.to_csv(hedef / "tematik_kod_atamalari.csv", index=False,
                    encoding="utf-8-sig")
    yaz("=" * 78)
    yaz(f"Yazıldı: {hedef / 'tematik_analiz.json'}")
    yaz(f"         {hedef / 'tematik_kod_kitabi.csv'}")
    yaz(f"         {hedef / 'tematik_kod_atamalari.csv'}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
