# -*- coding: utf-8 -*-
"""
21 — İktisat ve işletme örneği: uzaktan çalışma anketi veri üretimi

!!! BU VERİ SETİ SENTETİKTİR. !!!
Gerçek bir alan araştırmasından gelmemiştir; yöntem öğretmek için
üretilmiştir. İçindeki hiçbir katsayı bir bulgu olarak alıntılanamaz.

Neden sentetik: beyaz yaka çalışanlardan toplanmış, örgütsel bağlılık ve
verimlilik ölçekleri içeren, kişisel veri barındırmayan ve açık lisansla
dağıtılabilen bir Türkçe mikro veri seti kamuya açık değildir. Yapısal
eşitlik modellemesi öğretmek için ayrıca GEREKEN bir şey daha var:
modelin gerçek katsayılarının BİLİNMESİ. Ancak o zaman "analiz doğru
kuruldu mu" sorusu yanıtlanabilir — tahmin edilen katsayı, veriyi üreten
katsayıya yakınsa yöntem çalışıyordur.

ÜRETİM MODELİ — dört örtük değişken üzerine kurulu bir yol modeli

    UCE  Uzaktan Çalışma Esnekliği   (dışsal / exogenous)
    IYD  İş–Yaşam Dengesi            (aracı / mediator)
    OB   Örgütsel Bağlılık           (aracı / mediator)
    CV   Çalışan Verimliliği         (içsel / endogenous, sonuç)

Yapısal katsayılar (standartlaştırılmış, GERÇEK değerler):

    UCE → IYD   0,52        IYD → OB    0,31
    UCE → OB    0,34        IYD → CV    0,18
    UCE → CV    0,22        OB  → CV    0,41

Buradan türeyen etkiler:
    UCE → CV doğrudan           0,220
    UCE → CV dolaylı            0,52·0,18 + 0,34·0,41 + 0,52·0,31·0,41
                              = 0,0936 + 0,1394 + 0,0661 = 0,299
    UCE → CV toplam             0,519
Yani ilişki KISMİ ARACILIK taşır: doğrudan yol anlamlı kalır ama
etkinin yarıdan fazlası aracı değişkenler üzerinden akar. H2 bunu
test eder.

Ölçüm modeli: her örtük değişken için 5–6 madde, faktör yükleri
0,69–0,90 arasında. Maddeler sürekli örtük skordan üretilir, sonra
eşik değerlerle 1–5 Likert ölçeğine indirgenir. Üç madde ters kodludur.

İKİNCİL VERİ: insan kaynakları performans kaydı. Yıllık değerlendirme
puanı, örtük CV ile r ≈ 0,45 düzeyinde ilişkilidir — mükemmel değil.
Bu bilerek böyle: öz-bildirim verimlilik ile kurumsal kayıt aynı şey
değildir ve aradaki fark ortak yöntem yanlılığı (common method bias)
tartışmasının somut dayanağıdır.

ÇIKTI
  uzaktan_ham.csv          ham form çıktısı — eksik hücre, tutarsız
                           kategori yazımı, dikkatsiz doldurma, mükerrer
                           kayıt, aralık dışı değer içerir
  uzaktan_ik_kayitlari.csv ikincil veri: İK performans kayıtları
  uzaktan_madde_sozlugu.csv hangi madde hangi ölçekte, ters kodlu mu
  uzaktan_gercek_parametreler.csv  veriyi üreten gerçek katsayılar

Temiz dosya ayrı bir betikle (22_uzaktan_temizle.py) üretilir.

Kullanım:
  python 21_uzaktan_veri_uret.py <çıktı_klasörü>
"""
import pathlib
import sys

import numpy as np
import pandas as pd

TOHUM = 20261104
N = 1480          # ham satır sayısı; temizlikten sonra ~1.340 kalır

rng = np.random.default_rng(TOHUM)

# ------------------------------------------------------------- yapısal yol
# (kaynak, hedef, standartlaştırılmış katsayı)
YOLLAR = [
    ("UCE", "IYD", 0.52),
    ("UCE", "OB",  0.34),
    ("UCE", "CV",  0.22),
    ("IYD", "OB",  0.31),
    ("IYD", "CV",  0.18),
    ("OB",  "CV",  0.41),
]

# --------------------------------------------------------------- maddeler
# (kod, metin, örtük değişken, faktör yükü, eşik kayması, ters kodlu mu)
MADDELER = [
    # --- Uzaktan Çalışma Esnekliği ---------------------------------------
    ("UCE1", "Çalışma saatlerimi kendi günlük düzenime göre "
             "ayarlayabiliyorum.", "UCE", 0.86, 0.10, False),
    ("UCE2", "Hangi gün ofiste, hangi gün evde çalışacağıma ben karar "
             "veriyorum.", "UCE", 0.84, -0.15, False),
    ("UCE3", "İşimi yürütmek için gereken dijital altyapıya evden de "
             "erişebiliyorum.", "UCE", 0.76, 0.45, False),
    ("UCE4", "Yöneticim, uzaktan çalıştığım günlerde beni saat saat "
             "denetlemiyor.", "UCE", 0.79, 0.20, False),
    ("UCE5T", "Uzaktan çalışma düzenimiz kâğıt üstünde esnek, "
              "uygulamada değil.", "UCE", 0.72, -0.05, True),

    # --- İş–Yaşam Dengesi -------------------------------------------------
    ("IYD1", "Evden çalışırken iş ile özel yaşamım arasında sınır "
             "kurabiliyorum.", "IYD", 0.86, 0.05, False),
    ("IYD2", "Çalışma düzenim ailevi sorumluluklarımı yerine getirmeme "
             "izin veriyor.", "IYD", 0.83, 0.15, False),
    ("IYD3", "İş gününün bittiği saati kendim belirleyebiliyorum.",
     "IYD", 0.78, -0.20, False),
    ("IYD4T", "Mesai bittikten sonra da iş yazışmalarına yanıt vermek "
              "zorunda hissediyorum.", "IYD", 0.80, -0.10, True),
    ("IYD5", "Yolda geçirmediğim süreyi kendime ayırabiliyorum.",
     "IYD", 0.71, 0.35, False),

    # --- Örgütsel Bağlılık ------------------------------------------------
    ("OB1", "Kariyerimin geri kalanını bu kurumda geçirmek beni mutlu "
            "eder.", "OB", 0.87, -0.25, False),
    ("OB2", "Bu kurumun sorunlarını kendi sorunum gibi hissediyorum.",
     "OB", 0.83, -0.05, False),
    ("OB3", "Kurumumdan dışarıda söz ederken kendimi onun bir parçası "
            "olarak anlatıyorum.", "OB", 0.81, 0.10, False),
    ("OB4", "Bu kuruma karşı duygusal bir bağ hissediyorum.",
     "OB", 0.90, 0.00, False),
    ("OB5T", "Benzer koşullarda bir teklif gelse hemen ayrılırım.",
     "OB", 0.77, -0.30, True),
    ("OB6", "Kurumun değerleri ile kendi değerlerim örtüşüyor.",
     "OB", 0.81, 0.05, False),

    # --- Çalışan Verimliliği (algılanan) ----------------------------------
    ("CV1", "Üstlendiğim işleri verilen sürede tamamlıyorum.",
     "CV", 0.81, 0.50, False),
    ("CV2", "Uzaktan çalıştığım günlerde daha az bölünüyorum.",
     "CV", 0.77, -0.10, False),
    ("CV3", "Çıkardığım işin niteliğinden memnunum.", "CV", 0.85, 0.30,
     False),
    ("CV4", "Bir iş gününde planladığım işlerin tamamına yakınını "
            "bitiriyorum.", "CV", 0.83, 0.05, False),
    ("CV5", "Zor bir görevle karşılaştığımda çözüm üretme hızım yüksek.",
     "CV", 0.69, 0.15, False),
]

ORTUK = ["UCE", "IYD", "OB", "CV"]

# --------------------------------------------------------------- demografi
SEKTOR = {"Yazılım ve bilişim": 0.42, "Finans ve sigortacılık": 0.33,
          "Danışmanlık": 0.15, "Telekomünikasyon": 0.10}
EGITIM = {"Ön lisans": 0.08, "Lisans": 0.54, "Yüksek lisans": 0.31,
          "Doktora": 0.07}
UNVAN = {"Uzman": 0.46, "Kıdemli uzman": 0.27, "Takım lideri": 0.17,
         "Yönetici": 0.10}
SEHIR = {"İstanbul": 0.52, "Ankara": 0.19, "İzmir": 0.11,
         "Kocaeli": 0.07, "Diğer": 0.11}


def kategori(sozluk, n):
    return rng.choice(list(sozluk), size=n, p=list(sozluk.values()))


def main(cikti_klasoru: str) -> None:
    # ---------------------------------------------- örtük değişken skorları
    # Yapısal model, artık (residual) varyansları standartlaştırılmış
    # değişkenlere göre hesaplanacak biçimde sırayla çözülür. Her içsel
    # değişkenin varyansı 1 olsun isteniyor; bu yüzden artık varyans
    # 1 − açıklanan varyans olarak alınır.
    eta = {}
    eta["UCE"] = rng.standard_normal(N)

    def kur(hedef, girdiler):
        pay = np.zeros(N)
        for kaynak, kat in girdiler:
            pay += kat * eta[kaynak]
        aciklanan = float(np.var(pay))
        artik_sd = np.sqrt(max(1.0 - aciklanan, 0.05))
        eta[hedef] = pay + artik_sd * rng.standard_normal(N)
        # Standartlaştır: örneklem varyansı tam 1 olsun, böylece
        # beklenen katsayılar standartlaştırılmış katsayılarla kıyaslanır
        eta[hedef] = (eta[hedef] - eta[hedef].mean()) / eta[hedef].std()

    kur("IYD", [("UCE", 0.52)])
    kur("OB",  [("UCE", 0.34), ("IYD", 0.31)])
    kur("CV",  [("UCE", 0.22), ("IYD", 0.18), ("OB", 0.41)])

    # ------------------------------------------------------- madde yanıtları
    # Sürekli madde skoru: yük · örtük + benzersiz hata. Sonra beşli
    # ölçeğe indirgenir. Eşikler standart normalin yüzdeliklerinden
    # türetilir; "kayma" maddenin kolaylığını/zorluğunu kaydırır.
    temel_esik = np.array([-1.25, -0.45, 0.30, 1.05])
    satirlar = {}
    for kod, _metin, ortuk, yuk, kayma, ters in MADDELER:
        surekli = yuk * eta[ortuk] + np.sqrt(1 - yuk ** 2) * \
            rng.standard_normal(N)
        esikler = temel_esik + kayma
        puan = np.digitize(surekli, esikler) + 1  # 1..5
        if ters:
            puan = 6 - puan
        satirlar[kod] = puan.astype(float)

    df = pd.DataFrame(satirlar)

    # ------------------------------------------------------------ demografi
    yas = np.clip(rng.normal(35.5, 7.8, N), 22, 63).round().astype(int)
    kidem = np.clip((yas - 23) * rng.uniform(0.15, 0.55, N), 0.5, 28)
    # Uzaktan çalışılan yıl pandemiyle başlar: en çok 6 yıl
    uzaktan_yil = np.clip(rng.gamma(2.2, 1.35, N), 0.5, 6).round(1)
    # Haftalık uzaktan gün, esneklikle ilişkili olsun (ama belirlemesin)
    egilim = 2.6 + 0.85 * eta["UCE"] + rng.normal(0, 0.9, N)
    uzaktan_gun = np.clip(np.round(egilim), 0, 5).astype(int)

    df.insert(0, "katilimci_no", np.arange(1001, 1001 + N))
    df["yas"] = yas
    df["cinsiyet"] = rng.choice(["Kadın", "Erkek", "Belirtmek istemiyorum"],
                                N, p=[0.44, 0.53, 0.03])
    df["egitim"] = kategori(EGITIM, N)
    df["sektor"] = kategori(SEKTOR, N)
    df["unvan"] = kategori(UNVAN, N)
    df["sehir"] = kategori(SEHIR, N)
    df["kidem_yil"] = kidem.round(1)
    df["uzaktan_yil"] = uzaktan_yil
    df["haftalik_uzaktan_gun"] = uzaktan_gun
    df["cocuk_var"] = rng.choice(["Evet", "Hayır"], N, p=[0.46, 0.54])
    df["calisma_modeli"] = np.where(
        uzaktan_gun >= 4, "Tam uzaktan",
        np.where(uzaktan_gun >= 1, "Hibrit", "Tam ofis"))
    # Formun doldurulma süresi (saniye): dikkatsiz doldurma göstergesi
    df["doldurma_sn"] = np.clip(
        rng.lognormal(np.log(430), 0.42, N), 45, 4200).round().astype(int)
    df["kurum_kod"] = rng.choice([f"K{i:02d}" for i in range(1, 29)], N)

    # -------------------------------------------- dikkat kontrol maddesi
    # "Bu soruyu okuduğunuzu göstermek için 2 işaretleyiniz."
    # Dikkatli katılımcı 2 yazar; dalgın olan rastgele bir şey.
    dikkatli = rng.random(N) > 0.052
    df["DK1"] = np.where(dikkatli, 2, rng.integers(1, 6, N))

    # --------------------------------------------------- ikincil veri: İK
    # Yıllık performans puanı (0–100). Örtük CV ile ilişkili ama onunla
    # aynı değil: amir değerlendirmesi başka bir ölçüm kaynağıdır.
    ik_gurultu = rng.standard_normal(N)
    ik_surekli = 0.45 * eta["CV"] + 0.12 * eta["OB"] + \
        np.sqrt(1 - 0.45 ** 2 - 0.12 ** 2) * ik_gurultu
    ik = pd.DataFrame({
        "katilimci_no": df["katilimci_no"],
        "kurum_kod": df["kurum_kod"],
        "yillik_performans_puani": np.clip(
            72 + 9.5 * ik_surekli, 35, 100).round(1),
        "tamamlanan_proje_12ay": np.clip(
            rng.poisson(5.4 + 1.3 * np.clip(ik_surekli, -2, 2)), 0, 22),
        "devamsizlik_gun_12ay": np.clip(
            rng.poisson(np.clip(4.2 - 0.9 * ik_surekli, 0.4, 12)), 0, 30),
        "egitim_saati_12ay": np.clip(
            rng.normal(28 + 4 * ik_surekli, 11), 0, 90).round(0),
    })
    # İK kayıtlarının bir kısmı eşleşmiyor: kurum veriyi paylaşmadı
    eslesmeyen = rng.choice(N, int(N * 0.18), replace=False)
    ik = ik.drop(index=eslesmeyen).reset_index(drop=True)

    df = df.astype(object)

    # ====================================================== ham veri kirleri
    madde_kodlari = [m[0] for m in MADDELER]

    # 1) Dikkatsiz doldurma: düz çizgi (straightlining).
    #    Katılımcı bütün maddelere aynı yanıtı vermiş.
    duz = rng.choice(N, 46, replace=False)
    for i in duz:
        sabit = int(rng.integers(1, 6))
        for k in madde_kodlari:
            df.at[i, k] = float(sabit)
        df.at[i, "doldurma_sn"] = int(rng.integers(48, 150))

    # 2) Zıt örüntü: ters kodlu maddelerle düz maddeler çelişiyor
    celiskili = rng.choice([i for i in range(N) if i not in duz], 31,
                           replace=False)
    for i in celiskili:
        for k in ("UCE5T", "IYD4T", "OB5T"):
            df.at[i, k] = df.at[i, k.replace("T", "").replace("5", "1")
                                .replace("4", "1")]

    # 3) Kategori yazımı üç farklı formda girilmiş
    yazim = {
        "cinsiyet": {"Kadın": ["kadın", "KADIN", "Kadin"],
                     "Erkek": ["erkek", "ERKEK", " Erkek"]},
        "egitim": {"Lisans": ["lisans", "Lisans ", "LİSANS"],
                   "Yüksek lisans": ["yüksek lisans", "Y. Lisans",
                                     "Yuksek Lisans"]},
        "sektor": {"Yazılım ve bilişim": ["Yazılım", "yazılım ve bilişim",
                                          "Bilişim"]},
    }
    for sutun, harita in yazim.items():
        for dogru, varyantlar in harita.items():
            adaylar = df.index[df[sutun] == dogru]
            if len(adaylar) == 0:
                continue
            secim = rng.choice(adaylar, min(34, len(adaylar)), replace=False)
            for i in secim:
                df.at[i, sutun] = str(rng.choice(varyantlar))

    # 4) Aralık dışı değerler: form doğrulaması yokmuş
    for i in rng.choice(N, 9, replace=False):
        df.at[i, rng.choice(madde_kodlari)] = float(rng.choice([0, 6, 55]))
    for i in rng.choice(N, 5, replace=False):
        df.at[i, "yas"] = int(rng.choice([17, 199, 0]))

    # 5) Eksik hücreler
    for sutun, adet in [("OB3", 23), ("CV5", 19), ("IYD5", 17),
                        ("egitim", 12), ("kidem_yil", 15),
                        ("haftalik_uzaktan_gun", 8)]:
        for i in rng.choice(N, adet, replace=False):
            df.at[i, sutun] = np.nan

    # 6) Mükerrer kayıt: aynı kişi formu iki kez göndermiş
    cift = rng.choice(N, 14, replace=False)
    df = pd.concat([df, df.iloc[cift]], ignore_index=True)

    # ------------------------------------------------------------- yazma
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)
    df.to_csv(hedef / "uzaktan_ham.csv", index=False, encoding="utf-8-sig")
    ik.to_csv(hedef / "uzaktan_ik_kayitlari.csv", index=False,
              encoding="utf-8-sig")

    pd.DataFrame(
        [{"madde": k, "metin": m, "olcek": o, "faktor_yuku_gercek": y,
          "esik_kaymasi": e, "ters_kodlu": "evet" if t else "hayır"}
         for k, m, o, y, e, t in MADDELER]
    ).to_csv(hedef / "uzaktan_madde_sozlugu.csv", index=False,
             encoding="utf-8-sig")

    pd.DataFrame(
        [{"kaynak": a, "hedef": b, "gercek_katsayi": k} for a, b, k in YOLLAR]
    ).to_csv(hedef / "uzaktan_gercek_parametreler.csv", index=False,
             encoding="utf-8-sig")

    print(f"Ham anket   : {len(df)} satır, {df.shape[1]} sütun")
    print(f"İK kayıtları: {len(ik)} satır "
          f"({N - len(ik)} katılımcı için kayıt yok)")
    print(f"  düz çizgi dolduran   : {len(duz)}")
    print(f"  çelişkili ters madde : {len(celiskili)}")
    print(f"  dikkat kontrolünü kaçıran: {int((~dikkatli).sum())}")
    print(f"  mükerrer kayıt       : {len(cift)}")
    print(f"  boş hücre            : {int(df.isna().sum().sum())}")


if __name__ == "__main__":
    main(sys.argv[1])
