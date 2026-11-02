/* Kurs sitesi — küçük etkileşimler.
   Çerçeve yok, derleme yok: dosya doğrudan tarayıcıya gider.
   Yazı boyutu, yan gezinme ve kopyalama tümüyle tarayıcıda çalışır.
   Dışarıya giden tek istek, ziyaretçi KABUL EDERSE yüklenen ölçüm
   betiğidir; reddedilirse hiçbir istek gitmez.                   */
(function () {
  "use strict";

  /* ------------------------------------------------ ölçüm kimliği
     Google Analytics 4 ölçüm kimliği. Google Analytics hesabında
     bir "veri akışı" (data stream) oluşturup verilen G- ile başlayan
     kimliği buraya yazın, örneğin "G-XXXXXXXXXX".

     Boş bırakılırsa hiçbir ölçüm betiği yüklenmez; çerez kutusu yine
     görünür ve tercih saklanır, ama dışarıya istek gitmez.        */
  var OLCUM_KIMLIGI = "G-Q0PVMNQYT8";

  /* Tarayıcı deposu gizli pencerede ya da kısıtlı ayarlarda
     erişilemez olabilir; her okuma-yazma sarmalanır.             */
  var depo = {
    oku: function (anahtar, varsayilan) {
      try {
        var d = window.localStorage.getItem(anahtar);
        return d === null ? varsayilan : d;
      } catch (e) { return varsayilan; }
    },
    yaz: function (anahtar, deger) {
      try { window.localStorage.setItem(anahtar, deger); } catch (e) {}
    }
  };

  /* ===================================================== yazı boyutu
     Kök (html) yazı boyutunu değiştirir. Sayfadaki bütün ölçüler rem
     cinsinden olduğu için düzen birlikte büyür: metin yeniden akar,
     yatay kaydırma oluşmaz.                                        */
  var BASAMAKLAR = [85, 92, 100, 110, 122, 135, 150];
  var VARSAYILAN = 2;

  function boyutUygula(indeks) {
    indeks = Math.max(0, Math.min(BASAMAKLAR.length - 1, indeks));
    var yuzde = BASAMAKLAR[indeks];
    document.documentElement.style.fontSize = yuzde + "%";
    var gosterge = document.getElementById("olcek-gosterge");
    if (gosterge) { gosterge.textContent = "%" + yuzde; }
    document.querySelectorAll(".yazi-boyut button").forEach(function (d) {
      var yon = parseInt(d.getAttribute("data-boyut"), 10);
      if (yon === -1) { d.disabled = indeks === 0; }
      if (yon === 1) { d.disabled = indeks === BASAMAKLAR.length - 1; }
    });
    depo.yaz("kurs-yazi-boyutu", String(indeks));
    return indeks;
  }

  var boyutIndeks = parseInt(depo.oku("kurs-yazi-boyutu", VARSAYILAN), 10);
  if (isNaN(boyutIndeks)) { boyutIndeks = VARSAYILAN; }
  boyutIndeks = boyutUygula(boyutIndeks);

  document.querySelectorAll(".yazi-boyut button").forEach(function (dugme) {
    dugme.addEventListener("click", function () {
      var yon = parseInt(dugme.getAttribute("data-boyut"), 10);
      boyutIndeks = boyutUygula(yon === 0 ? VARSAYILAN : boyutIndeks + yon);
    });
  });

  /* Klavye: Ctrl/Cmd + artı, eksi, sıfır — tarayıcının kendi
     yakınlaştırmasıyla çakışmaması için yalnız Alt ile.           */
  document.addEventListener("keydown", function (o) {
    if (!o.altKey) { return; }
    if (o.key === "+" || o.key === "=") {
      boyutIndeks = boyutUygula(boyutIndeks + 1); o.preventDefault();
    } else if (o.key === "-") {
      boyutIndeks = boyutUygula(boyutIndeks - 1); o.preventDefault();
    } else if (o.key === "0") {
      boyutIndeks = boyutUygula(VARSAYILAN); o.preventDefault();
    }
  });

  /* ============================================================ tema
     Temayı asıl koyan betik <head> içinde, sayfanın en başında
     duruyor; buradaki iş yalnız düğmeyi yönetmek. İkisi aynı anahtarı
     ("kurs-tema") ve aynı özniteliği (<html data-tema>) kullanıyor.

     Seçim yapılmadıysa işletim sisteminin tercihine uyulur ve o
     tercih sonradan değişirse sayfa da değişir. Ziyaretçi düğmeye bir
     kez bastıktan sonra kendi seçimi geçerli olur; sistem artık
     karışmaz. */
  var TEMA_ANAHTAR = "kurs-tema";
  var temaDugme = document.getElementById("tema-dugme");
  var koyuSorgu = window.matchMedia
    ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function sistemTemasi() {
    return koyuSorgu && koyuSorgu.matches ? "koyu" : "acik";
  }

  function temaUygula(tema, sakla) {
    var koyu = tema === "koyu";
    if (koyu) {
      document.documentElement.setAttribute("data-tema", "koyu");
    } else {
      document.documentElement.removeAttribute("data-tema");
    }
    if (sakla) { depo.yaz(TEMA_ANAHTAR, tema); }
    if (temaDugme) {
      var hedef = koyu ? "Açık moda geç" : "Koyu moda geç";
      temaDugme.setAttribute("aria-pressed", koyu ? "true" : "false");
      temaDugme.setAttribute("aria-label", hedef);
      temaDugme.title = hedef;
      var simge = temaDugme.querySelector(".simge");
      var yazi = temaDugme.querySelector(".yazi");
      if (simge) { simge.textContent = koyu ? "☀" : "☾"; }
      if (yazi) { yazi.textContent = koyu ? "Açık" : "Koyu"; }
    }
  }

  var kayitliTema = depo.oku(TEMA_ANAHTAR, "");
  temaUygula(kayitliTema === "koyu" || kayitliTema === "acik"
    ? kayitliTema : sistemTemasi(), false);

  if (temaDugme) {
    temaDugme.addEventListener("click", function () {
      var koyu = document.documentElement.getAttribute("data-tema") === "koyu";
      temaUygula(koyu ? "acik" : "koyu", true);
    });
  }

  /* Ziyaretçi kendi seçimini yapmadıysa sistem tercihi izlenir. */
  if (koyuSorgu && koyuSorgu.addEventListener) {
    koyuSorgu.addEventListener("change", function () {
      var secim = depo.oku(TEMA_ANAHTAR, "");
      if (secim !== "koyu" && secim !== "acik") {
        temaUygula(sistemTemasi(), false);
      }
    });
  }

  /* ====================================================== tam ekran
     Tarayıcının F11'i zaten var; bu düğme dokunmatik ekranlar ve
     sunum sırasında klavyeye uzanmadan geçmek için. Esc ya da F11 ile
     çıkıldığında da etiket güncellensin diye olay dinleniyor —
     düğmenin durumu tarayıcıdan okunuyor, kendi belleğinden değil.

     Eski Safari sürümleri webkit önekini kullanır. Hiç desteklemeyen
     tarayıcılarda (iPhone'da Safari, öğe tam ekranını açmaz) düğme
     gösterilmez: çalışmayan bir düğme, olmayan bir düğmeden kötüdür. */
  var tamDugme = document.getElementById("tam-ekran-dugme");
  var kok = document.documentElement;
  var ac = kok.requestFullscreen || kok.webkitRequestFullscreen;
  var kapat = document.exitFullscreen || document.webkitExitFullscreen;

  function tamEkranda() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement);
  }

  if (tamDugme && ac && kapat) {
    var tamEtiketle = function () {
      var icinde = tamEkranda();
      var hedef = icinde ? "Tam ekrandan çık" : "Tam ekrana geç";
      tamDugme.setAttribute("aria-pressed", icinde ? "true" : "false");
      tamDugme.setAttribute("aria-label", hedef);
      tamDugme.title = icinde ? hedef + " (Esc)" : hedef + " (F11)";
      var simge = tamDugme.querySelector(".simge");
      var yazi = tamDugme.querySelector(".yazi");
      if (simge) { simge.textContent = icinde ? "⤡" : "⤢"; }
      if (yazi) { yazi.textContent = icinde ? "Çık" : "Tam ekran"; }
    };

    tamDugme.addEventListener("click", function () {
      /* requestFullscreen bir söz (promise) döndürür ve tarayıcı
         izin vermezse reddedilir; yakalanmazsa konsola hata düşer. */
      try {
        var sonuc = tamEkranda() ? kapat.call(document) : ac.call(kok);
        if (sonuc && sonuc.catch) { sonuc.catch(function () {}); }
      } catch (e) {}
    });

    document.addEventListener("fullscreenchange", tamEtiketle);
    document.addEventListener("webkitfullscreenchange", tamEtiketle);
    tamEtiketle();
  } else if (tamDugme) {
    tamDugme.hidden = true;
  }

  /* ============================================ açılır-kapanır kısımlar */
  document.querySelectorAll(".kisim-grup").forEach(function (grup) {
    var ad = grup.getAttribute("data-kisim");
    var dugme = grup.querySelector(".kisim-dugme");
    var etkinSayfaVar = grup.querySelector("a.etkin") !== null;

    /* Okurun bulunduğu kısım her zaman açık gelir. */
    if (!etkinSayfaVar && depo.oku("kurs-kisim-" + ad, "acik") === "kapali") {
      grup.setAttribute("data-kapali", "evet");
      dugme.setAttribute("aria-expanded", "false");
    }

    dugme.addEventListener("click", function () {
      var kapali = grup.getAttribute("data-kapali") === "evet";
      grup.setAttribute("data-kapali", kapali ? "hayir" : "evet");
      dugme.setAttribute("aria-expanded", kapali ? "true" : "false");
      depo.yaz("kurs-kisim-" + ad, kapali ? "acik" : "kapali");
    });
  });

  /* ================================================ istemleri kopyalama */
  document.querySelectorAll(".kopyala").forEach(function (dugme) {
    dugme.addEventListener("click", function () {
      var kutu = dugme.closest(".istem");
      var metin = kutu ? kutu.querySelector("pre").innerText : "";
      var bitir = function (oldu) {
        dugme.textContent = oldu ? "Kopyalandı ✓" : "Kopyalanamadı";
        dugme.classList.toggle("oldu", oldu);
        setTimeout(function () {
          dugme.textContent = "Kopyala";
          dugme.classList.remove("oldu");
        }, 1800);
      };
      /* navigator.clipboard yalnız güvenli bağlamda (https ya da
         localhost) çalışır; file:// ile açıldığında yedek yola
         düşülür.                                                  */
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(metin).then(
          function () { bitir(true); }, function () { bitir(false); });
      } else {
        var alan = document.createElement("textarea");
        alan.value = metin;
        alan.style.position = "fixed";
        alan.style.opacity = "0";
        document.body.appendChild(alan);
        alan.select();
        var oldu = false;
        try { oldu = document.execCommand("copy"); } catch (e) { oldu = false; }
        document.body.removeChild(alan);
        bitir(oldu);
      }
    });
  });

  /* ========================================================= yan menü
     Tek düğme, iki davranış:
       geniş ekran — menüyü tümden gizler/gösterir, tercih saklanır
       dar ekran   — menüyü üstte açılır çekmece olarak açar, saklanmaz
     Eşik CSS'teki kırılma noktasıyla aynıdır (64rem).              */
  var dugme = document.getElementById("yan-dugme");
  var ortu = document.getElementById("yan-kapat");
  var darEkran = window.matchMedia("(max-width: 64rem)");

  function dugmeyiGuncelle() {
    if (!dugme) { return; }
    var gizli = darEkran.matches
      ? !document.body.classList.contains("yan-acik")
      : document.body.classList.contains("yan-gizli");
    dugme.textContent = gizli ? "☰ Bölümler" : "✕ Bölümler";
    dugme.setAttribute("aria-expanded", gizli ? "false" : "true");
    dugme.setAttribute("aria-label",
      gizli ? "Bölüm listesini aç" : "Bölüm listesini kapat");
  }

  function menuDegistir() {
    if (darEkran.matches) {
      document.body.classList.toggle("yan-acik");
    } else {
      var gizlendi = document.body.classList.toggle("yan-gizli");
      depo.yaz("kurs-yan-menu", gizlendi ? "gizli" : "acik");
    }
    dugmeyiGuncelle();
  }

  /* Geniş ekranda son tercih geri yüklenir. */
  if (!darEkran.matches && depo.oku("kurs-yan-menu", "acik") === "gizli") {
    document.body.classList.add("yan-gizli");
  }
  dugmeyiGuncelle();

  if (dugme) { dugme.addEventListener("click", menuDegistir); }
  if (ortu) {
    ortu.addEventListener("click", function () {
      document.body.classList.remove("yan-acik");
      dugmeyiGuncelle();
    });
  }
  document.addEventListener("keydown", function (o) {
    if (o.key === "Escape" && document.body.classList.contains("yan-acik")) {
      document.body.classList.remove("yan-acik");
      dugmeyiGuncelle();
    }
  });
  /* Ekran boyutu değişince düğmenin anlattığı şey de değişir. */
  if (darEkran.addEventListener) {
    darEkran.addEventListener("change", function () {
      document.body.classList.remove("yan-acik");
      if (darEkran.matches) {
        document.body.classList.remove("yan-gizli");
      } else if (depo.oku("kurs-yan-menu", "acik") === "gizli") {
        document.body.classList.add("yan-gizli");
      }
      dugmeyiGuncelle();
    });
  }
  /* Dar ekranda bir bağlantıya tıklanınca çekmece kapansın. */
  document.querySelectorAll(".yan a").forEach(function (bag) {
    bag.addEventListener("click", function () {
      if (darEkran.matches) {
        document.body.classList.remove("yan-acik");
        dugmeyiGuncelle();
      }
    });
  });

  /* ========================================= okunan bölümü işaretleme
     Kendi kapsamında: içindeki erken çıkış yalnız bu özelliği atlar.
     Dış kapsamda duruyordu ve kapak gibi alt listesi olmayan
     sayfalarda ardından gelen her şeyi de atlıyordu.              */
  (function () {
    var altBaglar = Array.prototype.slice.call(
      document.querySelectorAll(".alt-liste a"));
    if (!altBaglar.length || !("IntersectionObserver" in window)) { return; }
    var harita = {};
    altBaglar.forEach(function (b) {
      harita[b.getAttribute("href").slice(1)] = b;
    });
    var gozlemci = new IntersectionObserver(function (girisler) {
      girisler.forEach(function (g) {
        var bag = harita[g.target.id];
        if (bag && g.isIntersecting) {
          altBaglar.forEach(function (b) { b.style.fontWeight = ""; });
          bag.style.fontWeight = "700";
        }
      });
    }, { rootMargin: "0px 0px -72% 0px" });
    document.querySelectorAll("h2[id]").forEach(function (b) {
      gozlemci.observe(b);
    });
  }());

  /* --------------------------------------------------- çerez onayı
     Tercih saklanana kadar kutu görünür. Ölçüm betiği YALNIZ kabul
     sonrası eklenir; bu, "önce yükle sonra sor" yaklaşımının tersi
     ve KVKK ile GDPR'ın beklediği sıra.                           */
  var kutu = document.getElementById("cerez-kutu");
  if (kutu) {
    var ANAHTAR = "cerez-onay";

    function olcumuBaslat() {
      if (!OLCUM_KIMLIGI) { return; }
      // İki kez yüklenmesin: sayfa içi gezinmede tekrar çağrılabilir.
      if (document.getElementById("ga-betik")) { return; }
      var e = document.createElement("script");
      e.id = "ga-betik";
      e.async = true;
      e.src = "https://www.googletagmanager.com/gtag/js?id=" +
              encodeURIComponent(OLCUM_KIMLIGI);
      document.head.appendChild(e);
      window.dataLayer = window.dataLayer || [];
      function gtag() { window.dataLayer.push(arguments); }
      window.gtag = gtag;
      gtag("js", new Date());
      // IP'nin son baytı Google tarafında atılır; ziyaretçi sayımı
      // için konum duyarlılığına gerek yok.
      gtag("config", OLCUM_KIMLIGI, { anonymize_ip: true });
    }

    var secim = depo.oku(ANAHTAR, "");
    if (secim === "kabul") {
      olcumuBaslat();
    } else if (secim !== "ret") {
      kutu.classList.add("acik");
    }

    var kabulDugme = document.getElementById("cerez-kabul");
    var retDugme = document.getElementById("cerez-ret");
    if (kabulDugme) {
      kabulDugme.addEventListener("click", function () {
        depo.yaz(ANAHTAR, "kabul");
        kutu.classList.remove("acik");
        olcumuBaslat();
      });
    }
    if (retDugme) {
      retDugme.addEventListener("click", function () {
        depo.yaz(ANAHTAR, "ret");
        kutu.classList.remove("acik");
      });
    }
  }
}());
