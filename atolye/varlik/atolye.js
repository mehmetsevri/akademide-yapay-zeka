/* Atölye sunumu — gezinme.
   Çerçeve yok. Slaytlar DOM'da duruyor, biri görünür kılınıyor.
   Dışarıya hiçbir istek gitmez.                                   */
(function () {
  "use strict";

  var slaytlar = Array.prototype.slice.call(
    document.querySelectorAll("#sunum .slayt"));
  if (!slaytlar.length) { return; }

  var simdi = 0;
  var govde = document.body;
  var ilerleme = document.getElementById("ilerleme");
  var sayacEl = document.getElementById("simdiki");
  var bolumEl = document.getElementById("bolumAd");
  var onceki = document.getElementById("onceki");
  var sonraki = document.getElementById("sonraki");
  var gb = document.getElementById("genelBakis");
  var gbIzgara = document.getElementById("gbIzgara");
  var yardim = document.getElementById("yardim");

  /* Adres çubuğundaki #12 doğrudan o slayta gider; sunum sırasında
     bir slayta bağlantı vermeyi ve yenilemede yeri korumayı sağlar. */
  function adrestenOku() {
    var n = parseInt((location.hash || "").replace("#", ""), 10);
    return (isFinite(n) && n >= 1 && n <= slaytlar.length) ? n - 1 : 0;
  }

  function goster(i, adresiGuncelle) {
    i = Math.max(0, Math.min(slaytlar.length - 1, i));
    slaytlar[simdi].classList.remove("etkin");
    slaytlar[i].classList.add("etkin");
    simdi = i;

    var tur = slaytlar[i].getAttribute("data-tur");
    govde.classList.toggle("koyu", tur === "kapak" || tur === "bolum");

    ilerleme.style.width = ((i + 1) / slaytlar.length * 100) + "%";
    sayacEl.textContent = i + 1;
    bolumEl.textContent = slaytlar[i].getAttribute("data-bolum") || "";
    onceki.disabled = i === 0;
    sonraki.disabled = i === slaytlar.length - 1;

    if (adresiGuncelle !== false) {
      history.replaceState(null, "", "#" + (i + 1));
    }
    // Uzun slaytlarda dar ekranda kaydırma başa alınır
    var ic = slaytlar[i].querySelector(".ic");
    if (ic) { ic.scrollTop = 0; }
    sigdir(slaytlar[i]);
  }

  /* İstem ve çıktı kutularını kalan alana sığdırır.

     Sunumda kaydırmak kötüdür: dinleyici metnin devamı olduğunu
     bilmez. İki aşama var. Önce yazı okunur bir tabana kadar
     küçültülür. Oraya rağmen sığmıyorsa kutu iki sütuna geçer —
     uzun istemde yazıyı 9 piksele indirmek yerine yana yaymak
     perdede çok daha okunur kalıyor.

     Ölçüm yalnız görünür slaytta yapılır; gizli öğelerin yüksekliği
     okunamaz. */
  var TABAN_TEK = 14;   // tek sütunda inilecek en küçük boy (px)
  var TABAN_CIFT = 11;  // iki sütuna geçildikten sonraki taban
  var TAVAN_CIFT = 19;  // iki sütunda çıkılacak en büyük boy
  var TABAN_CIKTI = 11; // çıktı kutusu: sütuna geçmez, yalnız küçülür

  function kucult(kutu, taban, tasiyor) {
    var boy = parseFloat(getComputedStyle(kutu).fontSize);
    var guvenlik = 0;
    /* boy - .5 >= taban: eşiğin altına düşmeyi engeller. Önceki
       sürüm "boy > taban" diye bakıyordu ve tabanın yarım piksel
       altında durabiliyordu. */
    while (tasiyor() && boy - 0.5 >= taban && guvenlik < 60) {
      boy -= 0.5;
      kutu.style.fontSize = boy + "px";
      guvenlik++;
    }
  }

  function sigdir(slayt) {
    var kutu = slayt.querySelector("pre.istem, pre.cikti");
    if (!kutu) { return; }
    kutu.classList.remove("iki-sutun");
    kutu.style.fontSize = "";
    /* Dar ekranda küçültme yapılmaz: telefonda yazıyı sığdırmak
       okunmaz hâle getirir ve orada kaydırmak zaten doğal. */
    if (window.innerWidth < 768) { return; }

    /* İki sütunda taşma yana doğru olur, bu yüzden iki eksen de
       ölçülüyor. */
    function tasiyor() {
      return kutu.scrollHeight > kutu.clientHeight + 2 ||
             kutu.scrollWidth > kutu.clientWidth + 2;
    }
    if (!tasiyor()) { return; }

    /* İki sütun yalnız istem kutusuna uygulanır. Çıktı kutusu
       programın kendi çıktısıdır: hizalı sütunlar, ayraç çizgileri,
       girintiler taşır. Dar sütunda bunlar sarınca tablo kırılıyor.
       Çıktıda yalnız küçültme yapılır. */
    var sutunaGecebilir = kutu.classList.contains("istem");
    kucult(kutu, sutunaGecebilir ? TABAN_TEK : TABAN_CIKTI, tasiyor);
    if (!tasiyor() || !sutunaGecebilir) { return; }

    kutu.style.fontSize = "";
    kutu.classList.add("iki-sutun");
    if (tasiyor()) { kucult(kutu, TABAN_CIFT, tasiyor); return; }
    /* İki sütuna geçince genelde bol yer kalıyor. Kalan boşluk
       yazıyı büyütmekte kullanılır — perdede her yarım piksel
       okunurluğa yarıyor. */
    buyut(kutu, TAVAN_CIFT, tasiyor);
  }

  function buyut(kutu, tavan, tasiyor) {
    var boy = parseFloat(getComputedStyle(kutu).fontSize);
    var guvenlik = 0;
    while (boy + 0.5 <= tavan && guvenlik < 40) {
      kutu.style.fontSize = (boy + 0.5) + "px";
      if (tasiyor()) { kutu.style.fontSize = boy + "px"; return; }
      boy += 0.5;
      guvenlik++;
    }
  }

  window.addEventListener("resize", function () {
    sigdir(slaytlar[simdi]);
  });

  function git(adim) { goster(simdi + adim); }

  /* ------------------------------------------------- bölüm başına dön */
  function bolumBasi() {
    for (var i = simdi; i >= 0; i--) {
      if (slaytlar[i].getAttribute("data-tur") === "bolum") {
        goster(i === simdi ? Math.max(0, i - 1) : i);
        return;
      }
    }
    goster(0);
  }

  /* ----------------------------------------------------- genel bakış */
  function gbKur() {
    if (gbIzgara.childElementCount) { return; }
    slaytlar.forEach(function (s, i) {
      var d = document.createElement("button");
      d.type = "button";
      d.className = "gb-oge";
      d.setAttribute("data-tur", s.getAttribute("data-tur") || "metin");
      var b = s.querySelector("h1, h2");
      d.innerHTML = '<span class="gb-no">' + (i + 1) + "</span><b></b>";
      d.querySelector("b").textContent =
        s.getAttribute("data-kisa") || (b ? b.textContent : "—");
      d.addEventListener("click", function () {
        gbKapat();
        goster(i);
      });
      gbIzgara.appendChild(d);
    });
  }

  function gbAc() {
    gbKur();
    Array.prototype.forEach.call(gbIzgara.children, function (c, i) {
      c.classList.toggle("etkin", i === simdi);
    });
    gb.hidden = false;
    var etkin = gbIzgara.children[simdi];
    if (etkin) { etkin.scrollIntoView({ block: "center" }); }
  }
  function gbKapat() { gb.hidden = true; }

  /* ---------------------------------------------------------- olaylar */
  onceki.addEventListener("click", function () { git(-1); });
  sonraki.addEventListener("click", function () { git(1); });
  document.getElementById("gbKapat").addEventListener("click", gbKapat);
  document.getElementById("genelBakisDugme").addEventListener("click", gbAc);
  document.getElementById("yardimKapat").addEventListener("click", function () {
    yardim.hidden = true;
  });

  document.getElementById("tamEkranDugme").addEventListener("click", function () {
    if (document.fullscreenElement) { document.exitFullscreen(); }
    else if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen();
    }
  });

  document.addEventListener("keydown", function (o) {
    if (o.metaKey || o.ctrlKey || o.altKey) { return; }
    var k = o.key;
    if (!gb.hidden) {
      if (k === "Escape") { gbKapat(); o.preventDefault(); }
      return;
    }
    if (!yardim.hidden) {
      if (k === "Escape" || k === "?") { yardim.hidden = true; o.preventDefault(); }
      return;
    }
    if (k === "ArrowRight" || k === " " || k === "PageDown") {
      git(1); o.preventDefault();
    } else if (k === "ArrowLeft" || k === "PageUp") {
      git(-1); o.preventDefault();
    } else if (k === "Home") { goster(0); o.preventDefault(); }
    else if (k === "End") { goster(slaytlar.length - 1); o.preventDefault(); }
    else if (k === "o" || k === "O") { gbAc(); o.preventDefault(); }
    else if (k === "s" || k === "S") { bolumBasi(); o.preventDefault(); }
    else if (k === "?") { yardim.hidden = false; o.preventDefault(); }
    else if (k === "f" || k === "F") {
      document.getElementById("tamEkranDugme").click(); o.preventDefault();
    }
  });

  /* Dokunmatik: yatay kaydırma slayt değiştirir. Dikey kaydırma,
     dar ekranda içerik taşarsa gerekli olduğu için serbest bırakılır. */
  var bx = 0, by = 0;
  document.addEventListener("touchstart", function (o) {
    bx = o.changedTouches[0].clientX;
    by = o.changedTouches[0].clientY;
  }, { passive: true });
  document.addEventListener("touchend", function (o) {
    var dx = o.changedTouches[0].clientX - bx;
    var dy = o.changedTouches[0].clientY - by;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.6) {
      git(dx < 0 ? 1 : -1);
    }
  }, { passive: true });

  window.addEventListener("hashchange", function () {
    var i = adrestenOku();
    if (i !== simdi) { goster(i, false); }
  });

  slaytlar[0].classList.add("etkin");
  goster(adrestenOku());
}());
