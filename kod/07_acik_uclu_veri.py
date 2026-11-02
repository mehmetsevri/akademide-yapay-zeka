# -*- coding: utf-8 -*-
"""
07 — Açık uçlu anket yanıtları (tematik analiz için veri)

!!! BU METİNLER SENTETİKTİR. !!!
Gerçek katılımcılardan toplanmamıştır; tematik analiz yöntemini öğretmek
için yazılmıştır. Hiçbir yanıt gerçek bir kişinin görüşü değildir ve
hiçbiri bulgu olarak alıntılanamaz.

Neden sentetik: açık uçlu yanıt içeren, kişisel veri barındırmayan ve
açık lisansla dağıtılabilen Türkçe bir akademisyen anketi mikro verisi
kamuya açık değildir. Nicel örnekler gerçek veri setleriyle yürütülmüştür
(UCI 262 ve UCI 967); yalnız bu nitel katman üretilmiştir.

Yanıtlar üç ölçütle yazılmıştır:
  1. Uzunluk ve üslup çeşitliliği — bir sözcüklük yanıttan üç cümleye
  2. Çelişkili ve kararsız yanıtlar — gerçek veride olduğu gibi
  3. Kodlanamayan yanıtlar — konuya değmeyen, boş sayılacak birkaç yanıt

Kullanım:
  python 07_acik_uclu_veri.py <çıktı_klasörü>
"""
import pathlib
import sys

import pandas as pd

SORULAR = {
    1: "Üretken yapay zekâ araçlarını araştırma sürecinizin hangi "
       "aşamasında yararlı buluyorsunuz? Örnek vererek yazınız.",
    2: "Bu araçların akademik kullanımına ilişkin çekince ve "
       "kaygılarınızı yazınız.",
    3: "Bu konuda kurumunuzdan beklentileriniz nelerdir?",
}

# (katılımcı no, soru no, yanıt)
YANITLAR = [
    # ===================== SORU 1 — fayda görülen aşamalar =====================
    ("K004", 1, "Literatür taramasında işe yarıyor. Elli makalenin özetini okuyup hangisini açacağıma karar vermek yerine, hepsini birden taratıp bana ilgili olanları listeletiyorum. Zaman kazancı ciddi."),
    ("K007", 1, "Esas olarak İngilizce yazarken. Metni ben yazıyorum, sonra dil düzeltmesi için veriyorum. Native speaker'a para ödemekten kurtuldum."),
    ("K011", 1, "Python kodu yazdırıyorum. İstatistik analizlerinde kendim kod yazmakta zorlanıyordum, şimdi analizi anlatıp kodu alıyorum, sonra çıktıyı kontrol ediyorum."),
    ("K013", 1, "Hiçbir aşamada kullanmıyorum. Denedim, güvenemedim."),
    ("K016", 1, "Makalenin iskeletini çıkarmakta. Bölüm başlıklarını, hangi bölümde ne anlatılacağını konuşuyorum onunla. Yazıyı kendim yazıyorum ama plan çıkarmak kolaylaşıyor."),
    ("K019", 1, "Hakem cevabı yazarken. Hakemin on maddelik eleştirisini maddeleyip her birine ne cevap vereceğimi planlıyorum. Cevabın dilini de yumuşatıyor."),
    ("K022", 1, "Ders materyali hazırlamakta çok işime yarıyor ama araştırmada pek kullanmıyorum. Sunum, soru havuzu, örnek problem üretiyorum."),
    ("K025", 1, "Proje önerisi yazarken özgün değer kısmını tartışmak için kullanıyorum. Benim yazdığımı okutup 'bir değerlendirici bunu nasıl eleştirir' diye sorduruyorum. Çok işe yarıyor."),
    ("K028", 1, "Veri temizleme. Elimde yirmi farklı formatta gelmiş anket çıktısı vardı, tek biçime indirmek günlerimi alırdı."),
    ("K031", 1, "Özet yazımı. Dört bin kelimelik makaleyi iki yüz elli kelimeye indirmek benim en zorlandığım iş."),
    ("K034", 1, "Yabancı dildeki makaleleri hızlı anlamak için. Alanım dışı bir makaleyi okumam gerektiğinde önce özetletiyorum, sonra gerekiyorsa kendim okuyorum."),
    ("K037", 1, "Anahtar kelime belirlemede. Hangi terimlerle arama yapacağımı bilmiyordum, eş anlamlıları ve alanda kullanılan karşılıklarını çıkarttırdım."),
    ("K040", 1, "Tablo düzenleme ve biçimlendirme gibi sıkıcı işler. Derginin istediği formata çevirme işi."),
    ("K043", 1, "Fikir aşamasında. Kafamdaki yarım fikri anlatıp üstüne konuşuyorum, bir tür düşünme ortağı gibi. Çıktısını kullanmıyorum, konuşmanın kendisi fayda veriyor."),
    ("K046", 1, "Grafik çizdirmekte. Matplotlib kodunu kendim yazmaya çalışırken saatler harcıyordum."),
    ("K049", 1, "Etik kurul başvurusu metinleri. Her defasında aynı şeyleri yeniden yazmak yerine şablon üretiyorum."),
    ("K052", 1, "Henüz deneme aşamasındayım, net bir şey diyemem."),
    ("K055", 1, "Sistematik derlemede makale tarama kısmında. Dahil etme ölçütlerini verip yüz makalenin başlık-özetini taratıyorum, kararı ben veriyorum ama ön ayıklamayı o yapıyor."),
    ("K058", 1, "Kaynakça biçimlendirme. APA'dan IEEE'ye çevirme gibi işler."),
    ("K061", 1, "Yazdığım bölümün zayıf yerlerini bulmak için. Kendi metnimi okutup 'burada hangi iddia kanıtsız' diye sorduruyorum."),
    ("K064", 1, "İstatistik seçiminde. Verim şu, sorum bu, hangi testi kullanmalıyım diye soruyorum. Sonra kendim doğruluyorum ama nereden başlayacağımı biliyorum artık."),
    ("K067", 1, "Çok yararlı bulmuyorum. Ürettiği metin yüzeysel kalıyor, düzeltmek yeniden yazmaktan uzun sürüyor."),
    ("K070", 1, "Tez öğrencilerime yol gösterirken. Onların sorularına hızlı örnek üretmek için."),
    ("K073", 1, "Çeviri. Türkçe yazdığım bir bölümü İngilizceye çevirtip sonra üzerinde çalışıyorum. Sıfırdan İngilizce yazmaktan hızlı oluyor."),
    ("K076", 1, "Makale değerlendirirken hakem olarak. Kendi raporumu yazdıktan sonra gözden kaçırdığım bir şey var mı diye kontrol ettiriyorum."),
    ("K079", 1, "Literatürdeki boşluğu görmek için. On beş makalenin bulgularını bir tabloya döktürüp hangi konunun çalışılmadığını arıyorum."),
    ("K082", 1, "Sunum hazırlama ve konuşma metni."),
    ("K085", 1, "Nitel veri kodlamada deniyorum. Görüşme dökümlerini verip ilk kodları çıkarttırıyorum, sonra kendim gözden geçiriyorum. Zaman kazandırıyor ama kodların yarısını değiştiriyorum."),
    ("K088", 1, "Düzeltme ve son okuma. Yazım hatası, cümle düşüklüğü, tekrar eden ifadeler."),
    ("K091", 1, "Araştırma sorusunu daraltmakta. Geniş bir konuyla başlıyorum, soru sorarak daraltıyorum."),
    ("K094", 1, "Literatür ve dil. Bu ikisi dışında kullanmıyorum, kullanmak da istemiyorum."),
    ("K097", 1, "Veri görselleştirmede. Hangi grafik türünün uygun olduğunu tartışıp sonra çizdiriyorum."),
    ("K100", 1, "Ödev değerlendirmede kullanıyorum ama bunu söylemem gerekir mi bilmiyorum."),
    ("K103", 1, "Alanıma yeni giren konuları öğrenmek için. Yeni bir yöntemi anlatması, kitap okumaktan hızlı başlangıç veriyor."),
    ("K106", 1, "Kod hata ayıklama. Çalışmayan kodu verip nerede hata var diye soruyorum."),
    ("K109", 1, "Cover letter ve editöre yazılan yazılar."),
    ("K112", 1, "Tartışma bölümünde bulgularımı literatürle karşılaştırırken hangi çalışmalarla konuşmam gerektiğini bulmak için."),
    ("K115", 1, "Bir şey diyemem, kullanan meslektaşlarım var ama ben girmedim bu işe."),
    ("K118", 1, "Ölçek maddesi yazmakta. Anket maddelerini yazdırıp sonra uzman görüşüne sunuyorum. İlk taslak hızlı çıkıyor."),
    ("K121", 1, "Her aşamada az az. Tek bir yerde değil, günün içinde sürekli kullanıyorum; e-posta yazarken de, kod yazarken de."),
    ("K124", 1, "Meta-analizde etki büyüklüğü hesaplamalarını kontrol etmek için. Kendi hesabımı doğrulatıyorum."),
    ("K127", 1, "Çalıştığım konu çok nicedir, bu araçların alanımda işe yaradığını düşünmüyorum."),
    ("K130", 1, "Başlık ve anahtar kelime üretimi. On başlık alternatifi üretip aralarından seçiyorum."),
    ("K133", 1, "Not tutma ve okuduğum makalelerin özetini biriktirme. Kendi arşivimi kurdum böyle."),

    # ===================== SORU 2 — çekinceler ve kaygılar =====================
    ("K004", 2, "Uydurduğu kaynaklar. İki kez bana var olmayan makale verdi, DOI'si de vardı, açtım açılmadı. Artık her kaynağı tek tek kontrol ediyorum ama bu da ayrı iş."),
    ("K007", 2, "Yazdığı metin benim mi? Dil düzeltmesi yaptırdığımda hâlâ benim metnim sayılır mı, nereye kadar? Bunun sınırı belirsiz ve kimse söylemiyor."),
    ("K010", 2, "Veri gizliliği. Hasta verisiyle çalışıyorum, bu veriyi hiçbir buluta yüklemem. Ama meslektaşlarımın yüklediğini biliyorum ve kimse uyarmıyor."),
    ("K013", 2, "Her şeyden kaygılıyım. Bu araçların akademiye girmesi bilimin sonunu getirecek diye düşünüyorum."),
    ("K016", 2, "Kurum kuralı yok. Hangi derginin ne istediğini de bilmiyorum. Beyan etmem gerekiyor mu, ne yazmam gerekiyor, nereye yazmam gerekiyor — hiçbiri belli değil."),
    ("K019", 2, "Öğrenciler. Ödevleri artık değerlendiremiyorum. Hepsi aynı düzgünlükte, hepsi aynı yüzeysellikte. Kimin ne öğrendiğini anlamıyorum."),
    ("K022", 2, "Kendi yazma becerimi kaybediyorum. Eskiden bir paragrafı on beş dakikada kurardım, şimdi önce ona soruyorum. Bu bir kayıp."),
    ("K025", 2, "Ücret. Ben kendi paramla ödüyorum, ödemeyen meslektaşım ücretsiz sürümle çalışıyor ve arasındaki fark büyük. Bu eşitsizlik yayın rekabetine de yansıyor."),
    ("K028", 2, "İntihal yazılımları bunu yakalamıyor ama dergi yakalarsa ne olur? Geri çekilme riski var mı, bilmiyorum."),
    ("K031", 2, "Kaygım yok. Hesap makinesi de böyle tartışılmıştı."),
    ("K034", 2, "Yanlışı kendinden emin söylüyor. Bilmediğim bir konuda yanlış bir şey söylese anlamam. Bildiğim konuda yanlış söylediğini gördüm, bu yüzden bilmediğim konuda da güvenmiyorum."),
    ("K037", 2, "Hakemlikte kullanılması. Benim makalemi bir hakemin yapay zekâya okutup rapor yazdırdığını düşünmek rahatsız edici. Değerlendirilmeyi hak ettiğim şey okunmamış olabilir."),
    ("K040", 2, "Düşünme tembelliği. Bir soruyla uğraşıp çözmek yerine soruyorum. Zorlanmak öğrenmenin parçasıydı."),
    ("K043", 2, "Yazdığım makaleyi yükleyip düzeltme isterken aslında yayımlanmamış verimi üçüncü bir şirkete vermiş oluyorum. Bunun sözleşmesini kimse okumuyor."),
    ("K046", 2, "Herkes aynı araçları kullandığı için makaleler birbirine benzemeye başladı. Üslup farkı kalmıyor."),
    ("K049", 2, "Etik kurul bu konuda ne diyor bilmiyorum. Başvurumda yapay zekâ kullanacağımı yazmam gerekir mi?"),
    ("K052", 2, "Bilmediğim şeyden kaygı duymuyorum ama öğrenmem gerektiğini düşünüyorum."),
    ("K055", 2, "Sistematik derlemede tarama kararını ona bırakırsam, yanlı bir ayıklama yapmış olabilir ve bunu fark etmem imkânsız. Şeffaflık sorunu var."),
    ("K058", 2, "Türkçe üretimi kötü. İngilizcede iyi, Türkçede resmî dil tutmuyor, devrik cümle kuruyor. Türkçe yayın yapanlar için fayda sınırlı."),
    ("K061", 2, "Bana katılıyor. Yanlış bir şey söylediğimde düzeltmiyor, destekliyor. Bu bir düşünme ortağı için en kötü nitelik."),
    ("K064", 2, "İstatistik seçiminde yanlış yönlendirdi bir kez. Varsayım denetimi yapmadan test önerdi. Fark etmesem yanlış analizi yayımlamıştım."),
    ("K067", 2, "Yüzeysellik. Derinleşmesi gereken yerde genelleme yapıyor, her paragrafı aynı kalıpta kuruyor. Deneyimli bir okur bunu görür."),
    ("K070", 2, "Tez öğrencim tezinin bir bölümünü böyle yazdı ve itiraf etmedi. Fark ettim ama kanıtlayamadım. Bu durumda ne yapacağımı bilmiyorum."),
    ("K073", 2, "Çeviride anlam kaydırıyor. Teknik terimi bağlamdan koparıp yanlış karşılığı seçiyor, sonra cümle akıcı olduğu için hatayı görmek zorlaşıyor."),
    ("K076", 2, "Kurumsal lisans yok, kişisel hesapla kurum verisi işlemek sözleşmeye aykırı olabilir."),
    ("K079", 2, "Literatürü eski biliyor. Son bir yılın yayınlarını bilmiyor ama bilmediğini söylemiyor, eski bilgiyle cevap veriyor."),
    ("K082", 2, "Kaygılarım var ama kullanmaya devam ediyorum. Çelişkili olduğumu biliyorum."),
    ("K085", 2, "Nitel analizde kodları o çıkarırsa yorum kimin? Nitel araştırmada araştırmacının kendisi araçtır. Bu devredilemez."),
    ("K088", 2, "Yazım hatası düzelttiriyorum, bunda bir sorun görmüyorum. Metni yazdırmakta sorun görüyorum. Ama ikisi arasındaki çizgi kaygan."),
    ("K091", 2, "Fikri o verdiyse katkı sıralamasında nerede duruyor? Yazar olamaz biliyorum ama katkısı yok da denemez."),
    ("K094", 2, "Dergilerin politikası birbirinden farklı. Elsevier şöyle diyor, başka bir yayıncı böyle. Her gönderimde yeniden okumak gerekiyor."),
    ("K097", 2, "Grafik çizdirdiğimde eksen etiketlerini yanlış koydu, ben fark ettim. Fark etmeyen biri yanlış grafiği yayımlar."),
    ("K100", 2, "Ödev değerlendirmede kullandığımı söylemedim. Öğrenciye haksızlık mı bu, emin değilim."),
    ("K103", 2, "Yeni bir konuyu öğrenirken ondan öğrenirsem, öğrendiğim şey doğru mu? Kontrol etmek için konuyu bilmem gerekiyor, bilmediğim için ona soruyorum. Döngü."),
    ("K106", 2, "Kodun çalışması doğru olduğu anlamına gelmiyor. Çalışan ama yanlış hesaplayan kod verdi bir kez."),
    ("K112", 2, "Atıf uydurmasının en sinsi hâli: gerçek bir DOI'ye yanlış başlık yakıştırması. DOI açılıyor, yazı başka. Kontrol ederken açılıyor mu diye bakmak yetmiyor."),
    ("K118", 2, "Ölçek maddesi yazdırdım, kapsam geçerliği uzman görüşüyle sağlanır, onun yazdığı madde geçerli sayılır mı bilmiyorum."),
    ("K124", 2, "Hesap hatası yaptı. Etki büyüklüğünü yanlış formülle hesapladı, ben kontrol ettiğim için yakaladım."),
    ("K127", 2, "Alanımda kullanılmıyor, kaygılanacak bir şey görmüyorum."),
    ("K130", 2, "Veri uydurabileceğinden korkuyorum. Benim verimi değil ama 'örnek veri üret' dediğimde uyduruyor ve bunun gerçek sanılması çok kolay."),

    # ===================== SORU 3 — kurumdan beklentiler =====================
    ("K004", 3, "Eğitim. Ama bir saatlik tanıtım değil, elini kirleterek yapılan, kendi verimle çalıştığım bir atölye."),
    ("K007", 3, "Kurumsal lisans. Herkesin kendi parasıyla almasının yarattığı eşitsizlik ortadan kalksın."),
    ("K010", 3, "Veri güvenliği için kurum içinde çalışan bir sürüm. Hasta verisini dışarıya çıkarmadan kullanabileceğim bir altyapı."),
    ("K013", 3, "Yasaklanmasını bekliyorum ama olmayacağını biliyorum. O hâlde en azından sınır konsun."),
    ("K016", 3, "Yazılı kurum politikası. Neyin yapılabileceği, neyin yapılamayacağı, nasıl beyan edileceği — tek sayfa, net, bağlayıcı."),
    ("K019", 3, "Öğrenci tarafı için düzenleme. Ödev ve tezlerde ne kadarına izin verildiği belirlenmezse ben tek başıma çözemem."),
    ("K022", 3, "Beklentim yok. Kendi başımıza öğreniyoruz, öyle devam eder."),
    ("K025", 3, "Beyan şablonu. Makaleye yazacağım cümlenin kurum onaylı hâli verilsin, her defasında yeniden icat etmeyelim."),
    ("K028", 3, "Dergi politikalarını derleyen bir rehber. Hangi yayıncı ne istiyor, tek yerde."),
    ("K031", 3, "Lisans ve eğitim, ikisi birlikte."),
    ("K034", 3, "Atıf doğrulama için kurumsal bir araç veya en azından nasıl yapılacağının öğretilmesi."),
    ("K037", 3, "Hakemlik süreçleri için kural. Hakemlerin bu araçları kullanıp kullanamayacağı dergi düzeyinde değil, kurum düzeyinde de konuşulmalı."),
    ("K040", 3, "Zaman. Öğrenmek için zaman istiyorum, ders yükü ve idari işle bu araçları öğrenmeye vakit kalmıyor."),
    ("K043", 3, "Sözleşmelerin hukukçu tarafından okunup bize anlatılması. Veri nereye gidiyor, kim saklıyor, ne kadar süre."),
    ("K046", 3, "Etik kurul için güncellenmiş başvuru formu. İçinde yapay zekâ kullanımı alanı olsun."),
    ("K049", 3, "Etik kurul yönergesinin güncellenmesi."),
    ("K052", 3, "Başlangıç düzeyi eğitim. Hiç bilmeyen için."),
    ("K055", 3, "Sistematik derleme yapanlar için özel rehber. Genel eğitim bizim sorunumuzu çözmüyor."),
    ("K058", 3, "Türkçe akademik yazım için ayrı bir çalışma. Bu araçların Türkçesi zayıf, kurum bu boşluğu görmeli."),
    ("K061", 3, "Deneyimli kullananlarla deneyimsizleri eşleştiren bir yapı. Eğitimden çok, yanımda birinin olması işe yarıyor."),
    ("K064", 3, "İstatistik danışmanlığı. Yapay zekâdan bağımsız olarak bu zaten eksik; bu araçlar yanlış analizi hızlandırdı."),
    ("K070", 3, "Tez yönetmeliğinde açık hüküm. Öğrenciyle tartışırken dayanacağım bir metin olsun."),
    ("K073", 3, "Dil desteği. Kurumun İngilizce redaksiyon hizmeti olsa bu araçlara bu kadar yüklenmezdim."),
    ("K076", 3, "Kurumsal hesap ve kurumsal sorumluluk. Kişisel hesapla kurum işi yapmak sürdürülebilir değil."),
    ("K079", 3, "Veri tabanı erişimiyle bu araçları birleştiren bir altyapı. Web of Science'a bağlı çalışsa literatür sorunu çözülür."),
    ("K082", 3, "Açık tartışma ortamı. Kimse konuşmuyor, herkes kullanıyor. Bu suskunluk kuraldan daha zararlı."),
    ("K085", 3, "Nitel araştırmacılar için ayrı rehber. Nicel odaklı her şey; bizim sorunlarımız farklı."),
    ("K091", 3, "Yazarlık ve katkı konusunda kurum görüşü."),
    ("K097", 3, "Şekil ve tablo standartları eğitimi. Bu araçlarla üretilen grafiklerin yayın kalitesine ulaşması için."),
    ("K106", 3, "Kod gözden geçirme kültürü. Üretilen kodun kontrol edilmesi gerektiğini herkes bilmiyor."),
    ("K112", 3, "Kaynak doğrulama zorunluluğu getirilsin. Kurum, gönderilen makalelerde atıfların doğrulandığına dair bir onay isteyebilir."),
    ("K130", 3, "Eğitim, lisans, politika. Üçü olmadan bu iş kendi kendine yürümez."),
]


def main(cikti_klasoru: str) -> None:
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(YANITLAR, columns=["katilimci_no", "soru_no", "yanit"])
    df["soru_metni"] = df["soru_no"].map(SORULAR)
    df["karakter"] = df["yanit"].str.len()
    df["kelime"] = df["yanit"].str.split().str.len()
    df = df[["katilimci_no", "soru_no", "soru_metni", "yanit",
             "karakter", "kelime"]]
    df.to_csv(hedef / "anket_acik_uclu.csv", index=False,
              encoding="utf-8-sig")

    pd.DataFrame([{"soru_no": k, "soru_metni": v} for k, v in SORULAR.items()]
                 ).to_csv(hedef / "anket_acik_uclu_sorular.csv", index=False,
                          encoding="utf-8-sig")

    print(f"Yazıldı: {hedef / 'anket_acik_uclu.csv'}")
    print(f"  toplam yanıt : {len(df)}")
    for no in sorted(SORULAR):
        alt = df[df["soru_no"] == no]
        print(f"  soru {no}: {len(alt):3d} yanıt   "
              f"ortalama {alt['kelime'].mean():.1f} kelime "
              f"(en kısa {alt['kelime'].min()}, en uzun {alt['kelime'].max()})")
    print(f"  toplam kelime: {int(df['kelime'].sum()):,}")
    print(f"  farklı katılımcı: {df['katilimci_no'].nunique()}")


if __name__ == "__main__":
    main(sys.argv[1])
