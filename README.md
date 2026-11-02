# Akademide Üretken Yapay Zekâ — uygulamalı kurs

Akademik araştırma ve yayın sürecinde üretken yapay zekânın nasıl
kullanılacağını, **gerçekten çalıştırılmış istemler** ve **gerçekten
üretilmiş çıktılar** üzerinden anlatan Türkçe bir kurs.

On yedi bölüm, 48 istem kalıbı ve 46 doldurulmuş örnek, 21 şekil,
üç veri seti.
Sayfalardaki her sayı, yanındaki veri ve kodla yeniden üretilebilir.

## Yayımlamak

Site tamamen durağandır: sunucu tarafı kod yok, derleme adımı yok.

**GitHub Pages:** bu klasörü bir depoya yükleyin, depo ayarlarından
`Pages` bölümünde kaynak olarak ana dalı ve kök dizini seçin.
Birkaç dakika içinde `kullaniciadi.github.io/depo-adi/` adresinde
yayına girer. `.nojekyll` dosyası pakettedir ve silinmemelidir.

**Yerel:** `index.html` dosyasına çift tıklayın, ya da klasörün
içinde `python3 -m http.server 8000` çalıştırıp `localhost:8000`
adresine gidin.

## Klasörler

| Klasör | İçerik |
|---|---|
| `veri/` | Üç veri seti ve sözlükleri |
| `kod/` | On iki Python betiği ve ortak şekil stili dosyası |
| `cikti/` | Analiz çıktıları (metin ve JSON) |
| `varlik/sekil/` | Yirmi bir şekil, SVG |
| `varlik/sekil_png/` | Aynı şekiller PNG (Word ve sunum için) |

## Veri setleri

**Gerçek, açık erişimli:**

- Gündüz, N., & Fokoué, E. (2013). *Turkiye Student Evaluation*
  [Veri seti]. UCI Machine Learning Repository.
  <https://doi.org/10.24432/C5S02S> — CC BY 4.0
- Prasad, A., & Chandra, S. (2024). *PhiUSIIL Phishing URL (Website)*
  [Veri seti]. UCI Machine Learning Repository.
  <https://doi.org/10.1016/j.cose.2023.103545> — CC BY 4.0

**Sentetik, kurs için üretilmiş:** akademisyen anketi atölye verisi
(`veri/sosyal/anket_*.csv`). Gerçek bir anketten gelmemiştir; hiçbir
sayısı bulgu olarak alıntılanamaz. Üreten betikler pakettedir.

## Kodu çalıştırmak

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pandas numpy scipy statsmodels scikit-learn matplotlib
python kod/05_analiz_sosyal.py veri/sosyal cikti
```

Çalıştırma sırası ve tüm komutlar `16-kaynaklar.html` sayfasında.
Rastgelelik içeren her adımda tohum `20261103` olarak sabittir;
aynı sayıları alırsınız.

## Lisans

Veri setleri CC BY 4.0. Kurs içeriği (metin, şekil, kod, istemler)
eğitim amacıyla serbestçe kullanılabilir; kaynak göstermeniz
yeterlidir.
