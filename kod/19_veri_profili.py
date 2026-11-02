# -*- coding: utf-8 -*-
"""
19 — Veri profili çıkarma

Bir veri dosyasından, yapay zekâya BAĞLAM olarak verilebilecek bir
profil üretir. Ham veri yerine profil vermenin üç nedeni var:

  1. Gizlilik. Ham satırlar kişisel veri taşıyabilir; profil taşımaz.
  2. Jeton. 5.820 satırlık bir dosya bağlam penceresini doldurur;
     profili iki sayfadır.
  3. Doğruluk. Model 5.820 satırı okuyup ortalama hesaplamaz —
     hesaplamaya çalışırsa yanılır. Hesabı burada yapıp sonucu
     vermek daha güvenilirdir.

Profil her değişken için şunları verir: ölçüm düzeyi, eksik oran,
benzersiz değer sayısı, dağılım ölçüleri, normallik sınaması ve
dağılım biçimine dair bir not.

Kullanım:
  python 19_veri_profili.py <csv_dosyasi> <cikti_dosyasi> [--likert 1 5]
"""
import argparse
import pathlib

import numpy as np
import pandas as pd
from scipy import stats


def ts(x, b=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return (f"{x:,.{b}f}".replace(",", "\x00").replace(".", ",")
            .replace("\x00", "."))


def olcum_duzeyi(seri, likert_araligi=None):
    """Değişkenin ölçüm düzeyini tahmin eder.

    Tahmin eder — karar vermez. Ölçüm düzeyi veriye değil, verinin
    nasıl toplandığına bağlıdır: 1-5 arası bir sütun Likert de
    olabilir, sıralama da, sayma da. Betik gerekçesini yazar;
    doğrulamak araştırmacının işidir.
    """
    temiz = seri.dropna()
    if temiz.empty:
        return "boş", "hiç gözlem yok"
    if not pd.api.types.is_numeric_dtype(temiz):
        n = temiz.nunique()
        if n == 2:
            return "ikili (nominal)", f"iki düzey: {sorted(temiz.unique())}"
        return "nominal", f"{n} düzey, metin"
    # numpy skalerleri repr'de 'np.int64(1)' diye yazılır;
    # profil metni okunacak bir belge, Python çıktısı değil.
    benzersiz = sorted(v.item() if hasattr(v, 'item') else v
                       for v in temiz.unique())
    n = len(benzersiz)
    tamsayi = bool(np.all(np.equal(np.mod(temiz, 1), 0)))
    if n == 2:
        return "ikili (nominal)", f"iki düzey: {benzersiz}"
    # Likert sayılması için ölçeğin BÜTÜN basamakları görülmeli.
    # Gevşek bir ölçüt (yalnız aralığın içinde kalmak) kimlik
    # numaralarını da Likert sanar: 1-3 arası üç değer, hem üç
    # basamaklı bir ölçek hem üç öğretim elemanının kimliği olabilir.
    basamak = likert_araligi[1] - likert_araligi[0] + 1 if likert_araligi else 0
    if (likert_araligi and tamsayi and n == basamak
            and min(benzersiz) == likert_araligi[0]
            and max(benzersiz) == likert_araligi[1]):
        return ("sıralı (Likert)",
                f"{likert_araligi[0]}–{likert_araligi[1]} arası "
                f"{n} basamağın hepsi kullanılmış")
    if tamsayi and n <= 10:
        return ("sıralı ya da nominal",
                f"{n} tamsayı düzeyi: {benzersiz[:10]} — hangisi olduğu "
                "veriden anlaşılmaz, siz söylemelisiniz")
    if tamsayi:
        return "sayma (kesikli)", f"{n} farklı tamsayı"
    return "sürekli", f"{n} farklı değer"


def normallik(temiz):
    """Normallik sınaması ve örneklem büyüklüğüne göre yorum.

    Shapiro-Wilk büyük örneklemde küçük sapmaları da anlamlı bulur;
    bu yüzden p değeri tek başına karar ölçütü değildir. Çarpıklık ve
    basıklık birlikte verilir.
    """
    n = len(temiz)
    if n < 3:
        return None, None, "örneklem çok küçük"
    # Shapiro-Wilk 5.000'in üstünde güvenilirliğini yitirir; büyük
    # örneklemde rastgele bir altküme alınır ve bu belirtilir.
    if n > 5000:
        alt = pd.Series(temiz).sample(5000, random_state=20261103)
        w, p = stats.shapiro(alt)
        kaynak = "5.000 kişilik rastgele altküme üzerinde"
    else:
        w, p = stats.shapiro(temiz)
        kaynak = ""
    carpiklik = float(stats.skew(temiz))
    basiklik = float(stats.kurtosis(temiz))
    # Yaygın eşik: |çarpıklık| < 2 ve |basıklık| < 7 ise parametrik
    # testler için kabul edilebilir sapma (Kim, 2013; West ve ark., 1995)
    kabul = abs(carpiklik) < 2 and abs(basiklik) < 7
    if p >= 0.05:
        yorum = "normallikten sapma anlamlı değil"
    elif kabul:
        yorum = ("sapma anlamlı ama çarpıklık ve basıklık yaygın "
                 "eşiklerin içinde; büyük örneklemde beklenen durum")
    else:
        yorum = ("belirgin sapma; parametrik test öncesi dönüşüm ya da "
                 "parametrik olmayan alternatif düşünülmeli")
    if kaynak:
        yorum += f" ({kaynak})"
    return w, p, yorum


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("girdi")
    ap.add_argument("cikti")
    ap.add_argument("--likert", nargs=2, type=int, default=None,
                    metavar=("ALT", "UST"))
    ap.add_argument("--baslik", default=None)
    a = ap.parse_args()

    df = pd.read_csv(a.girdi, encoding="utf-8-sig")
    lik = tuple(a.likert) if a.likert else None
    ad = a.baslik or pathlib.Path(a.girdi).name

    s = [f"VERİ PROFİLİ — {ad}", "=" * 78, "",
         f"Gözlem sayısı : {len(df):,}".replace(",", "."),
         f"Değişken sayısı: {df.shape[1]}",
         f"Tam dolu satır : {int(df.notna().all(axis=1).sum()):,}"
         .replace(",", "."),
         "",
         "Bu profil, ham veri yerine yapay zekâya bağlam olarak",
         "verilmek üzere üretildi. Hiçbir satır-düzeyi bilgi içermez.",
         "", "-" * 78, ""]

    for sutun in df.columns:
        seri = df[sutun]
        temiz = seri.dropna()
        duzey, gerekce = olcum_duzeyi(seri, lik)
        eksik = len(seri) - len(temiz)
        s.append(f"{sutun}")
        s.append(f"  ölçüm düzeyi : {duzey}  ({gerekce})")
        s.append(f"  eksik        : {eksik} "
                 f"(%{ts(eksik / len(seri) * 100, 1)})")
        if pd.api.types.is_numeric_dtype(temiz) and len(temiz) > 0:
            s.append(f"  aralık       : {ts(temiz.min(), 2)} – "
                     f"{ts(temiz.max(), 2)}")
            s.append(f"  ortalama / SS: {ts(temiz.mean(), 3)} / "
                     f"{ts(temiz.std(), 3)}")
            s.append(f"  medyan / ÇAG : {ts(temiz.median(), 3)} / "
                     f"{ts(temiz.quantile(.75) - temiz.quantile(.25), 3)}")
            w, p, yorum = normallik(temiz.to_numpy(float))
            if w is not None:
                s.append(f"  Shapiro-Wilk : W = {ts(w, 4)}, "
                         f"p = {ts(p, 4)}")
                s.append(f"  çarpıklık    : "
                         f"{ts(float(stats.skew(temiz)), 3)} · basıklık: "
                         f"{ts(float(stats.kurtosis(temiz)), 3)}")
                s.append(f"  dağılım notu : {yorum}")
        else:
            sayim = temiz.value_counts()
            s.append(f"  düzey dağılımı:")
            for d, n in sayim.head(8).items():
                s.append(f"    {str(d)[:36]:<38} {n:>6} "
                         f"(%{ts(n / len(temiz) * 100, 1)})")
            if len(sayim) > 8:
                s.append(f"    … ve {len(sayim) - 8} düzey daha")
            # En küçük hücre, ki-kare varsayımı için belirleyicidir
            s.append(f"  en küçük düzey: {int(sayim.min())} gözlem")
        s.append("")

    # Sayısal değişkenler arası çoklu bağlantı uyarısı
    sayisal = df.select_dtypes(include=[np.number])
    if sayisal.shape[1] >= 2:
        kor = sayisal.corr().abs()
        ust = kor.where(np.triu(np.ones(kor.shape), k=1).astype(bool))
        yuksek = (ust.stack().sort_values(ascending=False)
                  .loc[lambda x: x > 0.80])
        s += ["-" * 78, "",
              "YÜKSEK İLİŞKİLİ DEĞİŞKEN ÇİFTLERİ (|r| > 0,80)", "",
              "Regresyon kurulacaksa bu çiftler çoklu bağlantı",
              "üretir; ikisini birden modele koymadan önce düşünün.", ""]
        if len(yuksek) == 0:
            s.append("  0,80'i aşan çift yok.")
        else:
            for (x, y), r in list(yuksek.items())[:15]:
                s.append(f"  {x} — {y}: r = {ts(r, 3)}")
            if len(yuksek) > 15:
                s.append(f"  … ve {len(yuksek) - 15} çift daha")
        s.append("")

    pathlib.Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.cikti).write_text("\n".join(s) + "\n",
                                     encoding="utf-8-sig")
    print(f"Profil yazıldı → {a.cikti}  "
          f"({len(s)} satır, {df.shape[1]} değişken)")


if __name__ == "__main__":
    main()
