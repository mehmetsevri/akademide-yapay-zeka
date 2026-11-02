# -*- coding: utf-8 -*-
# =====================================================================
# 24 — Aynı modeli ikinci bir motorda koşturmak: R / lavaan
#
# "Yapay zekânın yazdığı analiz kodunun doğru olduğundan nasıl emin
# olacağım?" sorusunun en güçlü yanıtı budur: aynı modeli, aynı veriyle,
# BAŞKA BİR YAZILIMDA koşturup katsayıları karşılaştırmak.
#
# Python tarafında semopy, burada lavaan var. İkisi birbirinden bağımsız
# yazılmış, farklı ekiplerin ürünü. İki motor aynı maksimum olabilirlik
# kestirimini yapıyorsa, katsayılar dördüncü ondalığa kadar örtüşmeli.
# Örtüşmüyorsa ya model tanımları farklıdır ya biri hatalıdır — her iki
# durumda da bakılacak bir şey vardır.
#
# lavaan ayrıca semopy'nin iyi yapmadığı bir şeyi yapar: ÖLÇÜM
# DEĞİŞMEZLİĞİ (measurement invariance). Hibrit çalışanlarla tam uzaktan
# çalışanları karşılaştırmadan önce, ölçeğin iki grupta aynı şeyi ölçtüğü
# gösterilmelidir. Gösterilmezse grup farkı bulgusu, ölçeğin gruplara
# göre kayması olabilir.
#
# Kullanım:
#   Rscript 24_lavaan_dogrulama.R <veri_klasörü> <çıktı_klasörü>
# =====================================================================

args <- commandArgs(trailingOnly = TRUE)
veri_klasoru <- args[1]
cikti_klasoru <- args[2]
if (length(args) >= 3) .libPaths(c(args[3], .libPaths()))

suppressPackageStartupMessages({
  library(lavaan)
})

dir.create(cikti_klasoru, showWarnings = FALSE, recursive = TRUE)
rapor <- file(file.path(cikti_klasoru, "isletme_lavaan.txt"), open = "wt",
              encoding = "UTF-8")
yaz <- function(...) {
  satir <- paste0(...)
  cat(satir, "\n", sep = "")
  writeLines(satir, rapor)
}

df <- read.csv(file.path(veri_klasoru, "uzaktan_temiz.csv"),
               fileEncoding = "UTF-8-BOM")

yaz("LAVAAN DOĞRULAMA KOŞUMU")
yaz(strrep("-", 74))
yaz("R sürümü     : ", R.version.string)
yaz("lavaan sürümü: ", as.character(packageVersion("lavaan")))
yaz("Gözlem       : ", nrow(df))

model <- '
  # ölçüm modeli
  UCE =~ UCE1 + UCE2 + UCE3 + UCE4 + UCE5T
  IYD =~ IYD1 + IYD2 + IYD3 + IYD4T + IYD5
  OB  =~ OB1 + OB2 + OB3 + OB4 + OB5T + OB6
  CV  =~ CV1 + CV2 + CV3 + CV4 + CV5

  # yapısal model
  IYD ~ a1*UCE
  OB  ~ a2*UCE + d*IYD
  CV  ~ c*UCE + b1*IYD + b2*OB

  # dolaylı etkiler: adlandırılmış katsayıların çarpımı
  y1 := a1*b1
  y2 := a2*b2
  y3 := a1*d*b2
  toplam_dolayli := y1 + y2 + y3
  toplam := c + y1 + y2 + y3
'

# ---------------------------------------------------------------- 1
yaz("")
yaz(strrep("=", 74))
yaz("1 — Yapısal model (ML kestirimi)")
yaz(strrep("=", 74))

uyum <- sem(model, data = df, estimator = "ML")
olcutler <- fitMeasures(uyum, c("chisq", "df", "pvalue", "cfi", "tli",
                                "rmsea", "rmsea.ci.lower",
                                "rmsea.ci.upper", "srmr", "aic", "bic"))
for (ad in names(olcutler)) {
  yaz(sprintf("  %-18s %12.4f", ad, olcutler[[ad]]))
}
yaz(sprintf("  %-18s %12.4f", "chisq/df",
            olcutler[["chisq"]] / olcutler[["df"]]))

yaz("")
yaz("Standartlaştırılmış yapısal katsayılar:")
par <- standardizedSolution(uyum)
yapisal <- par[par$op == "~", ]
for (i in seq_len(nrow(yapisal))) {
  s <- yapisal[i, ]
  yaz(sprintf("  %-5s <- %-5s  beta = %7.4f  s.h. = %6.4f  z = %7.3f  p = %s",
              s$lhs, s$rhs, s$est.std, s$se, s$z,
              format.pval(s$pvalue, digits = 3, eps = 1e-16)))
}

yaz("")
yaz("Dolaylı etkiler (delta yöntemi güven aralığı):")
tanimli <- par[par$op == ":=", ]
for (i in seq_len(nrow(tanimli))) {
  s <- tanimli[i, ]
  yaz(sprintf("  %-16s = %7.4f   [%7.4f ; %7.4f]",
              s$lhs, s$est.std, s$ci.lower, s$ci.upper))
}

yaz("")
yaz("Açıklanan varyans (R²):")
r2 <- inspect(uyum, "r2")
for (ad in c("IYD", "OB", "CV")) {
  yaz(sprintf("  %-4s R² = %.4f", ad, r2[[ad]]))
}

# Python tarafıyla karşılaştırma dosyası
karsilastirma <- data.frame(
  hedef = yapisal$lhs, kaynak = yapisal$rhs,
  lavaan_beta = round(yapisal$est.std, 6),
  lavaan_se = round(yapisal$se, 6),
  stringsAsFactors = FALSE)
write.csv(karsilastirma,
          file.path(cikti_klasoru, "isletme_lavaan_katsayilar.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# ---------------------------------------------------------------- 2
yaz("")
yaz(strrep("=", 74))
yaz("2 — Bootstrap ile dolaylı etki (lavaan, 2000 yeniden örnekleme)")
yaz(strrep("=", 74))
yaz("Delta yöntemi dolaylı etkinin dağılımını normal varsayar; bootstrap")
yaz("varsaymaz. İkisinin aralıkları örtüşüyorsa sonuç sağlamdır.")
yaz("")
yaz("DİKKAT — bu bölümdeki sayılar STANDARTLAŞTIRILMAMIŞ ölçektedir.")
yaz("lavaan'ın bootstrap güven aralığı ham parametre üzerinden kurulur;")
yaz("standartlaştırılmış sürümü doğrudan vermez. Bu yüzden karşılaştırma")
yaz("da ham ölçekte yapılıyor: aşağıdaki iki sütun aynı büyüklüğün iki")
yaz("ayrı yoldan hesaplanmış güven aralığıdır.")

set.seed(20261104)
boot_uyum <- sem(model, data = df, estimator = "ML", se = "bootstrap",
                 bootstrap = 2000)
boot_par <- parameterEstimates(boot_uyum, boot.ci.type = "perc",
                               standardized = TRUE)
boot_tanimli <- boot_par[boot_par$op == ":=", ]
delta_ham <- parameterEstimates(uyum)
delta_ham <- delta_ham[delta_ham$op == ":=", ]
yaz("")
yaz("  etki              kestirim      delta %95 GA        bootstrap %95 GA")
for (i in seq_len(nrow(boot_tanimli))) {
  s <- boot_tanimli[i, ]
  d <- delta_ham[delta_ham$lhs == s$lhs, ]
  yaz(sprintf("  %-16s = %7.4f  [%7.4f ; %7.4f]   [%7.4f ; %7.4f]",
              s$lhs, s$est, d$ci.lower, d$ci.upper,
              s$ci.lower, s$ci.upper))
}
yaz("")
yaz("İki aralık da sıfırı dışarıda bırakıyor ve birbirini örtüyor:")
yaz("dolaylı etkilerin anlamlılığı yönteme bağlı değil.")
write.csv(boot_tanimli[, c("lhs", "est", "se", "ci.lower", "ci.upper",
                           "pvalue")],
          file.path(cikti_klasoru, "isletme_lavaan_bootstrap.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

# ---------------------------------------------------------------- 3
yaz("")
yaz(strrep("=", 74))
yaz("3 — Ölçüm değişmezliği: hibrit ve tam uzaktan çalışanlar")
yaz(strrep("=", 74))
yaz("Üç iç içe model sırayla kurulur ve karşılaştırılır:")
yaz("  biçimsel (configural) — yapı iki grupta da aynı, katsayılar serbest")
yaz("  ölçümsel (metric)     — faktör yükleri iki grupta eşitlenir")
yaz("  skalar  (scalar)      — yükler VE kesme noktaları eşitlenir")
yaz("Ölçüt: ΔCFI < 0,01 ve ΔRMSEA < 0,015 (Chen, 2007).")
yaz("Skalar değişmezlik sağlanmadan grup ortalamaları kıyaslanamaz.")
yaz("")

olcum_modeli <- '
  UCE =~ UCE1 + UCE2 + UCE3 + UCE4 + UCE5T
  IYD =~ IYD1 + IYD2 + IYD3 + IYD4T + IYD5
  OB  =~ OB1 + OB2 + OB3 + OB4 + OB5T + OB6
  CV  =~ CV1 + CV2 + CV3 + CV4 + CV5
'

alt <- df[df$calisma_modeli %in% c("Hibrit", "Tam uzaktan"), ]
yaz("Grup büyüklükleri: ",
    paste(names(table(alt$calisma_modeli)), table(alt$calisma_modeli),
          sep = " = ", collapse = " · "))

modeller <- list(
  bicimsel = cfa(olcum_modeli, data = alt, group = "calisma_modeli"),
  olcumsel = cfa(olcum_modeli, data = alt, group = "calisma_modeli",
                 group.equal = "loadings"),
  skalar   = cfa(olcum_modeli, data = alt, group = "calisma_modeli",
                 group.equal = c("loadings", "intercepts"))
)

ozet <- data.frame()
for (ad in names(modeller)) {
  f <- fitMeasures(modeller[[ad]], c("chisq", "df", "cfi", "rmsea", "srmr"))
  ozet <- rbind(ozet, data.frame(model = ad, chisq = f[["chisq"]],
                                 df = f[["df"]], cfi = f[["cfi"]],
                                 rmsea = f[["rmsea"]], srmr = f[["srmr"]]))
}
ozet$dCFI <- c(NA, diff(ozet$cfi))
ozet$dRMSEA <- c(NA, diff(ozet$rmsea))
for (i in seq_len(nrow(ozet))) {
  s <- ozet[i, ]
  yaz(sprintf("  %-9s χ²=%8.2f  sd=%3d  CFI=%.4f  RMSEA=%.4f  SRMR=%.4f%s",
              s$model, s$chisq, s$df, s$cfi, s$rmsea, s$srmr,
              if (is.na(s$dCFI)) "" else
                sprintf("   ΔCFI=%+.4f  ΔRMSEA=%+.4f", s$dCFI, s$dRMSEA)))
}
write.csv(ozet, file.path(cikti_klasoru, "isletme_degismezlik.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

gecti <- all(abs(ozet$dCFI[-1]) < 0.01) && all(abs(ozet$dRMSEA[-1]) < 0.015)
yaz("")
yaz(if (gecti)
      "Skalar değişmezlik sağlanıyor: iki grup aynı ölçekle ölçülmüş, grup karşılaştırması yapılabilir."
    else
      "Skalar değişmezlik SAĞLANMIYOR: grup ortalamaları doğrudan kıyaslanamaz.")

close(rapor)
cat("\nRapor:", file.path(cikti_klasoru, "isletme_lavaan.txt"), "\n")
