# -*- coding: utf-8 -*-
"""
25 — Sosyoloji örneği: etnografik korpus üretimi

!!! BU KORPUS SENTETİKTİR. !!!
Gerçek bir sahadan, gerçek insanlardan gelmemiştir. "Yıldıztepe
Mahallesi" kurgusal bir yerdir; İstanbul'daki hiçbir mahalleyi
betimlemez ve buradaki hiçbir ifade gerçek bir sakinin sözü değildir.
Hiçbir cümle bulgu olarak alıntılanamaz.

Neden sentetik: nitel veri, tanımı gereği kişiseldir. Gerçek mülakat
dökümleri etik kurul izni, katılımcı onamı ve kimliksizleştirme
gerektirir; kamuya açık, Türkçe, tam metin bir etnografik korpus
bulunmaz. Oysa tematik analiz öğretmek için ÜZERİNDE ÇALIŞILACAK bir
metin gerekir.

Sentetik olmanın bir üstünlüğü daha var: her konuşma parçasının hangi
koddan üretildiği BİLİNİR. Gerçek sahada "doğru kod" diye bir şey
yoktur, kodlayıcıların uzlaşması vardır. Burada bir referans kodlama
olduğu için, yapay zekâ destekli kodlamanın ne kadarını bulduğu
ölçülebilir (bkz. 26_tematik_analiz_kentsel.py, Adım 7).

SAHA KURGUSU
  Yıldıztepe, 1970'lerde gecekondu olarak kurulmuş, 2000'lerde
  apartmanlaşmış, 2019–2024 arasında kentsel dönüşüme girmiş bir
  mahalle. Eski doku yıkıldı, yerine üç etaplı bir site yapıldı.
  Araştırma 14 ay sürdü (Eylül 2025 – Ekim 2026).

ÖRNEKLEM — kartopu (snowball) örnekleme
  A  Eski sakin, yerinde kalan            12 kişi
  B  Eski sakin, mahalleden ayrılan        8 kişi
  C  Mahalle esnafı                        7 kişi
  D  Yeni site sakini                      7 kişi
  E  Kilit aktör (muhtar, dernek, okul)    4 kişi
                                    toplam 38 derinlemesine mülakat
  + 6 odak grup görüşmesi (6–8 kişi)
  + 44 katılımcı gözlem alan notu
  + 19 arşiv kaydı (gazete kupürü, dilekçe, fotoğraf künyesi)

ÇIKTI
  kentsel_katilimcilar.csv     katılımcı künyeleri ve kartopu zinciri
  kentsel_mulakatlar.csv       kodlama birimi: her satır bir konuşma parçası
  kentsel_mulakatlar.txt       insan okuması için tam dökümler
  kentsel_odak_gruplar.csv     odak grup konuşma parçaları
  kentsel_odak_gruplar.txt     odak grup dökümleri
  kentsel_saha_notlari.csv     alan notları
  kentsel_arsiv.csv            arşiv ve görsel veri künyeleri
  kentsel_referans_kodlar.csv  her parçanın üretildiği kod (referans)
  kentsel_mulakat_formu.txt    yarı yapılandırılmış mülakat formu

Kullanım:
  python 25_kentsel_korpus_uret.py <çıktı_klasörü>
"""
import pathlib
import sys

import numpy as np
import pandas as pd

TOHUM = 20261105
rng = np.random.default_rng(TOHUM)

MAHALLE = "Yıldıztepe"

# ====================================================== KOD KİTABI (referans)
# (kod, tema, kısa tanım)
KODLAR = [
    # --- T1 Mekânsal yabancılaşma ve güvensizlik ------------------------
    ("T1-K1", "Mekânsal yabancılaşma ve güvensizlik",
     "Kapıyı kilitleme alışkanlığının değişmesi"),
    ("T1-K2", "Mekânsal yabancılaşma ve güvensizlik",
     "Güvenlik görevlisi, kartlı geçiş, kamera"),
    ("T1-K3", "Mekânsal yabancılaşma ve güvensizlik",
     "Tanımadık yüzler, yabancılık hissi"),
    ("T1-K4", "Mekânsal yabancılaşma ve güvensizlik",
     "Yapı ölçeği: yükseklik, gölge, rüzgâr"),
    ("T1-K5", "Mekânsal yabancılaşma ve güvensizlik",
     "Sokağın yerini koridorun alması"),
    # --- T2 Komşuluk ağlarının çözülmesi --------------------------------
    ("T2-K1", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Komşunun adını bilmemek"),
    ("T2-K2", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Kapı önü ve merdiven sohbetinin bitmesi"),
    ("T2-K3", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Karşılıklı yardımlaşmanın (çocuk, yemek, borç) sona ermesi"),
    ("T2-K4", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Asansör ve ortak alanlarda sessizlik"),
    ("T2-K5", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Yeni gelenlerle 'biz / onlar' ayrımı"),
    ("T2-K6", "Komşuluk ağlarının çözülmesi ve atomize yaşam",
     "Komşuluğun site yönetim grubuna taşınması"),
    # --- T3 Hafıza ve aidiyet -------------------------------------------
    ("T3-K1", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "Yıkılan yer imleri: çeşme, ağaç, dükkân"),
    ("T3-K2", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "Sokak ve blok adlarının değişmesi"),
    ("T3-K3", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "Fotoğraf ve eşya üzerinden hatırlama"),
    ("T3-K4", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "'Burası artık benim mahallem değil' ifadesi"),
    ("T3-K5", "Eski hafızanın silinmesi ve mekânsal aidiyet kaybı",
     "Camiye, okula, mezarlığa tutunma"),
    # --- T4 Ekonomik baskı ----------------------------------------------
    ("T4-K1", "Ekonomik baskı ve yerinden edilme",
     "Aidat ve işletme giderlerinin yükü"),
    ("T4-K2", "Ekonomik baskı ve yerinden edilme",
     "Kira artışı ve mahalleden ayrılma"),
    ("T4-K3", "Ekonomik baskı ve yerinden edilme",
     "Müteahhitle pazarlık, hak sahipliği süreci"),
    ("T4-K4", "Ekonomik baskı ve yerinden edilme",
     "Esnafın müşteri kaybı ve kapanma"),
    ("T4-K5", "Ekonomik baskı ve yerinden edilme",
     "Konutun değerlenmesi (olumlu okuma)"),
    # --- T5 Ayrışma ve kazananlar (aykırı örnek) ------------------------
    ("T5-K1", "Kuşaklar arası ayrışma ve konforun kazananları",
     "Genç kuşakta konfor memnuniyeti: ısınma, otopark, asansör"),
    ("T5-K2", "Kuşaklar arası ayrışma ve konforun kazananları",
     "Yaşlıların yeni düzene uyum güçlüğü"),
    ("T5-K3", "Kuşaklar arası ayrışma ve konforun kazananları",
     "Kadınlarda güvenlik algısının iyileşmesi"),
    ("T5-K4", "Kuşaklar arası ayrışma ve konforun kazananları",
     "Çocuklu ailelerde oyun alanı memnuniyeti"),
]
KOD_TEMA = {k: t for k, t, _ in KODLAR}

# =========================================================== SÖZ BANKASI
# Her kod için (konuşmacı tipi, evre, ifade) üçlüleri.
#   tip  : A yerinde kalan · B ayrılan · C esnaf · D yeni sakin · E kilit aktör
#   evre : "öncesi" dönüşüm öncesini anlatan geçmiş zamanlı ifade
#          "inşaat" yıkım ve inşaat dönemi
#          "sonrası" bugünü anlatan ifade
# Evre etiketi zorunludur: geçmişi soran bir soruya bugünü anlatan bir
# yanıt düşerse döküm inandırıcılığını kaybeder ve kodlama alıştırması
# anlamsızlaşır.
SOZLER = {
"T1-K1": [
 ("A", "öncesi", "Kapıyı kilitlemezdik. Çıkarken üstüne iterdik, o kadar. "
  "Komşu zaten evde kim var kim yok bilirdi."),
 ("A", "öncesi", "Anahtarı kapının yanındaki saksının altına koyardık. "
  "Bilen bilirdi, bilmeyene de zaten lazım olmazdı."),
 ("C", "öncesi", "Dükkânı öğle namazına giderken açık bırakırdım. "
  "Kimse bir şey almazdı, alsa da gören olurdu."),
 ("B", "öncesi", "Otuz yıl o evde oturdum, kilidi kaç kez çevirdiğimi "
  "sayabilirim. Gece bile açık kalırdı bazen."),
 ("A", "sonrası", "Şimdi iki kilit var, biri de şu akıllı olanlardan. "
  "Çıkarken ikisini de çeviriyorum."),
 ("A", "sonrası", "Kilit meselesi aslında şu: eskiden kapının arkasında "
  "kim olduğunu bilirdin. Şimdi bilmiyorsun, o yüzden kilitliyorsun."),
 ("B", "sonrası", "Yeni oturduğum yerde kapıyı kapatır kapatmaz kilidi "
  "çeviriyorum. Yıldıztepe\'de böyle bir şey yapmazdım."),
 ("C", "sonrası", "Artık kepenk indiriyorum. Beş dakikalığına bile "
  "çıksam indiriyorum, alışkanlık oldu."),
 ("D", "sonrası", "Ben baştan beri kilitliyorum, İstanbul\'da büyüdüm. "
  "Ama komşuların eskiden kilitlemediğini duyunca şaşırdım."),
 ("A", "sonrası", "Torunuma anlattım, güldü bana. Ona masal gibi "
  "geliyor herhâlde."),
],
"T1-K2": [
 ("A", "sonrası", "Girişte güvenlik var, kart okutuyorsun. Kendi evime "
  "girerken kart okutmak ilk aylar çok tuhaf geldi."),
 ("A", "sonrası", "Kamerayı koydular, iyi oldu diyorlar. Bana sorarsan "
  "kamera koyuyorsan orada bir sorun var demektir."),
 ("A", "sonrası", "Misafirim geldiğinde aşağıdan arıyorlar, onay "
  "veriyorum. Kardeşim için onay veriyorum yani."),
 ("B", "sonrası", "Siteye gelip çocuğumu görmek istediğimde güvenlikten "
  "izin almam gerekiyor. Doğduğum sokakta misafir oldum."),
 ("D", "sonrası", "Güvenlik benim için önemliydi, açıkçası onun için "
  "bu siteyi seçtim. Akşam geç geliyorum."),
 ("D", "sonrası", "Kargom güvenliğe bırakılıyor, kaybolmuyor. "
  "Küçük şey gibi ama günlük hayatta işe yarıyor."),
 ("E", "sonrası", "En çok şu şikâyeti alıyoruz: ziyaretçi kaydı. "
  "Akrabası gelen insan kendini sorgulanıyor gibi hissediyor."),
 ("C", "sonrası", "Eskiden müşteri sokaktan girerdi. Şimdi siteye "
  "giremiyor, ben de siteye mal çıkaramıyorum."),
 ("A", "inşaat", "İnşaat döneminde şantiye kapısında bekçi vardı. "
  "Kendi arsama bakmaya giderken izin istiyordum."),
],
"T1-K3": [
 ("A", "sonrası", "Sabah asansörde üç kişiyle karşılaşıyorum, "
  "üçünü de tanımıyorum."),
 ("A", "sonrası", "Mahallede yürürken selam vereceğim biri çıkmıyor. "
  "İnsan selam vermeye alışmış, zor bırakıyor."),
 ("A", "öncesi", "Sokağın iki ucundaki herkesi bilirdim. Kimin oğlu "
  "askere gitmiş, kimin kızı nişanlanmış, hepsi."),
 ("B", "sonrası", "Taşındıktan sonra bir kere geldim. Kimseyi "
  "tanıyamadım, beni de tanıyan olmadı. Bir daha gelmedim."),
 ("C", "sonrası", "Müşterilerin yarısı yabancı artık. Veresiye defteri "
  "tutamıyorum, çünkü adamı tanımıyorum."),
 ("D", "sonrası", "Ben de yabancıyım aslında. İki yıl önce geldim, "
  "hâlâ kimseyi tanımıyorum ama bu beni rahatsız etmiyor."),
 ("E", "sonrası", "Mahalle sakini listesinin yüzde altmışı yeni. "
  "Eski muhtarlık defterindeki adların çoğu artık burada değil."),
 ("A", "sonrası", "Markette kasiyer bile her hafta değişiyor. "
  "Tanıdık bir yüz görmek zor oldu."),
],
"T1-K4": [
 ("A", "sonrası", "On altı kat. Balkona çıkıyorum, aşağısı görünmüyor."),
 ("A", "öncesi", "Bahçedeki inciri pencereden uzanıp toplardım. "
  "İki kat vardı, o kadar."),
 ("A", "sonrası", "Bloklar arasında bir rüzgâr oluyor, kışın "
  "geçilmiyor. Mimar bunu düşünmemiş herhâlde."),
 ("B", "inşaat", "O binalar yükselince bizim sokağa güneş girmedi. "
  "Taşınma kararımda bunun da payı var."),
 ("D", "sonrası", "Yükseklik beni rahatsız etmiyor, manzara güzel. "
  "Ama rüzgâr konusunda haklılar, girişte durulmuyor."),
 ("C", "sonrası", "Dükkânın önü gölgede kaldı. Yazın serin diye "
  "seviniyordum, kışın müşteri durmuyor."),
 ("A", "inşaat", "Kazık çakarken bardaklar titriyordu. İki yıl "
  "o sesle yaşadık."),
],
"T1-K5": [
 ("A", "sonrası", "Sokak diye bir şey kalmadı. Koridor var, asansör "
  "var, otopark var. Sokak yok."),
 ("A", "öncesi", "Akşamüstü herkes kapının önüne sandalyesini atardı. "
  "Yaz boyunca o kaldırım bizim oturma odamızdı."),
 ("A", "sonrası", "Şimdi kapının önü diye bir yer yok ki. "
  "Kapıyı açıyorsun, karşında başka bir kapı."),
 ("B", "öncesi", "Çocuklar sokakta oynardı, biz pencereden bakardık. "
  "Bir ses kesilse hemen kafanı uzatırdın."),
 ("E", "sonrası", "Mimari olarak kamusal alan sıfırlandı. Ortak alan "
  "var ama o alan bütün mahalleye değil, siteye ait."),
 ("D", "sonrası", "Ortak alanlar güzel düzenlenmiş, ben memnunum. "
  "Ama kimse kullanmıyor, boş duruyor çoğu zaman."),
],
"T2-K1": [
 ("A", "sonrası", "Alt komşumun adını bilmiyorum. Bir buçuk yıldır "
  "altımda oturuyor."),
 ("A", "öncesi", "Kim kiminle evli, kimin kaç çocuğu var, hepsini "
  "bilirdik. Yanlış numaradan telefon gelse tarif ederdik."),
 ("B", "sonrası", "Yeni binada kimse kimseyi tanımıyor. Orası yabancı "
  "yer zaten; asıl acı olan Yıldıztepe\'de de böyle olması."),
 ("D", "sonrası", "Yan komşumla iki yılda belki üç kez konuştuk. "
  "İkimiz de çalışıyoruz, denk gelmiyoruz."),
 ("C", "sonrası", "Ben esnafım, herkesi tanırım derdim. "
  "Artık diyemiyorum."),
 ("E", "sonrası", "Taziye listesi tutuyoruz. Eskiden bir ölüm olsa "
  "bütün mahalle bilirdi; şimdi apartmandan haberi olmuyor."),
 ("A", "sonrası", "Kapıdaki isimliklerden öğreniyorum komşuların "
  "soyadını. Konuşarak değil."),
],
"T2-K2": [
 ("A", "öncesi", "Kapı önünde çay içerdik. Komşu geçer, oturur, "
  "yarım saat laflardık."),
 ("A", "sonrası", "O yarım saatler bitti. Şimdi kimse kimseye "
  "takılmıyor, herkes kapısına giriyor."),
 ("A", "öncesi", "Merdivende karşılaşınca iki çift laf ederdin. "
  "Bazen çıkamazdın, kırk dakika merdivende geçerdi."),
 ("A", "sonrası", "Asansörde laf etmiyorsun, çünkü on beş saniye "
  "sürüyor. İnsan bir cümleye başlayamıyor."),
 ("B", "öncesi", "Yaz akşamları kaldırıma masa atılırdı. "
  "Bunu anlatınca torunum inanmıyor."),
 ("C", "öncesi", "Dükkânın önündeki tabure en iyi reklamımdı. "
  "İnsanlar oturur, konuşur, çıkarken bir şey alırdı."),
 ("C", "sonrası", "Tabure kalktı, oturacak yer kalmadı. "
  "Müşteri alıp gidiyor, iki kelime etmiyoruz."),
 ("D", "sonrası", "Bizim blokta kapı önünde oturmak yasak, yönetim "
  "uyarı astı. Mantıklı aslında ama biraz da üzücü."),
],
"T2-K3": [
 ("A", "öncesi", "Çocuğumu komşuya bırakıp işe giderdim. "
  "Parası pulu olmazdı, sırası gelince ben bakardım."),
 ("A", "sonrası", "Şimdi kime bırakacağım? Kreşe veriyorum, "
  "maaşımın üçte biri oraya gidiyor."),
 ("A", "öncesi", "Bir tencere yemek pişirirdin, iki kapıya "
  "götürürdün. Kapıdan tabak eksik olmazdı."),
 ("A", "sonrası", "Şimdi götürsen kapıyı açan şaşırır. "
  "Denedim bir kere, bir daha denemedim."),
 ("B", "sonrası", "Geçen yıl ameliyat oldum, kimse gelmedi. "
  "Kimseyi suçlamıyorum, öyle bir düzen kalmadı."),
 ("C", "öncesi", "Veresiye defteri vardı, ay sonu kapatırlardı. "
  "Defter güvene dayanıyordu."),
 ("C", "sonrası", "Defteri kaldırdım. Güven gidince defter de gitti."),
 ("E", "sonrası", "Yardım ağını ayakta tutmaya çalışıyoruz ama "
  "eskiden kendiliğinden olan şeyi şimdi örgütlemek gerekiyor."),
 ("A", "öncesi", "Anahtarımı komşuya bırakırdım, kargo gelirse alsın "
  "diye. Şimdi kargoyu güvenliğe bırakıyorlar."),
],
"T2-K4": [
 ("A", "sonrası", "Asansöre biniyorsun, iki kişi, kimse konuşmuyor. "
  "Herkes telefonuna bakıyor."),
 ("D", "sonrası", "Asansörde günaydın diyorum, karşılık veriyorlar. "
  "Sonrası gelmiyor, orada kalıyor."),
 ("A", "sonrası", "Ortak alanda bir masa var, hiç kimsenin oturduğunu "
  "görmedim. Masayı koymak yetmiyor demek ki."),
 ("B", "sonrası", "Yeni yerde de aynı. Demek ki mesele Yıldıztepe "
  "değil, bu yeni apartman biçimi."),
 ("D", "sonrası", "Lobide iki koltuk var. İki yılda bir kez "
  "birinin oturduğunu gördüm, o da kargo bekliyordu."),
],
"T2-K5": [
 ("A", "sonrası", "Yeni gelenler kötü insanlar değil, yanlış "
  "anlaşılmasın. Ama onların hayatı başka, bizimki başka."),
 ("A", "sonrası", "Aidatı tartışırken ikiye ayrıldık: hak sahipleri "
  "ve sonradan alanlar. Toplantıda iki ayrı tarafa oturuyoruz."),
 ("C", "sonrası", "Yeni gelenler zincir marketten alışveriş yapıyor. "
  "Kızmıyorum ama bir ayrışma var, görünüyor."),
 ("D", "sonrası", "Bize biraz mesafeli yaklaşıyorlar. Anlıyorum da, "
  "biz onların mahallesine geldik sonuçta."),
 ("E", "sonrası", "İki grup arasında açık bir husumet yok. Olan şey "
  "daha sessiz: aynı binada iki ayrı hayat sürüyor."),
 ("B", "sonrası", "Biz gidince yerimize kimler geldi görmedim. "
  "Gelenler de bizi bilmiyor."),
 ("A", "sonrası", "Site grubunda bir tartışma çıksa taraflar belli "
  "oluyor. Kimse söylemiyor ama herkes biliyor."),
],
"T2-K6": [
 ("A", "sonrası", "Bir WhatsApp grubu var, üç yüz kişi. Günde elli "
  "mesaj akıyor, hiçbiri komşuluk değil."),
 ("D", "sonrası", "Grup işe yarıyor aslında. Geçen ay merdivendeki "
  "lamba iki saatte halledildi."),
 ("A", "sonrası", "Grupta herkes var ama yüz yüze gelince kimse "
  "kimseyi tanımıyor. Tuhaf bir şey bu."),
 ("E", "sonrası", "Yönetim iletişimi gruba taşıdı. Telefonu olmayan "
  "yaşlılar haberleri en son duyuyor."),
 ("A", "sonrası", "Gruptan çıktım. Sürekli tartışma oluyordu, "
  "komşuluk gibi gelmiyordu bana."),
 ("D", "sonrası", "Komşumun sesini duymadım ama yazısını "
  "her gün okuyorum. Garip bir komşuluk."),
],
"T3-K1": [
 ("A", "öncesi", "Köşede bir çeşme vardı, üstünde 1974 yazardı. "
  "Yazın oradan su içerdik."),
 ("A", "inşaat", "Çeşmeyi yıkarken kimse sormadı. Bir sabah "
  "geldik, yerinde değildi."),
 ("A", "sonrası", "Çeşmenin yerinde şimdi trafo var. "
  "Oradan her geçişimde bakıyorum."),
 ("A", "inşaat", "Okulun bahçesindeki çınarı kestiler. "
  "O ağacın altında nişanlanmıştım ben."),
 ("B", "sonrası", "Bakkal Nuri\'nin dükkânı duruyor mu diye sordum, "
  "yerinde kuaför varmış. Nuri amca da vefat etmiş."),
 ("C", "sonrası", "Dükkânım kırk iki yıllıktı. Levhayı söktüler, "
  "eve götürdüm, duvarda asılı duruyor."),
 ("E", "sonrası", "Mahalle hafızası somut nesnelere bağlıydı: "
  "çeşme, fırın, kahve. Üçü de yok."),
 ("A", "öncesi", "Fırının kokusu sabah altıda bütün sokağa yayılırdı. "
  "Saate bakmana gerek kalmazdı."),
],
"T3-K2": [
 ("A", "sonrası", "Sokağımızın adı Gülbahar\'dı, şimdi B Blok diyoruz. "
  "Adres tarif ederken zorlanıyorum."),
 ("A", "sonrası", "Torunum \'nerede oturuyorsun dede\' diyor, "
  "\'ikinci etap, C blok\' diyorum. Sokak adı söyleyemiyorum."),
 ("B", "sonrası", "Eski adresimi yazmak istiyorum bazen, "
  "ama o adres artık yok. Posta kutusunda bile yok."),
 ("E", "sonrası", "Sokak adlarının çoğu etap numarasına dönüştü. "
  "İdari bir değişiklik gibi görünüyor ama insanlar için öyle değil."),
 ("A", "öncesi", "Her sokağın bir adı, bir de halk arasındaki adı "
  "vardı. İkisini de bilirdik."),
],
"T3-K3": [
 ("A", "sonrası", "Eski fotoğrafları çıkardım, torunlara gösterdim. "
  "\'Burası neresi dede\' dediler."),
 ("B", "inşaat", "Taşınırken kapının kolunu söküp aldım. Saçma "
  "geliyor biliyorum, ama bir şey kalsın istedim."),
 ("A", "sonrası", "Dernek bir fotoğraf sergisi yaptı. Herkes ağladı. "
  "Bir de şunu fark ettim: fotoğraftaki insanların çoğu gitmiş."),
 ("C", "sonrası", "Dükkânın ilk gün fotoğrafı var, babamla çekilmişiz. "
  "Arkada eski sokak görünüyor."),
 ("E", "sonrası", "Sözlü tarih çalışması başlattık, otuz kişiyle "
  "görüştük. Anlatılan her şey \'eskiden\' diye başlıyor."),
 ("A", "sonrası", "Annemin çeyiz sandığı duruyor. Yeni evde yeri yok "
  "ama atamadım, balkonda."),
],
"T3-K4": [
 ("A", "sonrası", "Burası artık benim mahallem değil. Evim burada "
  "ama mahallem değil. İkisi ayrı şey."),
 ("B", "sonrası", "Yıldıztepe\'yi özlüyorum ama gitmek istemiyorum. "
  "Çünkü gittiğimde özlediğim şeyi bulamıyorum."),
 ("A", "sonrası", "Adres aynı, bina farklı, insanlar farklı. "
  "Ne kalmış geriye?"),
 ("A", "sonrası", "Kendimi misafir gibi hissediyorum. "
  "Kırk yıldır buradayım."),
 ("D", "sonrası", "Ben buraya aidiyet hissetmiyorum, dürüst olayım. "
  "Yatırım olarak aldım."),
 ("B", "sonrası", "Nereli olduğumu soranlara hâlâ Yıldıztepe diyorum. "
  "Ama gidip bakmıyorum."),
],
"T3-K5": [
 ("A", "sonrası", "Cami yerinde duruyor, tek o kaldı. Cuma günü "
  "oraya gidiyorum, eski yüzleri orada görüyorum."),
 ("A", "sonrası", "Okul aynı yerde. Çocuklarım orada okudu, "
  "torunum da okuyor. Tutunacak bir şey lazım insana."),
 ("B", "sonrası", "Mezarlık burada, annem babam burada yatıyor. "
  "Bağım o yüzden kopmadı tam."),
 ("E", "sonrası", "Cami, okul ve mezarlık korundu. Mahalleyi mahalle "
  "yapan bağların son üç direği bunlar."),
 ("C", "sonrası", "Cuma çıkışı eski müşterilerimi görüyorum. "
  "Haftada bir, o kadar."),
 ("A", "öncesi", "Cami avlusu buluşma yeriydi. Namaz kılmayan da "
  "oraya uğrardı, haber oradan alınırdı."),
],
"T4-K1": [
 ("A", "sonrası", "Aidat dört bin lira. Emekli maaşımın beşte biri."),
 ("A", "sonrası", "Havuz var, spor salonu var. Ben hiç kullanmıyorum "
  "ama parasını ödüyorum."),
 ("B", "sonrası", "Aidatı duyunca satmaya karar verdim. Ev benim ama "
  "giderini karşılayamıyorum."),
 ("E", "sonrası", "En çok gelen şikâyet aidat. Hak sahiplerinin bir "
  "kısmı ödeyemiyor, icra takibi başlayanlar var."),
 ("A", "sonrası", "Gençler \'kullanmıyorsan kullan\' diyor. "
  "Mesele kullanmak değil, ödeyememek."),
 ("D", "sonrası", "Aidat yüksek ama hizmet de var. Ben buna razıyım, "
  "hesaplayarak aldım."),
 ("A", "sonrası", "Eski evde aidat yoktu. Kapıcıya para verirdik, "
  "o kadar."),
],
"T4-K2": [
 ("B", "inşaat", "Kira yardımı iki yıl ödendi, inşaat dört yıl sürdü. "
  "Aradaki iki yılı kendimiz karşıladık."),
 ("B", "sonrası", "Kira üç katına çıktı. Mahallede kalamadım, "
  "iki ilçe öteye gittim."),
 ("B", "inşaat", "Kiracıydım, hak sahibi değildim. Yıkım kararı "
  "çıkınca bana kimse bir şey sormadı."),
 ("C", "sonrası", "Dükkân kirası beş katına çıktı. "
  "Kırk iki yıl sonra kapattım."),
 ("B", "sonrası", "Çocuğumun okulu burada kaldı, ben uzaktayım. "
  "Her sabah bir saat yol."),
 ("E", "sonrası", "Eski kiracıların neredeyse tamamı mahalleyi terk "
  "etti. Bu süreçte en sessiz kaybeden grup onlar oldu."),
],
"T4-K3": [
 ("A", "inşaat", "Müteahhitle üç yıl pazarlık ettik. Metrekare "
  "meselesi, kat meselesi. Sonunda imzaladık, başka çare yoktu."),
 ("A", "sonrası", "Bana söylenen daire ile verilen daire aynı "
  "değildi. İtiraz ettim, \'proje değişti\' dediler."),
 ("B", "inşaat", "Hak sahipliği için tapu gerekiyordu. Bizimki "
  "hisseliydi, beş kardeş. Anlaşamadık, satıp dağıldık."),
 ("E", "inşaat", "Sürecin en çatışmalı kısmı buydu. Komşular "
  "pazarlıkta karşı karşıya geldi, o kırgınlıklar hâlâ duruyor."),
 ("A", "inşaat", "Toplantılar gece yarılarına kadar sürerdi. "
  "Kimse kimseye güvenmiyordu."),
 ("C", "inşaat", "İşyeri sahiplerine ayrı bir şey teklif edilmedi. "
  "Konutla aynı kefeye konduk."),
],
"T4-K4": [
 ("C", "sonrası", "Müşterimin yarısı taşındı. Yeni gelenler zincir "
  "markete gidiyor. Ciro üçte bire düştü."),
 ("C", "inşaat", "İnşaat döneminde üç yıl kapalı kaldım. "
  "Açtığımda kimse beni hatırlamıyordu."),
 ("C", "sonrası", "Sitenin içine dükkân açmak istedim, yönetim izin "
  "vermedi. Kendi mahallemde esnaflık yapamıyorum."),
 ("A", "sonrası", "Bakkal gitti, manav gitti, kahve gitti. Üçü de "
  "gidince sokakta konuşacak yer kalmadı."),
 ("C", "sonrası", "Oğlum devralmak istemiyor. Haklı da, "
  "ben bile devam edeyim mi bilmiyorum."),
 ("E", "sonrası", "Yirmi iki esnaftan yedisi döndü. Geri kalanı "
  "başka mahallede ya da hiç."),
],
"T4-K5": [
 ("A", "sonrası", "Dürüst olmak gerekirse evin değeri beş katına "
  "çıktı. Şikâyet ediyorum ama bunu da söylemem lazım."),
 ("D", "sonrası", "Yatırım olarak baktığımda doğru karar verdim. "
  "İki yılda ciddi değerlendi."),
 ("A", "sonrası", "Çocuğuma kalacak bir şey oldu en azından. "
  "Eski evde bu yoktu."),
 ("B", "sonrası", "Sattım, iyi para aldım, başka yerde ev aldım. "
  "Ama mahalleyi satın alamadım."),
],
"T5-K1": [
 ("A", "sonrası", "Oğlum memnun. \'Baba kombi yandı, otopark var, "
  "asansör var\' diyor. Haklı da, ben de üşümüyorum artık."),
 ("D", "sonrası", "Isıtma merkezî, kışın sorun yok. "
  "Eski binalarda soba vardı diyorlar, ben görmedim bile."),
 ("D", "sonrası", "Otopark en büyük kazanç. Eskiden arabayı nereye "
  "koyacağım diye dolanırlarmış."),
 ("A", "sonrası", "Asansör olmasaydı bu yaşta beşinci kata "
  "çıkamazdım. Onu söylemek lazım."),
 ("A", "öncesi", "Eski evde kışın soba yakardık. Romatizmam "
  "oradan kaldı bana."),
],
"T5-K2": [
 ("A", "sonrası", "Benim yaşımdakiler zorlandı. Kartlı sistem, "
  "interkom, aidat otomatiği... Hepsini öğrenmek gerekti."),
 ("E", "sonrası", "Yaşlılar için ayrı bir sorun var: yeni binada "
  "komşu yok, dışarıda tanıdık yok. Yalnızlık arttı."),
 ("A", "sonrası", "Annem son bir yıl hiç dışarı çıkmadı. Eskiden "
  "kapının önüne çıkardı, şimdi çıkacağı bir kapı önü yok."),
 ("A", "sonrası", "Gençler alıştı, biz alışamadık. "
  "Mesele teknoloji değil, alışkanlık."),
 ("E", "sonrası", "Dijital destek programı açtık; en çok başvuru "
  "yetmiş yaş üstünden geldi."),
],
"T5-K3": [
 ("D", "sonrası", "Akşam dokuzda eve geliyorum, kapıda güvenlik var. "
  "Eskiden o sokaktan geçer miydim bilmiyorum."),
 ("A", "sonrası", "Kızım için daha rahatım, doğru. Aydınlatma iyi, "
  "kamera var. Bunu inkâr edemem."),
 ("D", "sonrası", "Kadın olarak güvenlik benim için ilk sırada. "
  "Site bu açıdan iyi."),
 ("E", "sonrası", "Kadın sakinlerle yaptığımız toplantıda güvenlik en "
  "olumlu başlıktı. Erkeklerde aynı vurgu yok."),
],
"T5-K4": [
 ("D", "sonrası", "Çocuk parkı sitenin içinde, pencereden görüyorum."),
 ("A", "sonrası", "Torunum aşağıda oynuyor, ben balkondan bakıyorum. "
  "Bu iyi tarafı, kabul."),
 ("D", "sonrası", "Oyun alanı temiz ve kapalı. "
  "Çocuk için bundan iyisi yok."),
 ("A", "sonrası", "Ama çocuklar birbirini tanımıyor. Parkta "
  "oynuyorlar, sonra her biri ayrı bloğa gidiyor."),
 ("A", "öncesi", "Çocuklar sokakta büyürdü. Kimin çocuğu olduğunu "
  "bilmeden kimse azarlamazdı, herkes herkesin çocuğuna bakardı."),
],
}

# Konuşma açıcıları. Gerçek dökümlerde her cümle doğrudan başlamaz;
# konuşmacının kendi dil alışkanlığı vardır. Her katılımcıya sabit bir
# açıcı kümesi atanır, böylece aynı çekirdek ifade farklı ağızlardan
# farklı duyulur.
ACICILAR = [
    "", "", "", "Yani ", "Bakın ", "Şöyle söyleyeyim, ", "Valla ",
    "Şimdi ", "Doğrusu ", "Ben şunu diyeyim: ", "Açık konuşayım, ",
    "Bir de şu var: ", "Nasıl anlatsam, ", "Düşünün ki ",
]

# ------------------------------------------------- mülakat formu soruları
SORULAR = [
    (1, "Mahallede ne kadar zamandır yaşıyorsunuz? Buraya nasıl "
        "geldiniz, biraz anlatır mısınız?", "öncesi"),
    (2, "Dönüşümden önceki komşuluk ilişkilerinizi nasıl tarif "
        "edersiniz?", "öncesi"),
    (3, "Yıkım ve inşaat süreci sizin için nasıl geçti?", "inşaat"),
    (4, "O dönemde nerede oturdunuz, günlük hayatınız nasıl etkilendi?",
     "inşaat"),
    (5, "Eski komşuluk ilişkileriniz ile bugünkü sitedeki yaşamı nasıl "
        "kıyaslarsınız?", "sonrası"),
    (6, "Bugün kendinizi bu mahallenin bir parçası olarak hissediyor "
        "musunuz?", "sonrası"),
    (7, "Dönüşümün size göre en iyi ve en kötü yanı ne oldu?",
     "sonrası"),
    (8, "Eklemek istediğiniz bir şey var mı?", "sonrası"),
]

# Her katılımcı tipinin hangi evrede hangi kodlara yönelme eğilimi var.
# Bu, sahada gözlenen bir örüntünün karşılığıdır: esnaf ekonomiye,
# yeni sakin konfora, yaşlı sakin hafızaya ağırlık verir.
EGILIM = {
    "A": {"T1": 1.0, "T2": 1.3, "T3": 1.4, "T4": 0.9, "T5": 0.6},
    "B": {"T1": 0.8, "T2": 1.1, "T3": 1.5, "T4": 1.3, "T5": 0.3},
    "C": {"T1": 0.9, "T2": 1.0, "T3": 1.1, "T4": 1.8, "T5": 0.3},
    "D": {"T1": 0.7, "T2": 0.9, "T3": 0.4, "T4": 0.7, "T5": 1.9},
    "E": {"T1": 1.1, "T2": 1.2, "T3": 1.2, "T4": 1.3, "T5": 0.8},
}

GRUP_ADI = {
    "A": "Eski sakin — yerinde kalan",
    "B": "Eski sakin — mahalleden ayrılan",
    "C": "Mahalle esnafı",
    "D": "Yeni site sakini",
    "E": "Kilit aktör",
}
GRUP_SAYI = {"A": 12, "B": 8, "C": 7, "D": 7, "E": 4}

MESLEK = {
    "A": ["emekli memur", "emekli işçi", "terzi", "öğretmen", "ev hanımı",
          "serbest muhasebeci", "şoför", "emekli hemşire"],
    "B": ["tekstil işçisi", "kuaför", "emekli", "güvenlik görevlisi",
          "ev hanımı", "kurye"],
    "C": ["bakkal", "kahveci", "manav", "kuaför", "tamirci", "fırıncı",
          "kırtasiyeci"],
    "D": ["yazılımcı", "banka çalışanı", "mimar", "öğretim görevlisi",
          "satış uzmanı", "doktor"],
    "E": ["muhtar", "mahalle derneği başkanı", "okul müdürü",
          "cami imamı"],
}
KONUT = {"A": ["hak sahibi — mülk"], "B": ["eski kiracı", "satıp ayrılan"],
         "C": ["işyeri kiracısı", "işyeri mülk sahibi"],
         "D": ["sonradan satın alan", "kiracı"],
         "E": ["hak sahibi — mülk", "mahalle dışı görevli"]}


def evre_kodlari(evre, grup):
    """Bir evrede ve konuşmacı tipinde ifadesi bulunan kodları verir.

    Evre süzgeci bankanın kendisinden gelir: bir kodun o evrede
    yazılmış ifadesi yoksa o soruda hiç geçmez. Böylece "dönüşümden
    önce komşuluk nasıldı" sorusuna bugünü anlatan bir yanıt düşemez.
    """
    kendi = [k for k, sozler in SOZLER.items()
             if any(t == grup and e == evre for t, e, _ in sozler)]
    if kendi:
        return kendi
    return [k for k, sozler in SOZLER.items()
            if any(e == evre for _, e, _ in sozler)]


def soz_sec(kod, grup, evre, kullanilan):
    """Kullanılmamış ifadeyi önceler: aynı cümle iki kişinin ağzından
    çıkmasın. Banka tükenirse tekrar kaçınılmaz olur; o durumda
    konuşma açıcısı farklılaştırır."""
    for sart in (lambda t, e: t == grup and e == evre,
                 lambda t, e: e == evre,
                 lambda t, e: True):
        adaylar = [s for t, e, s in SOZLER[kod]
                   if sart(t, e) and (kod, s) not in kullanilan]
        if adaylar:
            secim = adaylar[int(rng.integers(len(adaylar)))]
            kullanilan.add((kod, secim))
            return secim
    havuz = [s for t, e, s in SOZLER[kod] if e == evre] or \
            [s for _, _, s in SOZLER[kod]]
    return havuz[int(rng.integers(len(havuz)))]


def acici_ata(katilimci_kodu):
    """Her katılımcıya kendi konuşma açıcısı kümesini verir."""
    tohum = sum(ord(c) for c in katilimci_kodu)
    yerel = np.random.default_rng(TOHUM + tohum)
    return list(yerel.choice(ACICILAR, size=4, replace=False))


def main(cikti_klasoru: str) -> None:
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------- katılımcılar
    katilimcilar = []
    no = 0
    zincir_havuzu = []
    for grup, adet in GRUP_SAYI.items():
        for _ in range(adet):
            no += 1
            kod = f"K{no:02d}"
            yas = int(rng.integers(26, 48) if grup == "D"
                      else rng.integers(34, 82))
            mahallede = (int(rng.integers(1, 4)) if grup == "D"
                         else int(min(yas - 18, rng.integers(18, 52))))
            # Kartopu: ilk üç kişi doğrudan erişim, sonrakiler yönlendirme
            yonlendiren = ("doğrudan erişim" if len(zincir_havuzu) < 3
                           else str(rng.choice(zincir_havuzu)))
            katilimcilar.append({
                "katilimci_kodu": kod,
                "grup": grup,
                "grup_adi": GRUP_ADI[grup],
                "yas": yas,
                "cinsiyet": str(rng.choice(["Kadın", "Erkek"],
                                           p=[0.48, 0.52])),
                "meslek": str(rng.choice(MESLEK[grup])),
                "mahallede_yil": mahallede,
                "konut_durumu": str(rng.choice(KONUT[grup])),
                "gorusme_dk": int(rng.integers(46, 91)),
                "gorusme_tarihi": str(
                    pd.Timestamp("2025-09-15")
                    + pd.Timedelta(days=int(rng.integers(0, 400))))[:10],
                "tur": int(rng.choice([1, 2], p=[0.74, 0.26])),
                "yonlendiren": yonlendiren,
            })
            zincir_havuzu.append(kod)

    kat_df = pd.DataFrame(katilimcilar)

    # ------------------------------------------------------------ mülakatlar
    parcalar = []
    kullanilan = set()
    parca_no = 0
    aciciler = {k["katilimci_kodu"]: acici_ata(k["katilimci_kodu"])
                for k in katilimcilar}
    for k in katilimcilar:
        grup = k["grup"]
        for soru_no, soru, evre in SORULAR:
            adaylar = evre_kodlari(evre, grup)
            agirlik = np.array([EGILIM[grup][kod[:2]] for kod in adaylar],
                               dtype=float)
            agirlik /= agirlik.sum()
            kac = int(rng.choice([1, 2, 3], p=[0.40, 0.46, 0.14]))
            secilen = list(rng.choice(adaylar, size=min(kac, len(adaylar)),
                                      replace=False, p=agirlik))
            for kod in secilen:
                parca_no += 1
                govde = soz_sec(kod, grup, evre, kullanilan)
                acici = aciciler[k["katilimci_kodu"]][
                    int(rng.integers(4))]
                metin = (acici + govde[0].lower() + govde[1:]
                         if acici else govde)
                parcalar.append({
                    "parca_id": f"M{parca_no:04d}",
                    "kaynak": "mülakat",
                    "katilimci_kodu": k["katilimci_kodu"],
                    "grup": grup,
                    "soru_no": soru_no,
                    "evre": evre,
                    "metin": metin,
                    "referans_kod": kod,
                    "referans_tema": KOD_TEMA[kod],
                })

    mul_df = pd.DataFrame(parcalar)

    # --------------------------------------------------------- odak gruplar
    ODAK = [
        ("OG1", "Yaşlı sakinler", ["A", "A", "A", "B", "A", "B", "A"]),
        ("OG2", "Kadın sakinler", ["A", "A", "D", "A", "D", "B", "A", "D"]),
        ("OG3", "Gençler (18–30)", ["D", "A", "D", "A", "D", "D"]),
        ("OG4", "Mahalle esnafı", ["C", "C", "C", "C", "C", "C"]),
        ("OG5", "Yeni sakinler", ["D", "D", "D", "D", "D", "D", "D"]),
        ("OG6", "Karma grup", ["A", "B", "C", "D", "E", "A", "D", "C"]),
    ]
    og_parcalar = []
    og_no = 0
    for og_kod, og_ad, uyeler in ODAK:
        for sira, grup in enumerate(uyeler, start=1):
            konusmaci = f"{og_kod}-{sira}"
            for _ in range(int(rng.integers(2, 5))):
                adaylar = evre_kodlari("sonrası", grup)
                agirlik = np.array([EGILIM[grup][kod[:2]] for kod in adaylar],
                                   dtype=float)
                agirlik /= agirlik.sum()
                kod = str(rng.choice(adaylar, p=agirlik))
                og_no += 1
                govde = soz_sec(kod, grup, "sonrası", kullanilan)
                og_parcalar.append({
                    "parca_id": f"O{og_no:04d}",
                    "kaynak": "odak grup",
                    "odak_grup": og_kod,
                    "odak_grup_adi": og_ad,
                    "konusmaci": konusmaci,
                    "grup": grup,
                    "evre": "sonrası",
                    "metin": govde,
                    "referans_kod": kod,
                    "referans_tema": KOD_TEMA[kod],
                })
    og_df = pd.DataFrame(og_parcalar)

    # ---------------------------------------------------------- alan notları
    MEKANLAR = ["site girişi", "çocuk parkı", "eski cami avlusu",
                "A blok lobisi", "mahalle kahvesi (yeni)", "market önü",
                "okul çıkışı", "otopark rampası", "muhtarlık",
                "eski sokak hattı", "site sosyal tesisi", "durak"]
    GOZLEM = [
        ("Girişte kart okutma sırası oluştu; iki yaşlı sakin kartı "
         "bulamadı, güvenlik elle açtı. Bu üçüncü kez gördüğüm durum.",
         "T1-K2"),
        ("Akşam 18.40. Lobide altı kişi var, hiçbiri konuşmuyor. "
         "Asansör gelene kadar beş kişi telefona baktı.", "T2-K4"),
        ("Parkta on bir çocuk oynuyor; veliler birbirinden ayrı "
         "oturuyor, aralarında konuşma yok.", "T5-K4"),
        ("Cami avlusunda cuma sonrası on beş dakika süren bir "
         "toplanma oldu. Burası hâlâ karşılaşma yeri.", "T3-K5"),
        ("Kahvede altı masa dolu, hepsi 60 yaş üstü erkek. "
         "Genç yok, kadın yok.", "T2-K2"),
        ("Esnaf bana veresiye defterini gösterdi: son kayıt "
         "on dört ay önce.", "T2-K3"),
        ("Site yönetim panosunda 'kapı önünde oturmak yasaktır' "
         "uyarısı asılı. Altına el yazısıyla not düşülmüş.", "T2-K2"),
        ("Eski sokak hattında yürüdüm. Çeşmenin yeri artık trafo; "
         "yaşlı bir sakin oradan geçerken durup baktı.", "T3-K1"),
        ("WhatsApp grubunda bugün 63 mesaj aktı. Konular: otopark, "
         "aidat, su kesintisi. Komşuluk içerikli mesaj yok.", "T2-K6"),
        ("Aidat toplantısında salon ikiye ayrılmış oturdu: "
         "hak sahipleri solda, sonradan alanlar sağda.", "T2-K5"),
        ("Bloklar arası geçitte rüzgâr çok sert; iki kişi "
         "yolunu değiştirip dolaştı.", "T1-K4"),
        ("Markette üç müşteri izledim; üçü de kasiyerle "
         "selamlaşmadı, konuşma olmadı.", "T2-K1"),
        ("Muhtarlıkta bir saat bekledim: gelen yedi kişiden beşi "
         "aidat ve icra konusunda geldi.", "T4-K1"),
        ("Okul çıkışında veliler kümelenmiş konuşuyor. "
         "Gördüğüm en canlı karşılaşma burası.", "T3-K5"),
        ("Eski bakkalın yerindeki kuaförde, duvarda mahallenin "
         "1998 tarihli bir fotoğrafı asılı.", "T3-K3"),
    ]
    notlar = []
    for i in range(44):
        metin, kod = GOZLEM[i % len(GOZLEM)]
        notlar.append({
            "not_id": f"N{i+1:03d}",
            "tarih": str(pd.Timestamp("2025-09-20")
                         + pd.Timedelta(days=int(rng.integers(0, 390))))[:10],
            "mekan": str(rng.choice(MEKANLAR)),
            "sure_dk": int(rng.integers(20, 180)),
            "metin": metin,
            "referans_kod": kod,
            "referans_tema": KOD_TEMA[kod],
        })
    not_df = pd.DataFrame(notlar).sort_values("tarih").reset_index(drop=True)

    # ------------------------------------------------------------- arşiv
    ARSIV = [
        ("gazete kupürü", "Yerel Haber", "2019-04-12",
         "Yıldıztepe'de dönüşüm kararı: 1.240 bağımsız bölüm yıkılacak"),
        ("gazete kupürü", "Yerel Haber", "2019-11-03",
         "Hak sahipleri metrekare dağılımına itiraz etti"),
        ("dilekçe", "Yıldıztepe Mahalle Derneği", "2020-02-18",
         "Çeşmenin korunması talebi — 212 imza"),
        ("dilekçe", "Yıldıztepe Mahalle Derneği", "2021-06-09",
         "Kira yardımı süresinin uzatılması talebi — 388 imza"),
        ("gazete kupürü", "Kent Gazetesi", "2021-09-27",
         "İnşaat gecikti, kira yardımı kesildi: aileler mağdur"),
        ("fotoğraf", "Dernek arşivi", "1998-05-01",
         "Gülbahar Sokak, bahar şenliği — 40 kişi"),
        ("fotoğraf", "Dernek arşivi", "2007-08-14",
         "Köşe çeşmesi ve bakkal, sokak görünümü"),
        ("fotoğraf", "Katılımcı K03 arşivi", "2014-06-20",
         "Okul bahçesindeki çınar ağacı altında mezuniyet"),
        ("fotoğraf", "Araştırmacı arşivi", "2026-03-11",
         "Aynı noktadan güncel görünüm: trafo ve B blok"),
        ("toplantı tutanağı", "Site yönetimi", "2025-12-04",
         "Aidat artışı oylaması: 148 kabul, 131 ret"),
        ("gazete kupürü", "Kent Gazetesi", "2024-10-02",
         "Yıldıztepe'nin yeni yüzü: üçüncü etap teslim edildi"),
        ("dilekçe", "Esnaf grubu", "2023-03-15",
         "Site içinde işyeri tahsisi talebi — reddedildi"),
        ("fotoğraf", "Dernek arşivi", "2019-12-01",
         "Yıkım öncesi son mahalle kahvaltısı"),
        ("toplantı tutanağı", "Muhtarlık", "2026-05-19",
         "Yaşlı sakinlere dijital destek programı kararı"),
        ("gazete kupürü", "Yerel Haber", "2026-08-08",
         "Mahalle derneğinden fotoğraf sergisi: 'Burası Neresi?'"),
        ("fotoğraf", "Katılımcı K17 arşivi", "2003-04-23",
         "Dükkân önünde baba-oğul, eski levha görünüyor"),
        ("dilekçe", "Kiracılar grubu", "2020-07-30",
         "Kiracılara geçici konut talebi — yanıtsız"),
        ("toplantı tutanağı", "Mahalle derneği", "2026-09-12",
         "Sözlü tarih projesi: 30 görüşme tamamlandı"),
        ("gazete kupürü", "Kent Gazetesi", "2026-01-17",
         "Dönüşüm sonrası aidat krizi: icra takibi 40 haneye ulaştı"),
    ]
    arsiv_df = pd.DataFrame(
        [{"arsiv_id": f"A{i+1:02d}", "tur": t, "kaynak": k, "tarih": d,
          "aciklama": a} for i, (t, k, d, a) in enumerate(ARSIV)])

    # ------------------------------------------------------------- yazma
    kat_df.to_csv(hedef / "kentsel_katilimcilar.csv", index=False,
                  encoding="utf-8-sig")
    mul_df.drop(columns=["referans_kod", "referans_tema"]).to_csv(
        hedef / "kentsel_mulakatlar.csv", index=False, encoding="utf-8-sig")
    og_df.drop(columns=["referans_kod", "referans_tema"]).to_csv(
        hedef / "kentsel_odak_gruplar.csv", index=False,
        encoding="utf-8-sig")
    not_df.drop(columns=["referans_kod", "referans_tema"]).to_csv(
        hedef / "kentsel_saha_notlari.csv", index=False,
        encoding="utf-8-sig")
    arsiv_df.to_csv(hedef / "kentsel_arsiv.csv", index=False,
                    encoding="utf-8-sig")

    # Referans kodlama ayrı dosyada durur: kodlama denemesi yapılırken
    # yanlışlıkla okunmasın diye.
    pd.concat([
        mul_df[["parca_id", "referans_kod", "referans_tema"]],
        og_df[["parca_id", "referans_kod", "referans_tema"]],
        not_df.rename(columns={"not_id": "parca_id"})[
            ["parca_id", "referans_kod", "referans_tema"]],
    ]).to_csv(hedef / "kentsel_referans_kodlar.csv", index=False,
              encoding="utf-8-sig")

    pd.DataFrame([{"kod": k, "tema": t, "tanim": a} for k, t, a in KODLAR]
                 ).to_csv(hedef / "kentsel_kod_kitabi_referans.csv",
                          index=False, encoding="utf-8-sig")

    # --------------------------------------------- insan okuması: dökümler
    satir = [f"{MAHALLE.upper()} ARAŞTIRMASI — DERİNLEMESİNE MÜLAKAT "
             f"DÖKÜMLERİ", "=" * 74,
             "SENTETİK KORPUS. Kurgusal mahalle, kurgusal katılımcılar.", ""]
    for k in katilimcilar:
        satir += ["", "-" * 74,
                  f"{k['katilimci_kodu']} · {k['grup_adi']} · "
                  f"{k['yas']} yaş · {k['cinsiyet']} · {k['meslek']}",
                  f"Mahallede {k['mahallede_yil']} yıl · "
                  f"{k['konut_durumu']} · {k['gorusme_dk']} dk · "
                  f"{k['gorusme_tarihi']} · {k['tur']}. tur",
                  "-" * 74]
        alt = mul_df[mul_df["katilimci_kodu"] == k["katilimci_kodu"]]
        for soru_no, soru, _evre in SORULAR:
            yanitlar = alt[alt["soru_no"] == soru_no]["metin"].tolist()
            if not yanitlar:
                continue
            satir.append(f"\nA: {soru}")
            satir.append(f"K: {' '.join(yanitlar)}")
    (hedef / "kentsel_mulakatlar.txt").write_text(
        "\n".join(satir) + "\n", encoding="utf-8")

    og_satir = [f"{MAHALLE.upper()} ARAŞTIRMASI — ODAK GRUP DÖKÜMLERİ",
                "=" * 74, "SENTETİK KORPUS.", ""]
    for og_kod, og_ad, uyeler in ODAK:
        og_satir += ["", "-" * 74,
                     f"{og_kod} · {og_ad} · {len(uyeler)} katılımcı",
                     "-" * 74]
        for _, s in og_df[og_df["odak_grup"] == og_kod].iterrows():
            og_satir.append(f"{s['konusmaci']}: {s['metin']}")
    (hedef / "kentsel_odak_gruplar.txt").write_text(
        "\n".join(og_satir) + "\n", encoding="utf-8")

    form = ["YARI YAPILANDIRILMIŞ MÜLAKAT FORMU", "=" * 74,
            f"{MAHALLE} Mahallesi · kentsel dönüşüm ve mahalle kültürü", "",
            "Açılış: araştırmanın amacı, ses kaydı izni, kimliğin "
            "gizliliği ve istenildiği an bırakma hakkı okunur.", ""]
    for no_s, soru, evre in SORULAR:
        form.append(f"{no_s}. [{evre}] {soru}")
    form += ["", "Sondalar (probe):",
             "  — Bunu bir örnekle anlatabilir misiniz?",
             "  — O sırada ne hissettiniz?",
             "  — Bu sizin için ne zaman değişti?",
             "  — Başka kimler böyle düşünüyor sizce?"]
    (hedef / "kentsel_mulakat_formu.txt").write_text(
        "\n".join(form) + "\n", encoding="utf-8")

    print(f"Katılımcı        : {len(kat_df)}")
    print(f"Mülakat parçası  : {len(mul_df)}")
    print(f"Odak grup parçası: {len(og_df)}  ({len(ODAK)} oturum)")
    print(f"Alan notu        : {len(not_df)}")
    print(f"Arşiv kaydı      : {len(arsiv_df)}")
    print(f"Toplam kodlama birimi: "
          f"{len(mul_df) + len(og_df) + len(not_df)}")
    print(f"Kod sayısı       : {len(KODLAR)}  "
          f"({len(set(t for _, t, _ in KODLAR))} tema)")


if __name__ == "__main__":
    main(sys.argv[1])
