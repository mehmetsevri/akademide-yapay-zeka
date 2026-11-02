/* Canlı anlatımlar — modelin davranışını adım adım gösteren
   etkileşimli çizimler.

   Sayfada `:::canli tur="..."` bloğu bir kap bırakır; bu betik o
   kapları bulur ve içini kurar. Dış bağımlılık yok, çerez yok, ağ
   isteği yok: dosyayı açtığınızda çalışır.

   DÜRÜSTLÜK KURALI — buradaki olasılıklar ve parçalanmalar gerçek
   bir modelden alınmadı; mekanizmayı göstermek için elle seçildi.
   Her çizim bunu kendi altında yazar. Gerçek olan tek hesap sıcaklık
   formülüdür: p^(1/T) yeniden ölçekleme, modellerde de budur. */
(function () {
  "use strict";

  var AZ_HAREKET = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function el(etiket, sinif, metin) {
    var d = document.createElement(etiket);
    if (sinif) { d.className = sinif; }
    if (metin !== undefined) { d.textContent = metin; }
    return d;
  }

  function dugme(metin, sinif) {
    var b = el("button", "c-dugme" + (sinif ? " " + sinif : ""), metin);
    b.type = "button";
    return b;
  }

  function yuzde(p) {
    return (p * 100).toFixed(p < 0.1 ? 1 : 0).replace(".", ",") + "%";
  }

  /* Her çizimin altına aynı biçimde düşülen kaynak notu. */
  function damga(kok, metin) {
    kok.appendChild(el("p", "c-damga", metin));
  }

  /* --------------------------------------------------- 1 · sonraki sözcük */

  /* Cümle: "Bu çalışmada elde edilen bulgular, önceki çalışmalarla
     büyük ölçüde örtüşmektedir."  Her adımda modelin önüne koyduğu
     metin büyür ve beş aday yeniden sıralanır. */
  var ADIMLAR = [
    {aday: [["önceki", 0.38], ["literatürde", 0.19], ["bu", 0.12],
            ["daha", 0.09], ["genel", 0.07]]},
    {aday: [["çalışmalarla", 0.44], ["araştırmalarla", 0.26],
            ["yıllarda", 0.11], ["bulgularla", 0.08], ["dönemde", 0.05]]},
    {aday: [["büyük", 0.31], ["kısmen", 0.18], ["genel", 0.14],
            ["kısmi", 0.12], ["tam", 0.10]]},
    {aday: [["ölçüde", 0.67], ["oranda", 0.14], ["bir", 0.09],
            ["düzeyde", 0.05], ["farkla", 0.03]]},
    {aday: [["örtüşmektedir", 0.29], ["uyumludur", 0.24],
            ["tutarlıdır", 0.19], ["benzerlik", 0.08], ["paralellik", 0.07]]},
    {aday: [[".", 0.52], ["; ancak", 0.11], [" fakat", 0.10],
            [" ve", 0.08], [" ayrıca", 0.06]]}
  ];
  var BASLANGIC = "Bu çalışmada elde edilen bulgular,";

  function sonrakiSozcuk(kok) {
    var i = 0, oynuyor = null;

    var metinKutu = el("div", "c-metin");
    var etiketP = el("p", "c-ust-etiket", "Modelin o anda gördüğü metin");
    var barKutu = el("div", "c-barlar");
    var barEtiket = el("p", "c-ust-etiket",
                       "Sıradaki sözcük için olasılıklar");
    var sayac = el("span", "c-sayac", "");

    function metniYaz(yeni) {
      metinKutu.textContent = "";
      metinKutu.appendChild(document.createTextNode(BASLANGIC + " "));
      for (var a = 0; a < i; a++) {
        var s = el("span", "c-sozcuk", ADIMLAR[a].aday[0][0]);
        if (yeni && a === i - 1) { s.classList.add("c-yeni"); }
        metinKutu.appendChild(s);
        metinKutu.appendChild(document.createTextNode(" "));
      }
      if (i < ADIMLAR.length) {
        metinKutu.appendChild(el("span", "c-imlec", "▌"));
      }
    }

    function barlariYaz() {
      barKutu.textContent = "";
      if (i >= ADIMLAR.length) {
        barKutu.appendChild(el("p", "c-bitti",
          "Cümle tamamlandı. Nokta da bir sözcük gibi seçildi."));
        sayac.textContent = "bitti";
        return;
      }
      sayac.textContent = "adım " + (i + 1) + " / " + ADIMLAR.length;
      ADIMLAR[i].aday.forEach(function (a, k) {
        var satir = el("div", "c-bar" + (k === 0 ? " c-bar-ust" : ""));
        satir.appendChild(el("span", "c-bar-ad", a[0]));
        var oluk = el("span", "c-oluk");
        var dolu = el("span", "c-dolu");
        dolu.style.width = (a[1] * 100) + "%";
        oluk.appendChild(dolu);
        satir.appendChild(oluk);
        satir.appendChild(el("span", "c-bar-sayi", yuzde(a[1])));
        barKutu.appendChild(satir);
      });
    }

    function adim() {
      if (i >= ADIMLAR.length) { return false; }
      i++;
      metniYaz(true);
      barlariYaz();
      return i < ADIMLAR.length;
    }

    function basa() {
      dur();
      i = 0;
      metniYaz(false);
      barlariYaz();
    }

    function dur() {
      if (oynuyor) { clearInterval(oynuyor); oynuyor = null; }
      oynatD.textContent = "Oynat";
    }

    var araclar = el("div", "c-araclar");
    var adimD = dugme("Bir adım", "c-birincil");
    var oynatD = dugme("Oynat");
    var basaD = dugme("Baştan");
    adimD.addEventListener("click", function () { dur(); adim(); });
    oynatD.addEventListener("click", function () {
      if (oynuyor) { dur(); return; }
      if (i >= ADIMLAR.length) { basa(); }
      oynatD.textContent = "Durdur";
      oynuyor = setInterval(function () {
        if (!adim()) { dur(); }
      }, AZ_HAREKET ? 1400 : 950);
    });
    basaD.addEventListener("click", basa);
    [adimD, oynatD, basaD].forEach(function (d) { araclar.appendChild(d); });
    araclar.appendChild(sayac);

    kok.appendChild(etiketP);
    kok.appendChild(metinKutu);
    kok.appendChild(barEtiket);
    kok.appendChild(barKutu);
    kok.appendChild(araclar);
    damga(kok, "Canlandırma. Olasılıklar mekanizmayı göstermek için " +
               "seçildi; gerçek bir modelden okunmadı. Gerçek modelde " +
               "aday sayısı beş değil, on binlercedir.");
    basa();
  }

  /* ------------------------------------------------------- 2 · sıcaklık */

  /* Dört karar noktası. Sıcaklık, bu dağılımları yeniden ölçekler. */
  var SICAK_ADIM = [
    {oncesi: "Bulgular önceki çalışmalarla ",
     aday: [["büyük ölçüde", 0.42], ["kısmen", 0.24], ["genel hatlarıyla", 0.16],
            ["sınırlı biçimde", 0.11], ["beklenenden az", 0.07]]},
    {oncesi: " ",
     aday: [["örtüşmektedir", 0.38], ["uyumludur", 0.27], ["tutarlıdır", 0.18],
            ["benzerlik göstermektedir", 0.11], ["paralellik taşımaktadır", 0.06]]},
    {oncesi: "; ancak ",
     aday: [["örneklem büyüklüğü", 0.36], ["ölçüm aracı", 0.25],
            ["çalışma deseni", 0.20], ["veri toplama dönemi", 0.12],
            ["katılımcı profili", 0.07]]},
    {oncesi: " farklıdır",
     aday: [[".", 0.61], [" ve bu fark yoruma yansıtılmalıdır.", 0.18],
            [", bu nedenle karşılaştırma dikkatli yapılmalıdır.", 0.13],
            [", dolayısıyla genelleme sınırlıdır.", 0.08]]}
  ];

  /* Sıcaklık ölçeklemesi: w = p^(1/T), sonra normalize. Modellerde
     yapılan işlem budur (logit'i T'ye bölmek buna denk düşer).
     T = 0 sınır durumu: en yüksek olasılık 1, kalanlar 0. */
  function olcekle(aday, T) {
    if (T <= 0.001) {
      return aday.map(function (a, k) { return k === 0 ? 1 : 0; });
    }
    var us = 1 / T, toplam = 0;
    var w = aday.map(function (a) {
      var v = Math.pow(a[1], us); toplam += v; return v;
    });
    return w.map(function (v) { return v / toplam; });
  }

  function ornekle(aday, agirlik) {
    var r = Math.random(), bir = 0;
    for (var k = 0; k < aday.length; k++) {
      bir += agirlik[k];
      if (r <= bir) { return k; }
    }
    return aday.length - 1;
  }

  function cumleUret(T) {
    var parca = [];
    SICAK_ADIM.forEach(function (ad) {
      var k = ornekle(ad.aday, olcekle(ad.aday, T));
      parca.push(ad.oncesi + ad.aday[k][0]);
    });
    return parca.join("").replace(/\s+/g, " ").trim();
  }

  function sicaklik(kok) {
    var T = 0.7;

    var ayar = el("div", "c-ayar");
    var etiket = el("label", "c-ayar-ad", "Sıcaklık");
    var kaydirak = document.createElement("input");
    kaydirak.type = "range";
    kaydirak.min = "0"; kaydirak.max = "1.2"; kaydirak.step = "0.1";
    kaydirak.value = String(T);
    kaydirak.id = "c-sicaklik-" + Math.random().toString(36).slice(2, 7);
    etiket.setAttribute("for", kaydirak.id);
    var deger = el("output", "c-ayar-deger", "0,7");
    ayar.appendChild(etiket);
    ayar.appendChild(kaydirak);
    ayar.appendChild(deger);

    var barKutu = el("div", "c-barlar");
    var barEtiket = el("p", "c-ust-etiket",
      "İlk karar noktasındaki olasılıklar — sıcaklığa göre yeniden ölçekli");

    function barlariYaz() {
      var aday = SICAK_ADIM[0].aday, w = olcekle(aday, T);
      barKutu.textContent = "";
      aday.forEach(function (a, k) {
        var satir = el("div", "c-bar");
        satir.appendChild(el("span", "c-bar-ad", a[0]));
        var oluk = el("span", "c-oluk");
        var dolu = el("span", "c-dolu");
        dolu.style.width = (w[k] * 100) + "%";
        if (w[k] < 0.005) { dolu.classList.add("c-dolu-yok"); }
        oluk.appendChild(dolu);
        satir.appendChild(oluk);
        satir.appendChild(el("span", "c-bar-sayi", yuzde(w[k])));
        barKutu.appendChild(satir);
      });
    }

    var gecmis = el("ol", "c-gecmis");
    var gecmisEtiket = el("p", "c-ust-etiket", "Koşular");
    var bosluk = el("p", "c-bos",
      "Sıcaklık değişti. Bu ayardaki koşuları görmek için düğmeye basın.");

    /* Koşu listesi tek bir sıcaklığa aittir. Kaydırak oynatıldığında
       eski koşular silinir: iki ayrı sıcaklıkta üretilmiş cümlelerin
       aynı listede yan yana durması, canlandırmanın anlatmak istediği
       şeyi — sıcaklığın çeşitliliği belirlediğini — tam tersine
       çevirir. Her satır yine de kendi sıcaklığını taşır. */
    function gecmisiSifirla() {
      gecmis.textContent = "";
      bosluk.hidden = false;
      ikiKisi.textContent = "";
    }

    function kosuEkle(metin) {
      bosluk.hidden = true;
      var li = el("li", "");
      li.appendChild(el("span", "c-kosu-sicaklik",
                        "T = " + T.toFixed(1).replace(".", ",")));
      li.appendChild(document.createTextNode(" " + metin));
      gecmis.insertBefore(li, gecmis.firstChild);
      while (gecmis.children.length > 5) {
        gecmis.removeChild(gecmis.lastChild);
      }
    }

    var ikiKisi = el("div", "c-iki-kisi");
    function ikiKisiYaz() {
      var a = cumleUret(T), b = cumleUret(T);
      ikiKisi.textContent = "";
      [["Birinci kişi", a], ["İkinci kişi", b]].forEach(function (p) {
        var kutu = el("div", "c-kisi");
        kutu.appendChild(el("span", "c-kisi-ad", p[0]));
        kutu.appendChild(el("p", "", p[1]));
        ikiKisi.appendChild(kutu);
      });
      var sonuc = el("p", "c-sonuc");
      sonuc.textContent = (a === b)
        ? "Bu koşuda ikisi aynı cümleyi aldı. Sıcaklık düştükçe bu "
          + "beklenen sonuçtur."
        : "Aynı istem, aynı model, aynı an — iki farklı cümle. "
          + "Seçim her adımda yeniden çekiliyor.";
      sonuc.className = "c-sonuc " + (a === b ? "c-ayni" : "c-farkli");
      ikiKisi.appendChild(sonuc);
    }

    var araclar = el("div", "c-araclar");
    var kosD = dugme("Bir kez koştur", "c-birincil");
    var ikiD = dugme("İki kişi aynı anda sorsun");
    kosD.addEventListener("click", function () { kosuEkle(cumleUret(T)); });
    ikiD.addEventListener("click", ikiKisiYaz);
    araclar.appendChild(kosD);
    araclar.appendChild(ikiD);

    kaydirak.addEventListener("input", function () {
      var yeniT = parseFloat(kaydirak.value);
      if (yeniT === T) { return; }
      T = yeniT;
      deger.textContent = T.toFixed(1).replace(".", ",");
      barlariYaz();
      gecmisiSifirla();
    });

    kok.appendChild(ayar);
    kok.appendChild(barEtiket);
    kok.appendChild(barKutu);
    kok.appendChild(araclar);
    kok.appendChild(gecmisEtiket);
    kok.appendChild(bosluk);
    kok.appendChild(gecmis);
    kok.appendChild(ikiKisi);
    damga(kok, "Çubuklar gerçek sıcaklık formülüyle hesaplanıyor: " +
               "olasılıklar 1/T kuvvetine yükseltilip yeniden " +
               "ölçekleniyor. Başlangıç olasılıkları ise gösterim için " +
               "seçildi. Sıcaklık sıfırken her koşu aynı cümleyi verir.");
    barlariYaz();
    bosluk.hidden = true;
    kosuEkle(cumleUret(T));
  }

  /* -------------------------------------------------- 3 · belgeden cevap */

  var BELGE = [
    {m: "Bu kesitsel çalışmaya bir devlet üniversitesinin eğitim " +
        "fakültesinden "},
    {m: "214 öğretmen adayı", iz: 1},
    {m: " katıldı. Veriler Mart–Nisan 2026'da çevrim içi anketle " +
        "toplandı. Ölçeğin Cronbach alfa katsayısı 0,88 bulundu. " +
        "Gruplar arası farklar "},
    {m: "bağımsız örneklem t-testi", iz: 2},
    {m: " ile sınandı; "},
    {m: "cinsiyete göre anlamlı fark saptanmadı (t = 1,42; p = 0,157)", iz: 3},
    {m: "."}
  ];
  var SORU = "Çalışmaya kaç kişi katıldı, hangi test kullanıldı, " +
             "sonuç ne çıktı?";
  var YANIT = [
    {m: "Çalışmaya 214 öğretmen adayı katılmıştır", iz: 1},
    {m: ". Gruplar arası farklar bağımsız örneklem t-testi ile " +
        "sınanmıştır", iz: 2},
    {m: ". Cinsiyete göre anlamlı fark bulunmamıştır (t = 1,42; " +
        "p = 0,157)", iz: 3},
    {m: "."}
  ];
  var BELGESIZ = "Çalışmaya yaklaşık 250 öğretmen adayı katılmış, " +
      "gruplar ANOVA ile karşılaştırılmış ve cinsiyete göre anlamlı " +
      "fark bulunmuştur (p < 0,05).";

  function belgedenCevap(kok) {
    var belgeli = true, zaman = null;

    var secim = el("div", "c-secim");
    var d1 = dugme("Belge ekte", "c-birincil");
    var d2 = dugme("Belge verilmedi");
    secim.appendChild(d1);
    secim.appendChild(d2);

    var soruKutu = el("p", "c-soru");
    soruKutu.appendChild(el("span", "c-soru-ad", "Soru"));
    soruKutu.appendChild(document.createTextNode(" " + SORU));

    var belgeKutu = el("div", "c-belge");
    var belgeEtiket = el("p", "c-ust-etiket", "Eke konan belge");
    var yanitEtiket = el("p", "c-ust-etiket", "Modelin yanıtı");
    var yanitKutu = el("div", "c-yanit");
    yanitKutu.setAttribute("aria-live", "polite");

    function belgeyiYaz() {
      belgeKutu.textContent = "";
      BELGE.forEach(function (p) {
        if (!p.iz) {
          belgeKutu.appendChild(document.createTextNode(p.m));
          return;
        }
        var s = el("span", "c-iz c-iz-" + p.iz, p.m);
        s.appendChild(el("sup", "c-iz-no", String(p.iz)));
        belgeKutu.appendChild(s);
      });
    }

    function temizle() {
      if (zaman) { clearTimeout(zaman); zaman = null; }
      yanitKutu.textContent = "";
      belgeKutu.querySelectorAll(".c-iz").forEach(function (s) {
        s.classList.remove("c-iz-acik");
      });
    }

    function kur() {
      temizle();
      if (!belgeli) {
        var p = el("p", "c-uydurma", BELGESIZ);
        yanitKutu.appendChild(p);
        yanitKutu.appendChild(el("p", "c-uyari-satir",
          "Cümle akıcı, biçim doğru, sayılar inandırıcı. Hiçbirinin " +
          "dayanağı yok: belge verilmediği için model boşluğu kendi " +
          "örüntüsünden doldurdu. Burada doğrulanacak bir yer bile " +
          "yok — karşılaştıracağınız bir kaynak ortada değil."));
        return;
      }
      var k = 0;
      var p2 = el("p", "");
      yanitKutu.appendChild(p2);
      (function sira() {
        if (k >= YANIT.length) {
          yanitKutu.appendChild(el("p", "c-uyari-satir",
            "Yanıttaki her parça belgedeki bir yere dayanıyor. " +
            "Doğrulama işi de bu yüzden kısa: numarayı takip edip " +
            "belgeye bakarsınız."));
          return;
        }
        var y = YANIT[k];
        if (y.iz) {
          var kay = belgeKutu.querySelector(".c-iz-" + y.iz);
          if (kay) { kay.classList.add("c-iz-acik"); }
          var s = el("span", "c-cevap-parca c-iz-" + y.iz, y.m);
          s.appendChild(el("sup", "c-iz-no", String(y.iz)));
          p2.appendChild(s);
        } else {
          p2.appendChild(document.createTextNode(y.m));
        }
        k++;
        zaman = setTimeout(sira, AZ_HAREKET ? 900 : 650);
      })();
    }

    function modSec(yeni) {
      belgeli = yeni;
      d1.classList.toggle("c-birincil", yeni);
      d2.classList.toggle("c-birincil", !yeni);
      belgeKutu.hidden = !yeni;
      belgeEtiket.hidden = !yeni;
      kur();
    }
    d1.addEventListener("click", function () { modSec(true); });
    d2.addEventListener("click", function () { modSec(false); });

    kok.appendChild(secim);
    kok.appendChild(soruKutu);
    kok.appendChild(belgeEtiket);
    kok.appendChild(belgeKutu);
    kok.appendChild(yanitEtiket);
    kok.appendChild(yanitKutu);
    damga(kok, "Canlandırma. Belge metni bu kurs için yazıldı; " +
               "gerçek bir çalışmadan alınmadı. Gösterilen şey " +
               "sayıların kendisi değil, yanıtın nereye dayandığı.");
    belgeyiYaz();
    modSec(true);
  }

  /* ---------------------------------------------------------- 4 · jeton */

  var JETON = [
    {ad: "Kısa cümle",
     tr: ["Öğret", "men", "lerin", " ders", "e", " hazır", "lan", "ma",
          " biçim", "leri", " değiş", "ti", "."],
     en: ["Teach", "ers", "'", " lesson", " prepar", "ation", " has",
          " changed", "."]},
    {ad: "Yöntem cümlesi",
     tr: ["Grup", "lar", " arası", " fark", "lar", " bağım", "sız",
          " örnek", "lem", " t", "-test", "i", " ile", " sına", "n",
          "mıştır", "."],
     en: ["Group", " differences", " were", " tested", " with", " an",
          " independent", " samples", " t", "-test", "."]},
    {ad: "Bulgu cümlesi",
     tr: ["Çalış", "ma", "mız", "da", " elde", " edil", "en", " bulgu",
          "lar", " önce", "ki", " araştır", "ma", "lar", "la",
          " örtüş", "mekte", "dir", "."],
     en: ["Our", " findings", " are", " consistent", " with", " previous",
          " research", "."]}
  ];

  function jeton(kok) {
    var i = 0;

    var secim = el("div", "c-secim");
    var kutular = el("div", "c-jeton-ikili");

    function yaz() {
      kutular.textContent = "";
      [["Türkçe", JETON[i].tr], ["İngilizce", JETON[i].en]].forEach(
        function (p) {
          var kutu = el("div", "c-jeton-kutu");
          var bas = el("div", "c-jeton-bas");
          bas.appendChild(el("span", "c-kisi-ad", p[0]));
          bas.appendChild(el("span", "c-jeton-sayi", p[1].length + " jeton"));
          kutu.appendChild(bas);
          var sira = el("div", "c-jetonlar");
          p[1].forEach(function (j, k) {
            var c = el("span", "c-jeton", j.replace(/ /g, "␣"));
            c.style.animationDelay = (AZ_HAREKET ? 0 : k * 45) + "ms";
            sira.appendChild(c);
          });
          kutu.appendChild(sira);
          kutu.appendChild(el("p", "c-jeton-tam", p[1].join("")));
          kutular.appendChild(kutu);
        });
      var fark = JETON[i].tr.length / JETON[i].en.length;
      kutular.appendChild(el("p", "c-sonuc c-farkli",
        "Aynı anlam, " + fark.toFixed(1).replace(".", ",") +
        " kat jeton. Fark, Türkçenin ekleri ayrı parçalara " +
        "bölünmesinden geliyor."));
    }

    JETON.forEach(function (j, k) {
      var b = dugme(j.ad, k === 0 ? "c-birincil" : "");
      b.addEventListener("click", function () {
        i = k;
        secim.querySelectorAll(".c-dugme").forEach(function (d, n) {
          d.classList.toggle("c-birincil", n === k);
        });
        yaz();
      });
      secim.appendChild(b);
    });

    kok.appendChild(secim);
    kok.appendChild(kutular);
    damga(kok, "Canlandırma. Parçalanma gerçek bir jeton sayıcıdan " +
               "değil; yaygın davranışı göstermek için elle hazırlandı. " +
               "Kesin sayı gerekiyorsa sağlayıcının jeton sayma ucunu " +
               "kullanın. ␣ işareti sözcük başındaki boşluğu gösterir.");
    yaz();
  }

  /* ------------------------------------------------ 5 · istemin parçaları */

  /* ======================================= istemin altı parçası ======
     Eski sürüm çıktıyı AÇIK PARÇA SAYISINA göre seçiyordu. Bu yanlıştı:
     ROL, KAYNAK ve GÖREV'i kapatıp BİÇİM, SINIR ve DENETİM'i açınca
     sayı yine üç kalıyor ve çıktı hiç değişmiyordu — altı düğmeye
     sırayla basan okur, hiçbir şey olmadığını görüyordu.

     Yeni sürüm çıktıyı parçaların KENDİSİNDEN kuruyor. Her parça
     çıktının belirli bir niteliğinden sorumlu:

       GÖREV   yoksa ortada iş yoktur; model işi kendi tanımlar
       BİÇİM   yoksa düzyazı gelir, varsa tablo
       KAYNAK  yoksa madde numarası verilemez, genel konuşulur
       SINIR   yoksa model istenmeyen işi de yapar (yeni madde önerir)
       DENETİM yoksa kaç maddeye bakıldığı bilinmez
       ROL     yoksa alan dili yerine gündelik dil gelir
  */
  var PARCA = [
    {ad: "ROL", acik: "Hangi uzmanlıkla bakacağı",
     katki: "Yorumun düzeyi yükselir: genel geçer tavsiye yerine alan dili.",
     istem: "ROL\nÖlçek geliştirme ve madde yazımı üzerine çalışan bir\n" +
            "ölçme ve değerlendirme uzmanısın."},
    {ad: "KAYNAK", acik: "Neye dayanacağı",
     katki: "Model kendi belleğinden değil, verdiğiniz belgeden çalışır.",
     istem: "KAYNAK\nanket_madde_sozlugu.csv — 21 madde, beşli Likert.\n" +
            "Yalnız bu dosyadaki maddelere bak."},
    {ad: "GÖREV", acik: "Ne yapacağı",
     katki: "İşin kendisi belirlenir; yoksa model işi kendi tanımlar.",
     istem: "GÖREV\nHer maddeyi madde yazım ölçütlerine göre denetle:\n" +
            "1 çift ifade · 2 yönlendirme · 3 belirsizlik · 4 olumsuz kalıp."},
    {ad: "BİÇİM", acik: "Çıktının yapısı",
     katki: "Çıktı karşılaştırılabilir hâle gelir: aynı sütunlar, aynı sıra.",
     istem: "BİÇİM\nÇıktıyı tablo ver: No | Sorun | Ölçüt | Düzeltme.\n" +
            "Tablonun dışına açıklama yazma."},
    {ad: "SINIR", acik: "Ne yapmayacağı",
     katki: "Uydurma kapanır: olmayan kaydı eklemesi engellenir.",
     istem: "SINIR\nYeni madde önerme, ölçeğin kapsamını tartışma.\n" +
            "Dosyada olmayan bir maddeye değinme."},
    {ad: "DENETİM", acik: "Kendi işini nasıl sayacağı",
     katki: "Eksiği siz aramazsınız; model kaçını atladığını söyler.",
     istem: "DENETİM\nSonunda tek satır yaz: kaç madde denetledin,\n" +
            "kaçında sorun buldun, hangileri ters kodlanmalı."}
  ];

  var ROL_I = 0, KAYNAK_I = 1, GOREV_I = 2, BICIM_I = 3, SINIR_I = 4,
      DENETIM_I = 5;

  function istemKur(acik) {
    var parcalar = [];
    PARCA.forEach(function (p, k) {
      if (acik[k]) { parcalar.push(p.istem); }
    });
    if (!parcalar.length) {
      return "Ölçek maddelerime bir bakar mısın?";
    }
    return parcalar.join("\n\n");
  }

  function ciktiKur(acik) {
    var rol = acik[ROL_I], kaynak = acik[KAYNAK_I], gorev = acik[GOREV_I],
        bicim = acik[BICIM_I], sinir = acik[SINIR_I],
        denetim = acik[DENETIM_I];

    /* Görev yoksa ortada tanımlı bir iş yoktur. Diğer parçalar ne
       olursa olsun model önce işi kendi tanımlar; bu yüzden bu dal
       ayrı duruyor. */
    if (!gorev) {
      return {
        metin: rol
          ? "Ölçek maddeleri genel hatlarıyla alan yazınıyla uyumlu\n" +
            "görünüyor. Madde yazımında açıklık ve tek boyutluluk\n" +
            "ilkelerine dikkat edilmesi yerinde olur."
          : "Maddeler genel olarak iyi görünüyor. Bazılarını yeniden\n" +
            "yazabilirsiniz. Anketlerde soruların anlaşılır olması\n" +
            "önemlidir.",
        not: "GÖREV yok: model işi kendi tanımladı ve genel geçer bir " +
             "metin yazdı. Denetlenecek bir şey üretmedi."
      };
    }

    var satirlar = [];
    if (bicim) {
      satirlar.push("| No | Sorun | Ölçüt | Düzeltme |");
      if (kaynak) {
        satirlar.push("| 3 | Çift ifade | 1 | “…zenginleştiriyor.” |");
        satirlar.push("| 7 | Yönlendirme | 2 | “…yer alacaktır.” |");
        satirlar.push("| 12 | Belirsizlik | 3 | “Ders hazırlığımda…” |");
      } else {
        satirlar.push("| — | Çift ifade | 1 | Maddeyi ikiye bölün |");
        satirlar.push("| — | Yönlendirme | 2 | Yargı bildiren sıfatı atın |");
        satirlar.push("| — | Belirsizlik | 3 | Zaman aralığını yazın |");
      }
    } else if (kaynak) {
      satirlar.push(rol
        ? "3. maddede çift ifade var: iki ayrı yargı tek maddede\n" +
          "soruluyor. 7. madde yönlendirici; 12. maddede zaman\n" +
          "aralığı belirsiz."
        : "3. ve 7. maddelerde sorun görünüyor, 12. madde de biraz\n" +
          "belirsiz. Bunları düzeltmenizi öneririm.");
    } else {
      satirlar.push(rol
        ? "Maddelerin bir bölümünde çift ifade ve yönlendirme sorunu\n" +
          "bulunmaktadır; bazı maddelerde de zaman aralığı belirsizdir."
        : "Maddelerin bir bölümünde çift ifade ve yönlendirme sorunu\n" +
          "var. Bunları düzeltmenizi öneririm.");
    }

    if (!sinir) {
      satirlar.push("");
      satirlar.push("Ayrıca ölçeğe şu iki maddeyi eklemenizi öneririm:\n" +
                    "“Bu araçları haftada kaç kez kullanıyorum” ve\n" +
                    "“Kurumumun bu konudaki politikasını biliyorum”.");
    }
    if (denetim) {
      satirlar.push("");
      /* Tek satıra sığmıyor: dar sütunda sarılıp tablo hizasını
         bozuyordu. İki satıra bölündü. */
      satirlar.push("DENETİM — 21 madde denetlendi, 9'unda sorun var.\n" +
                    "Ters kodlanacak maddeler: 5, 11, 17");
    }

    /* Not, eksik olan İLK parçanın sonucunu söyler: okur neyi
       açtığında ne kazanacağını görsün. */
    var not;
    if (!bicim) {
      not = "BİÇİM yok: iş tanımlandı ama çıktının yapısı serbest. " +
            "İki koşuda iki farklı düzen gelir, karşılaştıramazsınız.";
    } else if (!kaynak) {
      not = "KAYNAK yok: tablo geldi ama madde numarası yok. Model " +
            "dosyayı görmediği için hangi maddeden söz ettiğini " +
            "söyleyemiyor.";
    } else if (!sinir) {
      not = "SINIR yok: model istenmeyen işi de yaptı, ölçeğe yeni " +
            "madde önerdi. Bu maddeler sizin ölçeğinizde yok.";
    } else if (!denetim) {
      not = "DENETİM yok: tablo temiz ama kaç maddeye bakıldığı " +
            "yazmıyor. Atlanan madde varsa göremezsiniz.";
    } else if (!rol) {
      not = "Altı parçanın beşi yerinde. ROL olmadan da iş yapılır; " +
            "eklenince dil alanın diline yaklaşır.";
    } else {
      not = "Altı parça da yerinde. Son satır önemli: 21 sayısı " +
            "tutmuyorsa bir şey atlanmıştır ve bunu siz saymadan " +
            "görürsünüz.";
    }
    return {metin: satirlar.join("\n"), not: not};
  }

  function istemParcalari(kok) {
    var acik = [true, true, true, false, false, false];

    var dugmeler = el("div", "c-parcalar");
    var istemKutu = el("pre", "c-istem-onizleme");
    var ciktiKutu = el("div", "c-cikti-ornek");
    ciktiKutu.setAttribute("aria-live", "polite");
    var notKutu = el("p", "c-uyari-satir");
    var sayac = el("span", "c-sayac");

    function yaz() {
      var d = ciktiKur(acik);
      istemKutu.textContent = istemKur(acik);
      ciktiKutu.textContent = d.metin;
      notKutu.textContent = d.not;
      sayac.textContent = acik.filter(Boolean).length + " / 6 parça açık";
      dugmeler.querySelectorAll(".c-parca").forEach(function (b, k) {
        b.classList.toggle("c-parca-acik", acik[k]);
        b.setAttribute("aria-pressed", acik[k] ? "true" : "false");
      });
    }

    PARCA.forEach(function (p, k) {
      var b = el("button", "c-parca");
      b.type = "button";
      b.appendChild(el("span", "c-parca-ad", p.ad));
      b.appendChild(el("span", "c-parca-acik-yazi", p.acik));
      b.title = p.katki;
      b.addEventListener("click", function () { acik[k] = !acik[k]; yaz(); });
      dugmeler.appendChild(b);
    });

    var tumu = dugme("Altısını da aç", "c-birincil");
    var hic = dugme("Hepsini kapat");
    tumu.addEventListener("click", function () {
      acik = [true, true, true, true, true, true]; yaz();
    });
    hic.addEventListener("click", function () {
      acik = [false, false, false, false, false, false]; yaz();
    });
    var araclar = el("div", "c-araclar");
    araclar.appendChild(tumu);
    araclar.appendChild(hic);
    araclar.appendChild(sayac);

    kok.appendChild(el("p", "c-amac",
      "Amaç: aynı iş için yazılan istemin, hangi parçası eklendiğinde " +
      "çıktının hangi niteliğini kazandığını görmek. Soldaki istem " +
      "düğmelere göre kuruluyor; sağdaki çıktı o isteme karşılık " +
      "geliyor."));
    kok.appendChild(el("p", "c-ust-etiket",
      "Parçaları açıp kapatın — istem de çıktı da buna göre değişir"));
    kok.appendChild(dugmeler);
    kok.appendChild(araclar);

    var ikili = el("div", "c-istem-ikili");
    var sol = el("div", "");
    sol.appendChild(el("p", "c-ust-etiket", "Modele giden istem"));
    sol.appendChild(istemKutu);
    var sag = el("div", "");
    sag.appendChild(el("p", "c-ust-etiket", "Beklenen çıktı"));
    sag.appendChild(ciktiKutu);
    ikili.appendChild(sol);
    ikili.appendChild(sag);
    kok.appendChild(ikili);
    kok.appendChild(notKutu);

    damga(kok, "Canlandırma. İstem metinleri gerçek; çıktılar bu kurs " +
               "için yazıldı ve düğmeler bir modele bağlı değil. " +
               "Gösterilen şey hangi parçanın çıktının hangi niteliğini " +
               "belirlediği.");
    yaz();
  }

  /* ------------------------------------------------------------- kurulum */

  var KURUCU = {
    "sonraki-sozcuk": sonrakiSozcuk,
    "sicaklik": sicaklik,
    "belgeden-cevap": belgedenCevap,
    "jeton": jeton,
    "istem-parcalari": istemParcalari
  };

  function kur() {
    var kaplar = document.querySelectorAll("[data-canli]");
    for (var i = 0; i < kaplar.length; i++) {
      var tur = kaplar[i].getAttribute("data-canli");
      var f = KURUCU[tur];
      if (!f) { continue; }
      kaplar[i].textContent = "";
      try {
        f(kaplar[i]);
      } catch (hata) {
        /* Bir çizim patlarsa sayfanın geri kalanı etkilenmesin. */
        kaplar[i].textContent = "Bu canlandırma yüklenemedi.";
        if (window.console) { console.error(tur, hata); }
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", kur);
  } else {
    kur();
  }
})();
