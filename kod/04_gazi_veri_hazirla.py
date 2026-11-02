# -*- coding: utf-8 -*-
"""
04 — Sosyal bilimler örneği: Gazi Üniversitesi ders değerlendirme verisi

GERÇEK VERİ SETİ — açık erişimli, bilinen bir kaynak.

  Gündüz, N., & Fokoué, E. (2013). Turkiye Student Evaluation [Veri seti].
  UCI Machine Learning Repository. https://doi.org/10.24432/C5S02S
  Lisans: CC BY 4.0
  İndirme adresi:
  https://archive.ics.uci.edu/dataset/262/turkiye+student+evaluation

5.820 öğrenci değerlendirmesi, 28 Likert maddesi (1–5) ve beş ek değişken.
Eksik hücre yok. Veri seti olduğu gibi kullanılır; bu betik yalnızca
Türkçe madde sözlüğünü ve iki alt ölçek puanını ekler.

Maddelerin İngilizce özgün metni UCI belgelerinden alınmıştır; Türkçe
karşılıkları bu kurs için çevrilmiştir (özgün Türkçe form metni UCI
deposunda yayımlanmamıştır).

Kullanım:
  python 04_gazi_veri_hazirla.py <kaynak_csv> <çıktı_klasörü>
"""
import pathlib
import sys

import pandas as pd

# (kod, boyut, İngilizce özgün, Türkçe çeviri)
MADDELER = [
    ("Q1",  "Ders", "The semester course content, teaching method and evaluation system were provided at the start.", "Dönem başında dersin içeriği, öğretim yöntemi ve değerlendirme sistemi hakkında bilgi verildi."),
    ("Q2",  "Ders", "The course aims and objectives were clearly stated at the beginning.", "Dersin amaç ve hedefleri dönem başında açıkça belirtildi."),
    ("Q3",  "Ders", "The course was worth the amount of credit assigned to it.", "Ders, kendisine verilen kredi miktarını hak ediyordu."),
    ("Q4",  "Ders", "The course was taught according to the syllabus announced on the first day of class.", "Ders, ilk gün duyurulan izlenceye uygun yürütüldü."),
    ("Q5",  "Ders", "The class discussions, homework assignments, applications and studies were satisfactory.", "Sınıf tartışmaları, ödevler, uygulamalar ve çalışmalar doyurucuydu."),
    ("Q6",  "Ders", "The textbook and other courses resources were sufficient and up to date.", "Ders kitabı ve diğer kaynaklar yeterli ve güncel idi."),
    ("Q7",  "Ders", "The course allowed field work, applications, laboratory, discussion and other studies.", "Ders; saha çalışması, uygulama, laboratuvar ve tartışma gibi etkinliklere olanak verdi."),
    ("Q8",  "Ders", "The quizzes, assignment, projects and exams contributed to helping the learning.", "Kısa sınavlar, ödevler, projeler ve sınavlar öğrenmeye katkı sağladı."),
    ("Q9",  "Ders", "I greatly enjoyed the class and was eager to actively participate during the semester.", "Dersten büyük keyif aldım ve dönem boyunca etkin katılmaya istekliydim."),
    ("Q10", "Ders", "My initial expectations about the course were met at the end of the period or year.", "Derse ilişkin başlangıçtaki beklentilerim dönem sonunda karşılandı."),
    ("Q11", "Ders", "The course was relevant and beneficial to my professional development.", "Ders, mesleki gelişimim açısından ilgili ve yararlıydı."),
    ("Q12", "Ders", "The course helped me look at life and the world with a new perspective.", "Ders, yaşama ve dünyaya yeni bir bakışla bakmamı sağladı."),
    ("Q13", "Öğretim elemanı", "The Instructor's knowledge was relevant and up to date.", "Öğretim elemanının alan bilgisi ilgili ve güncel idi."),
    ("Q14", "Öğretim elemanı", "The Instructor came prepared for classes.", "Öğretim elemanı derslere hazırlıklı geldi."),
    ("Q15", "Öğretim elemanı", "The Instructor taught in accordance with the announced lesson plan.", "Öğretim elemanı duyurulan ders planına uygun ders anlattı."),
    ("Q16", "Öğretim elemanı", "The Instructor was committed to the course and was understandable.", "Öğretim elemanı derse bağlıydı ve anlatımı anlaşılırdı."),
    ("Q17", "Öğretim elemanı", "The Instructor arrived on time for classes.", "Öğretim elemanı derslere zamanında geldi."),
    ("Q18", "Öğretim elemanı", "The Instructor has a smooth and easy to follow delivery/speech.", "Öğretim elemanının anlatımı akıcı ve izlenebilirdi."),
    ("Q19", "Öğretim elemanı", "The Instructor made effective use of class hours.", "Öğretim elemanı ders saatlerini etkin kullandı."),
    ("Q20", "Öğretim elemanı", "The Instructor explained the course and was eager to be helpful to students.", "Öğretim elemanı dersi açıkladı ve öğrencilere yardımcı olmaya istekliydi."),
    ("Q21", "Öğretim elemanı", "The Instructor demonstrated a positive approach to students.", "Öğretim elemanı öğrencilere olumlu yaklaştı."),
    ("Q22", "Öğretim elemanı", "The Instructor was open and respectful of the views of students about the course.", "Öğretim elemanı derse ilişkin öğrenci görüşlerine açık ve saygılıydı."),
    ("Q23", "Öğretim elemanı", "The Instructor encouraged participation in the course.", "Öğretim elemanı derse katılımı özendirdi."),
    ("Q24", "Öğretim elemanı", "The Instructor gave relevant homework assignments/projects, and helped/guided students.", "Öğretim elemanı ilgili ödev/proje verdi ve öğrencilere yol gösterdi."),
    ("Q25", "Öğretim elemanı", "The Instructor responded to questions about the course inside and outside of the course.", "Öğretim elemanı ders içinde ve dışında derse ilişkin soruları yanıtladı."),
    ("Q26", "Öğretim elemanı", "The Instructor's evaluation system (midterm and final questions, projects, assignments, etc.) effectively measured the course objectives.", "Öğretim elemanının değerlendirme sistemi ders hedeflerini etkili biçimde ölçtü."),
    ("Q27", "Öğretim elemanı", "The Instructor provided solutions to exams and discussed them with students.", "Öğretim elemanı sınav çözümlerini paylaştı ve öğrencilerle tartıştı."),
    ("Q28", "Öğretim elemanı", "The Instructor treated all students in a right and objective manner.", "Öğretim elemanı tüm öğrencilere doğru ve nesnel davrandı."),
]

# Kaynak veri setindeki kodlu değişkenlerin anlamı (UCI belgeleri)
DEGISKEN_SOZLUGU = [
    ("instr",      "Öğretim elemanı kimliği", "1, 2, 3 — üç öğretim elemanı"),
    ("class",      "Ders kodu", "1–13 — on üç farklı ders"),
    ("nb.repeat",  "Dersi kaçıncı kez alıyor", "1 = birinci, 2 = ikinci, 3 = üçüncü kez"),
    ("attendance", "Derse katılım düzeyi", "0 = hiç … 4 = tam katılım"),
    ("difficulty", "Dersi algılanan güçlüğü", "1 = çok kolay … 5 = çok güç"),
]


def main(kaynak: str, cikti_klasoru: str) -> None:
    df = pd.read_csv(kaynak)
    hedef = pathlib.Path(cikti_klasoru)
    hedef.mkdir(parents=True, exist_ok=True)

    ders_maddeleri = [k for k, b, *_ in MADDELER if b == "Ders"]
    ogretim_maddeleri = [k for k, b, *_ in MADDELER if b == "Öğretim elemanı"]

    df["ders_puan"] = df[ders_maddeleri].mean(axis=1).round(4)
    df["ogretim_puan"] = df[ogretim_maddeleri].mean(axis=1).round(4)
    df["genel_puan"] = df[ders_maddeleri + ogretim_maddeleri].mean(axis=1).round(4)

    df.to_csv(hedef / "gazi_ders_degerlendirme.csv", index=False,
              encoding="utf-8-sig")

    pd.DataFrame(
        [{"madde": k, "boyut": b, "ingilizce_ozgun": e, "turkce_ceviri": t}
         for k, b, e, t in MADDELER]
    ).to_csv(hedef / "gazi_madde_sozlugu.csv", index=False,
              encoding="utf-8-sig")

    pd.DataFrame(
        [{"degisken": a, "anlam": b, "kodlama": c}
         for a, b, c in DEGISKEN_SOZLUGU]
    ).to_csv(hedef / "gazi_degisken_sozlugu.csv", index=False,
              encoding="utf-8-sig")

    boyut = (hedef / "gazi_ders_degerlendirme.csv").stat().st_size / 1024
    print(f"Veri    : {hedef / 'gazi_ders_degerlendirme.csv'}  "
          f"({len(df):,} satır, {df.shape[1]} sütun, {boyut:.0f} KB)")
    print(f"Madde   : {hedef / 'gazi_madde_sozlugu.csv'}  ({len(MADDELER)} madde)")
    print(f"Değişken: {hedef / 'gazi_degisken_sozlugu.csv'}")
    print(f"  ders_puan     ort={df['ders_puan'].mean():.3f}  ss={df['ders_puan'].std():.3f}")
    print(f"  ogretim_puan  ort={df['ogretim_puan'].mean():.3f}  ss={df['ogretim_puan'].std():.3f}")
    print(f"  eksik hücre   {int(df.isna().sum().sum())}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
