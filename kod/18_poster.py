# -*- coding: utf-8 -*-
"""
18 — Konferans posteri (elle çizilmiş SVG)

Bölüm 12'deki poster isteminin gerçek çıktısı. İstem posterin
içeriğini, bölüm sırasını ve yerleşim planını üretti; bu betik o planı
A0 oranında çizer ve analiz şekillerini yerine gömer.

İçerikteki bütün sayılar kimya örneğinin gerçek analiz çıktısından
(cikti/adsorpsiyon_analiz.json) okunur; hiçbiri elle yazılmaz. Veri
sentetiktir ve poster üzerinde de böyle işaretlenir.

İKİ TASARIM KARARI

1. Şekiller posterin içine GÖMÜLÜR, dışarıdan bağlanmaz. Bir SVG
   <img> olarak gösterildiğinde tarayıcı dış kaynak çekmez; bağlantılı
   şekiller boş görünürdü. Gömme, posteri tek dosya da yapar.

2. Yazı boyutları milimetre cinsindendir ve A0 ölçeğine göre seçildi:
   gövde 9,5 mm (~27 punto), bölüm başlığı 12 mm, ana başlık 30 mm.
   Poster tipografisinde ölçüt, iki metre uzaktan okunabilmektir.

Kullanım:
  python 18_poster.py <analiz_json> <şekil_klasörü>
"""
import html
import json
import pathlib
import re
import shutil
import subprocess
import sys

LACIVERT = "#1F3A5F"
LACIVERT_ACIK = "#35557F"
TURKUAZ = "#227C8C"
AMBER = "#A96F22"
KIRMIZI = "#A8414A"
GRI = "#6B7280"
COK_ACIK = "#F7F8FA"
YAZI = ("'PT Sans','Source Sans 3','Helvetica Neue',Helvetica,Arial,"
        "sans-serif")

GEN, YUK = 841, 1189          # A0, milimetre
KENAR = 30
SUTUN_ARA = 16
BASLIK_BANDI = 19             # kutu başlık şeridinin yüksekliği
IC_KENAR = 8
GOVDE = 9.5                   # gövde yazısı, mm
SATIR = 12.6                  # satır aralığı, mm


def ts(x, b=2):
    return (f"{x:,.{b}f}".replace(",", "\x00").replace(".", ",")
            .replace("\x00", "."))


def sekil_goster(yol: pathlib.Path, x, y, g, onek):
    """Bir SVG dosyasını poster içine iç içe <svg> olarak gömer.

    Dönen değer (svg_parçası, yükseklik). Yükseklik, kaynak şeklin
    kendi en-boy oranından hesaplanır; şekil hiç esnetilmez.

    id öneki şart: matplotlib her şekilde aynı glif kimliklerini
    (ör. DejaVuSans-20) yazar. İki şekil aynı belgeye girince ikinci
    tanım yok sayılır ve yazılar birbirine karışır. Her gömmede id ve
    ona yapılan başvurular kendi önekini alır.
    """
    ham = yol.read_text(encoding="utf-8")
    ham = re.sub(r"<\?xml[^>]*\?>", "", ham)
    ham = re.sub(r"<!DOCTYPE[^>]*>", "", ham)
    kok = re.search(r"<svg\b[^>]*>", ham, re.S)
    if not kok:
        raise ValueError(f"SVG kökü bulunamadı: {yol}")
    nitelikler = kok.group(0)
    vb = re.search(r'viewBox="([^"]+)"', nitelikler)
    if not vb:
        raise ValueError(f"viewBox yok: {yol}")
    _, _, vg, vy = (float(t) for t in vb.group(1).split())
    ic = ham[kok.end():ham.rindex("</svg>")]
    ic = re.sub(r'id="([^"]+)"', lambda m: f'id="{onek}-{m.group(1)}"', ic)
    ic = re.sub(r'href="#([^"]+)"',
                lambda m: f'href="#{onek}-{m.group(1)}"', ic)
    h = g * vy / vg
    parca = (f'<svg x="{x:.2f}" y="{y:.2f}" width="{g:.2f}" '
             f'height="{h:.2f}" viewBox="{vb.group(1)}" '
             f'overflow="visible">{ic}</svg>')
    return parca, h


def satirlar_yuksekligi(satirlar):
    return len(satirlar) * SATIR


def metin(x, y, satirlar, boyut=GOVDE, renk="#1C2024", aralik=SATIR):
    """Satır listesini alt alta yazar.

    ** ile başlayan satır kalın yazılır. SVG'de satır içi biçimlendirme
    için ayrı <tspan> gerekir; poster metni kısa olduğu için satırın
    tamamı kalınlaştırılıyor ve bütün yıldızlar temizleniyor —
    yalnız baştakileri kırpmak satır ortasındaki ** işaretlerini
    ekranda bırakırdı.
    """
    cikti = []
    for i, satir in enumerate(satirlar):
        kalin = satir.startswith("**")
        temiz = satir.replace("**", "")
        cikti.append(
            f'<text x="{x:.2f}" y="{y + i * aralik:.2f}" '
            f'font-size="{boyut}" font-weight="{"700" if kalin else "400"}" '
            f'fill="{renk}">{html.escape(temiz)}</text>')
    return "\n".join(cikti)


class Kutu:
    """Poster kutusu: başlık, isteğe bağlı şekil ve metin satırları.

    Yüksekliğini kendisi hesaplar; sütun yerleştirmesi bu yüksekliğe
    göre yapılır ve artan boşluk kutular arasına eşit dağıtılır.
    """

    def __init__(self, baslik, satirlar=(), sekil=None, renk=LACIVERT,
                 sekil_once=True):
        self.baslik = baslik
        self.satirlar = list(satirlar)
        self.sekil = sekil              # (dosya adı, id öneki) ya da None
        self.renk = renk
        self.sekil_once = sekil_once
        self._sekil_yuk = 0.0

    def yukseklik_hesapla(self, genislik, klasor):
        if self.sekil:
            ad, _ = self.sekil
            ham = (klasor / ad).read_text(encoding="utf-8")
            vb = re.search(r'viewBox="([^"]+)"', ham)
            _, _, vg, vy = (float(t) for t in vb.group(1).split())
            self._sekil_yuk = (genislik - 2 * IC_KENAR) * vy / vg
        ic = satirlar_yuksekligi(self.satirlar) + self._sekil_yuk
        if self.satirlar and self.sekil:
            ic += 6
        return BASLIK_BANDI + IC_KENAR + ic + IC_KENAR

    def ciz(self, x, y, g, yuk, klasor):
        p = [f'<rect x="{x}" y="{y}" width="{g}" height="{yuk:.2f}" rx="4" '
             f'fill="white" stroke="#D8DDE3" stroke-width="0.8"/>',
             f'<rect x="{x}" y="{y}" width="{g}" height="{BASLIK_BANDI}" '
             f'rx="4" fill="{self.renk}"/>',
             f'<rect x="{x}" y="{y + BASLIK_BANDI - 5}" width="{g}" '
             f'height="5" fill="{self.renk}"/>',
             f'<text x="{x + IC_KENAR}" y="{y + 13.4}" font-size="11.4" '
             f'font-weight="700" fill="white">'
             f'{html.escape(self.baslik)}</text>']
        imlec = y + BASLIK_BANDI + IC_KENAR
        if self.sekil and self.sekil_once:
            ad, onek = self.sekil
            parca, h = sekil_goster(klasor / ad, x + IC_KENAR, imlec,
                                    g - 2 * IC_KENAR, onek)
            p.append(parca)
            imlec += h + 6
        if self.satirlar:
            p.append(metin(x + IC_KENAR, imlec + GOVDE * 0.82,
                           self.satirlar))
            imlec += satirlar_yuksekligi(self.satirlar)
        if self.sekil and not self.sekil_once:
            ad, onek = self.sekil
            parca, h = sekil_goster(klasor / ad, x + IC_KENAR, imlec + 6,
                                    g - 2 * IC_KENAR, onek)
            p.append(parca)
        return "\n".join(p)


def sutun_yerlestir(kutular, x, ust, alt, g, klasor):
    """Kutuları sütuna yerleştirir, artan boşluğu aralara eşit böler."""
    yukseklikler = [k.yukseklik_hesapla(g, klasor) for k in kutular]
    bosluk = (alt - ust - sum(yukseklikler)) / max(len(kutular) - 1, 1)
    bosluk = max(bosluk, 12)
    p, y = [], ust
    for k, h in zip(kutular, yukseklikler):
        p.append(k.ciz(x, y, g, h, klasor))
        y += h + bosluk
    return "\n".join(p), y - bosluk


def main(analiz_json: str, sekil_klasoru: str) -> None:
    S = json.loads(pathlib.Path(analiz_json).read_text(encoding="utf-8"))
    K = pathlib.Path(sekil_klasoru)

    anova = {r["kaynak"]: r for r in S["anova"]}
    ads, ph, etk = anova["adsorban"], anova["pH"], anova["adsorban × pH"]
    iz_t, iz_c = S["izoterm"]["ticari"], S["izoterm"]["cay_posasi"]
    sd = int(anova["Hata"]["df"])
    n_haric = S["duyarlilik"]["n_haric"]

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" '
         f'xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'width="{GEN}mm" height="{YUK}mm" '
         f'viewBox="0 0 {GEN} {YUK}" font-family="{YAZI}">',
         f'<rect width="{GEN}" height="{YUK}" fill="{COK_ACIK}"/>']

    # ------------------------------------------------------------ başlık
    bh = 132
    p.append(f'<rect x="0" y="0" width="{GEN}" height="{bh}" '
             f'fill="{LACIVERT}"/>')
    p.append(f'<rect x="0" y="{bh - 3}" width="{GEN}" height="3" '
             f'fill="{AMBER}"/>')
    p.append(f'<text x="{KENAR}" y="33" font-size="12.5" font-weight="700" '
             f'fill="#9FB4CC" letter-spacing="3">YÖNTEM ÖRNEĞİ · '
             f'SENTETİK VERİ</text>')
    p.append(f'<text x="{KENAR}" y="72" font-size="29" font-weight="700" '
             f'fill="white">Çay posası aktif karbonu yüksek pH\'ta ticari '
             f'kömüre</text>')
    p.append(f'<text x="{KENAR}" y="104" font-size="29" font-weight="700" '
             f'fill="white">yaklaşıyor: malzeme ile pH arasında etkileşim '
             f'var</text>')
    p.append(f'<text x="{GEN - KENAR}" y="33" font-size="10.5" '
             f'fill="#C3D1E0" text-anchor="end">Akademide Üretken Yapay '
             f'Zekâ — örnek poster</text>')

    ys = bh
    p.append(f'<rect x="0" y="{ys}" width="{GEN}" height="26" '
             f'fill="{LACIVERT_ACIK}"/>')
    p.append(f'<text x="{KENAR}" y="{ys + 17}" font-size="11" fill="white">'
             f'Ad Soyad¹, Ad Soyad² · ¹Kimya Bölümü · ²Çevre Mühendisliği '
             f'Bölümü · Üniversite adı</text>')

    ust = ys + 26 + 22
    alt = YUK - 26 - 16
    sg = (GEN - 2 * KENAR - 2 * SUTUN_ARA) / 3

    # ------------------------------------------- 1. sütun: soru ve yöntem
    sutun1 = [
        Kutu("1 · Araştırma sorusu", [
            "Tekstil atık suyundaki katyonik boyar madde,",
            "pahalı ticari aktif karbonla gideriliyor.",
            "",
            "**Soru:** Çay fabrikası atığından elde edilen",
            "aktif karbon aynı işi görebilir mi — ve bu,",
            "çalışma koşullarına göre değişir mi?",
            "",
            "İkinci yarı önemli: alan yazında malzemeler",
            "çoğunlukla tek bir pH'ta karşılaştırılıyor,",
            "oysa yüzey yükü pH ile değişir.",
        ]),
        Kutu("2 · Yöntem", [
            "**Tam faktöriyel kesikli deney**",
            "2 adsorban × 3 derişim (25 · 50 · 100 mg/L)",
            "× 3 pH (3 · 7 · 10) × 2 sıcaklık (25 · 45 °C)",
            "× 2 temas süresi (60 · 120 dk) × 3 tekrar",
            f"Tasarlanan 216 deney, geçerli {n_haric + 15} ölçüm.",
            "V = 0,05 L · m = 0,1 g · q = (C₀ − Cₑ)·V/m",
            "",
            "**Analiz**",
            "Bloklanmış ANOVA: adsorban × pH × sıcaklık",
            "tam etkileşimli; derişim ve temas süresi ana",
            "etki olarak modelde. Tip II kareler toplamı.",
            "İzotermler doğrusal olmayan en küçük kareler",
            "ile uyduruldu, AIC ile karşılaştırıldı.",
        ], renk=TURKUAZ),
        Kutu("Tuzak · ihmal edilen faktör", [
            "Derişim ve süre modele konmazsa varyansları",
            "hata terimine gider, bütün F değerleri birin",
            "altına düşer ve hiçbir etki görünmez olur.",
            "Blok olarak eklendiğinde dördü de anlamlı.",
        ], sekil=("k02_anova_kiyas.svg", "s2"), renk=KIRMIZI,
            sekil_once=False),
        Kutu("3 · Veri temizleme", [
            "215 ham satırdan 201 analiz satırına. Şüpheli",
            "cihaz dönemi silinmedi, etiketlendi; duyarlılık",
            "analizi onsuz da yinelendi ve hiçbir anlamlılık",
            "kararı değişmedi.",
        ], sekil=("k01_temizleme.svg", "s1"), sekil_once=False),
    ]

    # ------------------------------------------ 2. sütun: ana bulgular
    sutun2 = [
        Kutu("4 · Ana bulgu · etkileşim", [
            f"adsorban × pH: F(2, {sd}) = {ts(etk['F'])}, "
            f"p = {ts(etk['PR(>F)'], 3)},",
            f"kısmi eta kare = {ts(etk['kismi_eta_kare'], 3)}",
            "",
            "Çizgiler paralel değil: ticari kömürün üstünlüğü",
            "yalnız yüksek pH'ta belirginleşiyor. Bu yüzden",
            "\"ticari kömür daha iyidir\" demek eksik kalır.",
        ], sekil=("k03_etkilesim.svg", "s3")),
        Kutu("5 · İzoterm uyumu", [
            "Her iki malzemede de Langmuir daha iyi uyuyor",
            f"(AIC farkı {ts(iz_c['AIC_farki'], 1)} ve "
            f"{ts(iz_t['AIC_farki'], 1)}).",
            f"Ticari: qmax = {ts(iz_t['langmuir']['qmax_mgG'], 1)} mg/g · "
            f"KL = {ts(iz_t['langmuir']['KL_Lmg'], 3)} L/mg",
            f"Çay posası: qmax = "
            f"{ts(iz_c['langmuir']['qmax_mgG'], 1)} mg/g",
        ], sekil=("k04_izoterm.svg", "s4")),
        Kutu("6 · Sınır · qmax ne kadar güvenilir", [
            "Çay posasının qmax güven aralığı çok geniş:",
            f"[{ts(iz_c['langmuir']['qmax_GA'][0], 0)} – "
            f"{ts(iz_c['langmuir']['qmax_GA'][1], 0)}] mg/g.",
            "",
            "Nedeni deney aralığı: denge derişimleri doygunluk",
            "bölgesine girmiyor. qmax doygunluk düzeyidir;",
            "ulaşılmamış bir düzey veriden güvenilir biçimde",
            "çıkarılamaz.",
            "",
            "**Bu yüzden qmax tek başına raporlanmamalı.**",
        ], renk=AMBER),
    ]

    # ----------------------------------- 3. sütun: sonuç, beyan, kaynak
    sutun3 = [
        Kutu("7 · Sonuçlar", [
            f"**1.** Adsorban etkisi anlamlı: F(1, {sd}) = "
            f"{ts(ads['F'], 1)},",
            f"kısmi eta kare = {ts(ads['kismi_eta_kare'], 3)}.",
            "",
            f"**2.** pH en güçlü etken: F(2, {sd}) = {ts(ph['F'], 1)},",
            f"kısmi eta kare = {ts(ph['kismi_eta_kare'], 3)}.",
            "",
            "**3.** Etkileşim anlamlı; üstünlük pH'a bağlı.",
            "",
            "**4.** Çay posası pH 10'da ticariye yaklaşıyor —",
            "atık değerlendirme açısından çalışılmaya değer.",
            "",
            "**5.** Bulgular şüpheli cihaz döneminden",
            "bağımsız: duyarlılık analizinde hiçbir",
            "anlamlılık kararı değişmedi.",
        ], renk=TURKUAZ),
        Kutu("Sonraki adım", [
            "Çay posası için derişim aralığı doygunluğu",
            "kapsayacak biçimde genişletilmeli; ancak o",
            "zaman qmax karşılaştırması anlamlı olur.",
            "",
            "Ardından sürekli akışlı kolon denemesi ve",
            "gerçek tekstil atık suyuyla doğrulama.",
        ]),
        Kutu("Veri ve yapay zekâ beyanı", [
            "Bu poster bir öğretim örneğidir. Veri sentetiktir:",
            "Langmuir izotermi ve kütle dengesi birlikte",
            "çözülerek üretildi, sonra laboratuvar kirleri",
            "eklendi. **Hiçbir sayı gerçek bir ölçümden gelmiyor**",
            "ve bulgu olarak alıntılanamaz.",
            "",
            "Posterin içeriği ve yerleşim planı bir büyük dil",
            "modeline yazdırıldı. Sayılar analiz çıktısından",
            "okunarak çizildi, elle girilmedi.",
            "",
            "Üreten kod ve veri açık: kod/13–18, veri/kimya/",
        ], renk=GRI),
        Kutu("Kaynaklar", [
            "Langmuir, I. (1918). J. Am. Chem. Soc., 40(9),",
            "1361–1403.",
            "Freundlich, H. (1906). Z. Phys. Chem., 57, 385–470.",
            "Cohen, J. (1988). Statistical Power Analysis for",
            "the Behavioral Sciences (2. baskı).",
        ], renk=GRI),
    ]

    for kutular, x in ((sutun1, KENAR),
                       (sutun2, KENAR + sg + SUTUN_ARA),
                       (sutun3, KENAR + 2 * (sg + SUTUN_ARA))):
        parca, _ = sutun_yerlestir(kutular, x, ust, alt, sg, K)
        p.append(parca)

    p.append(f'<rect x="0" y="{YUK - 26}" width="{GEN}" height="26" '
             f'fill="{LACIVERT}"/>')
    p.append(f'<text x="{KENAR}" y="{YUK - 9}" font-size="10" '
             f'fill="#C3D1E0">Sentetik veri · yöntem örneğidir, bulgu '
             f'değildir · poster, 12. bölümdeki istemin çıktısıdır</text>')
    p.append('</svg>')

    yol = K / "p01_poster.svg"
    yol.write_text("\n".join(p), encoding="utf-8")
    print(f"Poster yazıldı → {yol}  ({yol.stat().st_size / 1024:.1f} KB)")
    print(f"  A0 · {GEN} × {YUK} mm · dört şekil gömülü")

    # PNG sürümü: sunum ve baskı provası için. Diğer şekiller bunu
    # matplotlib ile alıyor; bu şekil elle yazıldığı için rsvg-convert
    # ile dönüştürülüyor. Araç yoksa adım sessizce atlanır — poster
    # SVG olarak zaten tamdır.
    png = K.parent / "sekil_png" / "p01_poster.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    arac = shutil.which("rsvg-convert")
    if arac:
        # 1400 piksel genişlik: web önizlemesi için yeterli, dosya
        # boyutu makul. Baskı için SVG kullanılır.
        subprocess.run([arac, "-w", "1400", "-o", str(png), str(yol)],
                       check=True)
        print(f"  PNG sürümü → {png}  "
              f"({png.stat().st_size / 1024:.0f} KB)")
    else:
        print("  PNG atlandı: rsvg-convert bulunamadı "
              "(brew install librsvg)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
