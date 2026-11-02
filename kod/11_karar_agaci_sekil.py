# -*- coding: utf-8 -*-
"""
11 — Analiz seçimi karar ağacı (elle çizilmiş SVG)

Bu şekil veriden üretilmez; bir yöntem haritasıdır. Yine de elle SVG
yazmak yerine bir veri yapısından üretiliyor: kutular taşındığında
bağlantı çizgileri kendiliğinden yeniden hesaplanır.

Kullanım:
  python 11_karar_agaci_sekil.py <sekil_klasoru>
"""
import html
import pathlib
import sys

LACIVERT = "#1F3A5F"
TURKUAZ = "#227C8C"
AMBER = "#A96F22"
MOR = "#5E4C7D"
YESIL = "#3F7A4E"
GRI = "#6B7280"
CIZGI = "#C9D0D8"

YAZI = ("'PT Sans','Source Sans 3','Helvetica Neue',Helvetica,Arial,"
        "sans-serif")

# Her dal: (renk, soru türü, [(koşul, test, etki büyüklüğü), ...])
DALLAR = [
    (TURKUAZ, "BETİMLEME",
     "“Veri neye benziyor?”", [
         ("Sürekli değişken",
          "Ortalama · standart sapma\nÇarpıklık · basıklık",
          "—"),
         ("Sıralı / kategorik",
          "Ortanca · çeyrekler\nFrekans ve yüzde",
          "—"),
     ]),
    (LACIVERT, "FARK",
     "“Gruplar birbirinden\nfarklı mı?”", [
         ("2 grup · bağımsız\nvarsayım sağlanıyor",
          "Bağımsız örneklem t testi\n(varyans eşit değilse Welch)",
          "Cohen d"),
         ("2 grup · bağımsız\nvarsayım sağlanmıyor",
          "Mann–Whitney U",
          "Sıra-noktasal r"),
         ("2 ölçüm · aynı kişiler",
          "Eşleştirilmiş t testi\nveya Wilcoxon işaretli sıralar",
          "Cohen d"),
         ("3 ve daha fazla grup",
          "Tek yönlü ANOVA + Tukey\nveya Kruskal–Wallis + Dunn",
          "eta kare / epsilon kare"),
     ]),
    (AMBER, "İLİŞKİ",
     "“Birlikte mi\ndeğişiyorlar?”", [
         ("İki sürekli değişken",
          "Pearson r (doğrusal)\nSpearman rho (monotonik)",
          "r kare"),
         ("İki kategorik değişken",
          "Ki-kare bağımsızlık testi\n(beklenen < 5 ise Fisher)",
          "Cramér V"),
     ]),
    (MOR, "YORDAMA",
     "“Bir değişkeni\naçıklayabilir miyim?”", [
         ("Sonuç sürekli",
          "Çoklu doğrusal regresyon\n+ VIF, Breusch–Pagan",
          "R kare · standart beta"),
         ("Sonuç iki kategorili",
          "Lojistik regresyon",
          "Olasılık oranı (OR) · AUC"),
         ("Sonuç sayım",
          "Poisson / negatif binom\nregresyon",
          "Oran oranı (IRR)"),
     ]),
    (YESIL, "YAPI",
     "“Ölçeğim ne\nölçüyor?”", [
         ("İç tutarlılık",
          "Cronbach alfa\nMadde-toplam korelasyonu",
          "alfa · madde silinirse alfa"),
         ("Boyut sayısı bilinmiyor",
          "Açımlayıcı faktör analizi\n(önce KMO ve Bartlett)",
          "Açıklanan varyans"),
         ("Boyut yapısı kuramdan geliyor",
          "Doğrulayıcı faktör analizi",
          "CFI · RMSEA · SRMR"),
     ]),
]


def cok_satir(metin, x, y, boyut, renk, kalin=False, aralik=13.5,
              hizalama="start"):
    satirlar = metin.split("\n")
    agirlik = ' font-weight="700"' if kalin else ""
    parcalar = []
    for i, satir in enumerate(satirlar):
        parcalar.append(
            f'<text x="{x}" y="{y + i * aralik}" font-size="{boyut}" '
            f'fill="{renk}" text-anchor="{hizalama}"{agirlik}>'
            f'{html.escape(satir)}</text>')
    return "".join(parcalar)


def main(hedef_klasor):
    GEN, SOL, ORTA, SAG = 1180, 24, 300, 700
    SOL_G, ORTA_G, SAG_G, ETKI_G = 240, 350, 330, 190
    SATIR_Y, DAL_BOSLUK = 46, 26

    ogeler = []
    y = 76
    dal_konumlari = []

    for renk, baslik, soru, satirlar in DALLAR:
        dal_bas = y
        n = len(satirlar)
        dal_yuksek = n * SATIR_Y - 10

        # sol blok
        ogeler.append(
            f'<rect x="{SOL}" y="{dal_bas}" width="{SOL_G}" '
            f'height="{dal_yuksek}" rx="9" fill="{renk}"/>')
        ogeler.append(cok_satir(baslik, SOL + 16, dal_bas + 26, 14.5,
                                "#FFFFFF", kalin=True))
        ogeler.append(cok_satir(soru, SOL + 16, dal_bas + 46, 11.8,
                                "#FFFFFF", aralik=14))

        for i, (kosul, test, etki) in enumerate(satirlar):
            sy = dal_bas + i * SATIR_Y + 8
            orta_y = sy + 16

            # baglanti: sol bloktan kosula
            ogeler.append(
                f'<path d="M{SOL + SOL_G} {dal_bas + dal_yuksek / 2} '
                f'C{SOL + SOL_G + 28} {dal_bas + dal_yuksek / 2}, '
                f'{ORTA - 28} {orta_y}, {ORTA} {orta_y}" '
                f'fill="none" stroke="{CIZGI}" stroke-width="1.4"/>')
            # kosul
            ogeler.append(cok_satir(kosul, ORTA, orta_y - 2, 11.6, "#2B3038",
                                    aralik=12.5))
            # ok
            ogeler.append(
                f'<path d="M{ORTA + ORTA_G - 44} {orta_y} '
                f'h26 m-6 -4 l6 4 -6 4" fill="none" stroke="{renk}" '
                f'stroke-width="1.5"/>')
            # test kutusu
            ogeler.append(
                f'<rect x="{SAG}" y="{sy - 4}" width="{SAG_G}" '
                f'height="{SATIR_Y - 12}" rx="6" fill="#F7F8FA" '
                f'stroke="{renk}" stroke-width="1.1"/>')
            ogeler.append(cok_satir(test, SAG + 11, orta_y - 2, 11.6, renk,
                                    kalin=True, aralik=12.5))
            # etki buyuklugu
            ogeler.append(cok_satir(etki, SAG + SAG_G + 14, orta_y + 4, 10.8,
                                    GRI, aralik=12))

        dal_konumlari.append((dal_bas, dal_yuksek))
        y = dal_bas + dal_yuksek + DAL_BOSLUK

    yukseklik = y + 92

    # baslik satiri
    basliklar = (
        f'<text x="{SOL}" y="34" font-size="17" font-weight="700" '
        f'fill="{LACIVERT}">Hangi analizi seçmeliyim?</text>'
        f'<text x="{SOL}" y="54" font-size="11.5" fill="{GRI}">'
        f'Soru türünden teste, testten etki büyüklüğüne</text>'
        f'<text x="{ORTA}" y="{y + 4}" font-size="11" font-weight="700" '
        f'fill="{GRI}">DURUM</text>'
        f'<text x="{SAG}" y="{y + 4}" font-size="11" font-weight="700" '
        f'fill="{GRI}">TEST</text>'
        f'<text x="{SAG + SAG_G + 14}" y="{y + 4}" font-size="11" '
        f'font-weight="700" fill="{GRI}">ETKİ BÜYÜKLÜĞÜ</text>')

    uyari = (
        f'<rect x="{SOL}" y="{y + 18}" width="{GEN - 2 * SOL}" height="52" '
        f'rx="7" fill="#FDF5F5" stroke="#E0C2C4" stroke-width="1"/>'
        + cok_satir(
            "HER TESTTEN ÖNCE — varsayım denetimi",
            SOL + 14, y + 38, 11.8, "#A8414A", kalin=True)
        + cok_satir(
            "Dağılım biçimi (çarpıklık, basıklık) · varyans eşitliği "
            "(Levene) · bağımsızlık · yeterli hücre büyüklüğü.  "
            "Varsayım sağlanmıyorsa parametrik olmayan karşılığa geçilir — "
            "ikisi birlikte raporlanırsa karar varsayıma bağlı kalmaz.",
            SOL + 14, y + 55, 10.8, "#6B4347", aralik=12))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="0 0 {GEN} {yukseklik}" width="{GEN}" '
           f'height="{yukseklik}" font-family="{YAZI}">'
           f'<rect width="{GEN}" height="{yukseklik}" fill="#FFFFFF"/>'
           + basliklar + "".join(ogeler) + uyari + "</svg>")

    hedef = pathlib.Path(hedef_klasor) / "g01_analiz_karar_agaci.svg"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(svg, encoding="utf-8")
    print(f"Yazıldı: {hedef}  ({hedef.stat().st_size / 1024:.1f} KB, "
          f"{GEN}×{yukseklik})")
    print(f"  {sum(len(d[3]) for d in DALLAR)} karar satırı, "
          f"{len(DALLAR)} dal")


if __name__ == "__main__":
    main(sys.argv[1])
