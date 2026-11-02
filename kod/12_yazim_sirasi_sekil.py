# -*- coding: utf-8 -*-
"""
12 — Makale yazım sırası şeması (elle çizilmiş SVG)

Okuma sırası ile yazma sırasını yan yana gösterir. Veriden üretilmez;
bir yöntem haritasıdır.

Kullanım:
  python 12_yazim_sirasi_sekil.py <sekil_klasoru>
"""
import html
import pathlib
import sys

LACIVERT = "#1F3A5F"
TURKUAZ = "#227C8C"
GRI = "#6B7280"
ACIK = "#EEF1F4"
YAZI = ("'PT Sans','Source Sans 3','Helvetica Neue',Helvetica,Arial,"
        "sans-serif")

# Okurun gördüğü sıra
OKUMA = ["Başlık", "Öz", "Giriş", "İlgili çalışmalar", "Yöntem",
         "Bulgular", "Tartışma", "Sonuç"]

# Yazarın izlemesi gereken sıra: (bölüm, neden bu sırada)
YAZMA = [
    ("Yöntem", "Ne yaptığınızı zaten biliyorsunuz"),
    ("Bulgular", "Sayılar elinizde, yorum yok"),
    ("Tartışma", "Burada literatürle konuşmaya başlarsınız"),
    ("İlgili çalışmalar", "Hangi kaynaklara ihtiyaç olduğu belli oldu"),
    ("Giriş", "Artık ne bulduğunuzu biliyorsunuz"),
    ("Sonuç", "Girişteki söz tutuldu mu"),
    ("Öz", "Özetlenecek şey ancak şimdi hazır"),
    ("Başlık", "En kısa bölüm, en son"),
]


def main(hedef_klasor):
    GEN = 1000
    SATIR = 52
    UST = 76
    SOL_X, SAG_X = 30, 330
    SOL_G, SAG_G = 210, 250

    ogeler = []

    # Okuma sutunu
    for i, ad in enumerate(OKUMA):
        y = UST + i * SATIR
        ogeler.append(
            f'<rect x="{SOL_X}" y="{y}" width="{SOL_G}" height="{SATIR - 12}" '
            f'rx="6" fill="{ACIK}" stroke="#D7DCE2" stroke-width="1"/>')
        ogeler.append(
            f'<text x="{SOL_X + 14}" y="{y + 26}" font-size="13" '
            f'fill="{GRI}">{html.escape(ad)}</text>')
        ogeler.append(
            f'<text x="{SOL_X + SOL_G - 14}" y="{y + 26}" font-size="12" '
            f'fill="#AAB1B9" text-anchor="end">{i + 1}</text>')

    # Yazma sutunu + baglanti cizgileri
    for i, (ad, neden) in enumerate(YAZMA):
        y = UST + i * SATIR
        kaynak_i = OKUMA.index(ad)
        kaynak_y = UST + kaynak_i * SATIR + (SATIR - 12) / 2
        hedef_y = y + (SATIR - 12) / 2
        ogeler.append(
            f'<path d="M{SOL_X + SOL_G} {kaynak_y} '
            f'C{SOL_X + SOL_G + 50} {kaynak_y}, {SAG_X - 50} {hedef_y}, '
            f'{SAG_X} {hedef_y}" fill="none" stroke="{TURKUAZ}" '
            f'stroke-width="1.5" opacity="0.5"/>')
        ogeler.append(
            f'<rect x="{SAG_X}" y="{y}" width="{SAG_G}" '
            f'height="{SATIR - 12}" rx="6" fill="{LACIVERT}"/>')
        ogeler.append(
            f'<text x="{SAG_X + 14}" y="{y + 26}" font-size="13" '
            f'font-weight="700" fill="#FFFFFF">{html.escape(ad)}</text>')
        ogeler.append(
            f'<text x="{SAG_X + SAG_G - 14}" y="{y + 26}" font-size="12" '
            f'fill="#9FB3C8" text-anchor="end">{i + 1}</text>')
        ogeler.append(
            f'<text x="{SAG_X + SAG_G + 22}" y="{y + 26}" font-size="12" '
            f'fill="#4D555E">{html.escape(neden)}</text>')

    yukseklik = UST + len(OKUMA) * SATIR + 54

    basliklar = (
        f'<text x="{SOL_X}" y="30" font-size="16.5" font-weight="700" '
        f'fill="{LACIVERT}">Okuma sırası ile yazma sırası aynı değildir</text>'
        f'<text x="{SOL_X}" y="60" font-size="11" font-weight="700" '
        f'fill="{GRI}">OKUR BÖYLE GÖRÜR</text>'
        f'<text x="{SAG_X}" y="60" font-size="11" font-weight="700" '
        f'fill="{TURKUAZ}">SİZ BÖYLE YAZIN</text>'
        f'<text x="{SAG_X + SAG_G + 22}" y="60" font-size="11" '
        f'font-weight="700" fill="{GRI}">NEDEN</text>'
        f'<text x="{SOL_X}" y="{yukseklik - 18}" font-size="11.5" '
        f'fill="{GRI}">Kural: elinizde en çok malzeme olan bölümden '
        f'başlayın. Giriş en sona kalır, çünkü ne bulduğunuzu ancak o '
        f'zaman bilirsiniz.</text>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="0 0 {GEN} {yukseklik}" width="{GEN}" '
           f'height="{yukseklik}" font-family="{YAZI}">'
           f'<rect width="{GEN}" height="{yukseklik}" fill="#FFFFFF"/>'
           + basliklar + "".join(ogeler) + "</svg>")

    hedef = pathlib.Path(hedef_klasor) / "g02_yazim_sirasi.svg"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(svg, encoding="utf-8")
    print(f"Yazıldı: {hedef} ({hedef.stat().st_size / 1024:.1f} KB, "
          f"{GEN}×{yukseklik})")


if __name__ == "__main__":
    main(sys.argv[1])
