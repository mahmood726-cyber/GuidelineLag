library(testthat)
library(metafor)

# Resolve fixture paths robustly whether invoked from repo root or tests/unit.
find_fixture <- function(rel) {
  candidates <- c(
    file.path("tests", "fixtures", rel),
    file.path("..", "fixtures", rel),
    file.path("..", "..", "tests", "fixtures", rel)
  )
  for (p in candidates) if (file.exists(p)) return(p)
  stop(sprintf("fixture not found: %s (cwd=%s)", rel, getwd()))
}

test_that("cumulative pooler reproduces direct metafor call at final year", {
  df <- read.csv(find_fixture("sample_cd_data.csv"))
  df <- df[order(df$Study.year), ]
  es <- escalc(measure = "RR",
               ai = df$Experimental.cases, n1i = df$Experimental.N,
               ci = df$Control.cases, n2i = df$Control.N)
  ref <- rma(yi = es$yi, vi = es$vi, method = "REML", test = "knha")
  ref_hr <- as.numeric(exp(ref$b))

  out <- read.csv(find_fixture("sample_cumulative.csv"))
  final <- out[nrow(out), ]
  expect_equal(final$effect, ref_hr, tolerance = 1e-6)
})
