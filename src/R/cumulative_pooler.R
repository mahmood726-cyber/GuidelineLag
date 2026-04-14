# cumulative_pooler.R - compute cumulative pooled HR per year using metafor
# Usage: Rscript cumulative_pooler.R <input.csv or .rda> <out_csv>
suppressPackageStartupMessages(library(metafor))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("Usage: Rscript cumulative_pooler.R <input> <out_csv>")
input_path <- args[1]
out_csv <- args[2]

if (endsWith(input_path, ".rda")) {
  env <- new.env()
  load(input_path, envir = env)
  obj_name <- ls(env)[1]
  df <- env[[obj_name]]
} else {
  df <- read.csv(input_path)
}

df <- df[order(df$Study.year), ]
df <- df[!is.na(df$Experimental.cases) & !is.na(df$Control.cases), ]

results <- data.frame(year = integer(), k = integer(), effect = double(),
                      se = double(), ci_lo = double(), ci_hi = double(),
                      tau2 = double(), method = character(),
                      stringsAsFactors = FALSE)

unique_years <- sort(unique(df$Study.year))
for (y in unique_years) {
  sub <- df[df$Study.year <= y, ]
  k <- nrow(sub)
  if (k < 2) next
  es <- escalc(measure = "RR",
               ai = sub$Experimental.cases, n1i = sub$Experimental.N,
               ci = sub$Control.cases, n2i = sub$Control.N)
  method <- if (k >= 5) "REML" else "PM"
  res <- tryCatch(
    rma(yi = es$yi, vi = es$vi, method = method, test = "knha"),
    error = function(e) NULL
  )
  if (is.null(res)) next
  # HKSJ Q-floor: if Q < k-1, metafor's knha can narrow; we enforce a floor by re-scaling SE.
  q_floor <- max(1, res$QE / max(1, res$k - 1))
  se_adj <- res$se * sqrt(q_floor / max(1e-12, res$QE / max(1, res$k - 1)))
  hr <- exp(res$b)
  ci_lo <- exp(res$b - qt(0.975, df = res$k - 1) * se_adj)
  ci_hi <- exp(res$b + qt(0.975, df = res$k - 1) * se_adj)
  results <- rbind(results, data.frame(
    year = y, k = k, effect = as.numeric(hr),
    se = as.numeric(se_adj),
    ci_lo = as.numeric(ci_lo), ci_hi = as.numeric(ci_hi),
    tau2 = as.numeric(res$tau2), method = method
  ))
}

dir.create(dirname(out_csv), showWarnings = FALSE, recursive = TRUE)
write.csv(results, out_csv, row.names = FALSE)
cat("wrote", nrow(results), "rows to", out_csv, "\n")
