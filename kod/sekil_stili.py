# -*- coding: utf-8 -*-
"""
Şekil stili — tüm kurs şekilleri için tek tipografi ve renk düzeni

Yayın kalitesinde şekil, süslü şekil değildir. Üç ilkeye dayanır:
  1. Mürekkep oranı — her çizgi bir bilgi taşımalı; süs çizgisi silinir
  2. Doğrudan etiketleme — mümkünse açıklama (legend) yerine etiketi
     verinin yanına yaz
  3. Tek tipografi — şekil yazısı, metin yazısıyla aynı aileden olmalı

SVG çıktısında yazı YAZI olarak kalır (svg.fonttype = "none"); bu dosya
boyutunu küçültür, metni seçilebilir ve arama yapılabilir kılar. Yazı
tipi adı sonradan bir yığına (font stack) çevrilir, böylece yazı tipi
bulunmayan makinede de düzgün yedek kullanılır.
"""
import pathlib
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ------------------------------------------------------------------ renkler
LACIVERT = "#1F3A5F"
TURKUAZ = "#2E8B9A"
YESIL = "#4C8B5A"
AMBER = "#C9893A"
KIRMIZI = "#B4474E"
MOR = "#6E5A8E"
GRI = "#6B7280"
ACIK = "#E8EAED"
COK_ACIK = "#F4F5F7"

# Beş basamaklı Likert için ayrışan (diverging) düzen
LIKERT = ["#A33F46", "#D4868B", "#DEDEDE", "#7FB8C2", "#2E7C8C"]
LIKERT_ETIKET = ["1 — Kesinlikle katılmıyorum", "2", "3 — Kararsız", "4",
                 "5 — Kesinlikle katılıyorum"]

SIRA = [LACIVERT, TURKUAZ, AMBER, YESIL, KIRMIZI, MOR, GRI]

YAZI_YIGINI = ("'PT Sans','Source Sans 3','Helvetica Neue',Helvetica,"
               "Arial,sans-serif")


def ts(sayi, basamak=3):
    """Sayıyı Türkçe ondalık ayracıyla (virgül) biçimler.

    Şekil üstündeki her sayı metin olarak okunur; metnin dili Türkçeyse
    ondalık ayracı da virgül olmalıdır. Bu, biçim titizliği değil
    okunurluk meselesidir: '0.05' Türkçe bir okura 'sıfır nokta sıfır
    beş' diye okunmaz.
    """
    # Python binliği virgül, ondalığı nokta yazar; Türkçede tam tersi.
    # Doğrudan çevirmek ikisini birbirine karıştırır, bu yüzden önce
    # binlik ayracı geçici bir imle değiştirilir.
    return (f"{sayi:,.{basamak}f}"
            .replace(",", "\x00").replace(".", ",").replace("\x00", "."))


def tam(sayi):
    """Tam sayıyı binlik ayracıyla (nokta) biçimler: 5820 → 5.820"""
    return f"{int(sayi):,}".replace(",", ".")


def stil_kur():
    """matplotlib genel ayarlarını kurar."""
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.12,
        "svg.fonttype": "none",
        "font.family": "sans-serif",
        # DejaVu Sans listede duruyor: PT Sans'ta bulunmayan Yunan
        # harfleri (η, α, χ) için matplotlib harf bazında buraya düşer.
        "font.sans-serif": ["PT Sans", "DejaVu Sans", "Helvetica Neue",
                            "Arial"],
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlecolor": LACIVERT,
        "axes.labelsize": 10.5,
        "axes.labelcolor": "#2A2A2A",
        "axes.edgecolor": "#C7CBD1",
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        # Izgara yalnız DEĞER ekseninde çizilir. Dikey grafiklerde bu
        # y eksenidir (varsayılan); yatay çubuk grafiklerinde değer
        # ekseni x olduğu için o şekiller ayrıca ax.grid(axis="x")
        # çağırır. Kategori ekseninde ızgara bilgi taşımaz.
        "axes.grid.axis": "y",
        "grid.color": "#EDEFF2",
        "grid.linewidth": 0.8,
        "xtick.color": "#4A4A4A",
        "ytick.color": "#4A4A4A",
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.frameon": False,
        "legend.fontsize": 9.5,
        "lines.linewidth": 1.8,
        "patch.linewidth": 0.6,
    })


def kaydet(fig, yol, png=True):
    """Şekli SVG (web) ve PNG (Word, sunum) olarak yazar.

    SVG'de yazı tipi adı yedekli bir yığına çevrilir: matplotlib tek bir
    ad yazar, tarayıcıda o ad yoksa yedeğe düşmesi gerekir.

    PNG, SVG'nin yanındaki `sekil_png/` klasörüne 200 dpi ile yazılır.
    Web sayfası SVG kullanır; PNG, şeklin Word belgesine ya da sunuma
    taşınması için durur.
    """
    yol = pathlib.Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(yol, format="svg")
    if png:
        png_yol = yol.parent.parent / "sekil_png" / (yol.stem + ".png")
        png_yol.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_yol, format="png", dpi=200)
    plt.close(fig)

    metin = yol.read_text(encoding="utf-8")
    # font-family değeri ';' ya da '"' ile biter; tırnaklı yazı tipi
    # adları da kapsanmalı, bu yüzden sonlandırıcı karakter kümesiyle
    # eşleştiriyoruz. (Tek tırnağı dışlayan bir desen, 'PT Sans' gibi
    # tırnaklı ilk adda yarıda keser ve bozuk değer bırakır.)
    metin = re.sub(r'font-family:[^;"}]*', f"font-family:{YAZI_YIGINI}", metin)
    metin = re.sub(r'font-family="[^"]*"', f'font-family="{YAZI_YIGINI}"',
                   metin)
    yol.write_text(metin, encoding="utf-8")
    return yol.stat().st_size


def alt_not(fig, metin):
    """Şeklin altına kaynak/not satırı ekler."""
    fig.text(0.005, -0.012, metin, fontsize=8, color=GRI, va="top")
