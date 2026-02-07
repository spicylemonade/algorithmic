# Peer Review: A Hybrid Convex–Genetic Light Curve Inversion Pipeline for Automated Asteroid Shape Modeling

**Reviewer:** Automated Peer Review (Nature/NeurIPS standard)
**Date:** 2026-02-07
**Paper:** research_paper.tex / research_paper.pdf (14 pages)

---

## Criterion Scores

| # | Criterion | Score (1–5) | Comments |
|---|-----------|:-----------:|---------|
| 1 | **Completeness** | 5 | All required sections present: Abstract, Introduction, Related Work, Background & Preliminaries, Method, Experimental Setup, Results, Discussion, Conclusion, References. The paper additionally includes notation tables, algorithm pseudocode, hyperparameter tables, and an architecture diagram. Excellent structural coverage. |
| 2 | **Technical Rigor** | 4 | Methods are described with proper equations (Eqs. 1–6), algorithm pseudocode (Algorithm 1), and complete hyperparameter specification (Table 3). The forward scattering model, objective function, H-G1-G2 phase function, and shape metrics are all formally defined. Minor deduction: the L-BFGS-B citation points to Levenberg (1944), which is the Levenberg-Marquardt paper, not the L-BFGS-B paper (Byrd et al. 1995 or Zhu et al. 1997). The GA stage description lacks a fitness function equation (it presumably reuses Eq. 6 but this is not stated explicitly). The vertex reconstruction "cube-root radial scaling heuristic" is mentioned in Discussion but never formally defined in the Method section. |
| 3 | **Results Integrity** | 5 | All claims in the paper are verified against actual data files. Validation metrics in Table 4 match `results/validation_metrics.csv` exactly (Eros IoU=0.177, Itokawa=0.425, Kleopatra=0.308, Gaspra=0.352, Betulia=0.707). Sparse stress test results in Table 5 match `results/sparse_stress_test.csv` exactly. Top-10 candidates in Table 6 match `results/candidates_top50.csv`. All 10 shape model `.obj` files and spin vectors exist in `results/models/`. All 5 blind test outputs exist with convergence logs. The `blind_test_summary.json` confirms chi-squared values match. No fabricated results detected. |
| 4 | **Citation Quality** | 4 | `sources.bib` contains 22 well-formed BibTeX entries with DOIs. All key methodological references are cited: Kaasalainen & Torppa (2001), Kaasalainen et al. (2001), Bartczak & Dudzinski (2018), Durech et al. (2009, 2010, 2016), Viikinkoski et al. (2015), Carry et al. (2012), Muinonen et al. (2010), Hapke (2012), Warner (2007, 2009). `\bibliography{sources}` is correctly used. Minor issue: the Levenberg (1944) citation is used for L-BFGS-B, which is incorrect — L-BFGS-B was published by Byrd, Lu, Nocedal & Zhu (1995). The Cignoni et al. entry has year 1998 in the bib but is cited as 2003 in the tex `\citet{cignoni2003mesh}` — this is cosmetic since the key matches, but the key name is misleading. The Marquardt (1963) entry exists in the bib but is never cited in the paper. |
| 5 | **Compilation** | 5 | The PDF exists, is 14 pages, and is well-formatted. All figures render correctly (TikZ architecture diagram, 3 matplotlib figures as PDF includes). All tables are properly formatted with booktabs. All equations render correctly. The bibliography renders with natbib/plainnat. No compilation artifacts or errors visible in the PDF. Page numbering, cross-references, and hyperlinks all function. |
| 6 | **Writing Quality** | 4 | Professional academic tone throughout. Clear logical flow from problem statement through method, experiments, and discussion. The contributions are cleanly enumerated. The discussion section is notably honest about limitations (inverse crime, convex approximation limits, vertex reconstruction artifact, GA budget insufficiency). Section transitions are smooth. Minor issues: some sentences are overly long (e.g., the first sentence of the abstract is 38 words), and a few passages could be more concise. The honest acknowledgment of the "inverse crime" (Section 7.6) is commendable and adds credibility. |
| 7 | **Figure Quality** | 4 | Three publication-quality figures are included, all as PDF vector graphics. **Figure 1** (architecture): Clean TikZ diagram with proper styling, color coding, and labels. **Figure 2** (IoU bar chart): Professional styling with value annotations, color differentiation for the threshold-exceeding bar (green vs. blue), dashed threshold line, and proper axis labels. The "Acceptance threshold" label overlaps slightly with the 0.707 annotation — minor cosmetic issue. **Figure 3** (convergence): Log-scale bar chart with clear legend, proper axis labels. However, this figure is somewhat misleading — it shows Initial (Convex) and Final (GA) as nearly identical bars for all targets, because `chi_squared_convex == chi_squared_final` in the actual data (the GA did not improve chi-squared). The figure caption acknowledges this but the visual representation is suboptimal — a convergence *curve* showing iteration-by-iteration progress would be more informative than a bar chart. **Figure 4** (sparse threshold): Well-styled line plot with distinct markers and line styles per target, proper legend, threshold line, and axis labels. Good use of color palette. Overall the figures are above-average quality — not default matplotlib styling. |

---

## Summary Assessment

### Strengths

1. **Comprehensive pipeline**: The paper presents a genuinely complete system spanning data ingestion, convex inversion, genetic refinement, sparse handling, uncertainty quantification, and C++ acceleration. The 12-module architecture is well-designed.

2. **Honest reporting**: The authors do not oversell their results. IoU values of 0.18–0.71 are reported without inflating the significance, and the "inverse crime" limitation is explicitly acknowledged. The GA budget limitation is candidly discussed.

3. **Reproducibility**: All hyperparameters are specified (Table 3), the computational environment is described, all source code and shape models are released, and results files are complete and verifiable.

4. **Novel contribution**: The paper provides the first published IoU benchmarks for photometry-only shape inversion — a genuinely useful contribution to the field even though the numbers are modest.

5. **Data integrity**: Every number in every table traces back to an actual result file. No fabrication detected.

### Weaknesses

1. **Incorrect L-BFGS-B citation**: Levenberg (1944) is cited for L-BFGS-B optimization. This is a factual error that must be corrected. The correct reference is Byrd et al. (1995) "A Limited Memory Algorithm for Bound Constrained Optimization."

2. **Convergence figure is misleading**: Figure 3 shows Initial vs. Final chi-squared as a bar chart, but the actual data shows `chi_squared_convex == chi_squared_final` for all targets (the GA stage produced zero improvement). The caption mentions the GA "did not achieve further reduction" but the figure title says "Convergence" which implies improvement occurred. The text in Section 6.2 claims "The convex stage achieves significant residual reduction (7.8–305x across targets)" but the convergence data in the JSON files shows the convex history values are nearly flat (e.g., Eros goes from ~2.96e7 to ~4.63e5, which is indeed a reduction, but this is between the *initial* chi-squared and the *optimized* chi-squared within the convex stage, not shown as a trajectory). A proper iteration-by-iteration convergence curve would be much more informative.

3. **GA stage is essentially non-functional**: The blind test summary shows `chi_squared_convex == chi_squared_final` for all 5 targets, meaning Stage 2 (GA refinement) contributed zero improvement. The paper claims a "hybrid convex-genetic" pipeline but the genetic component is inert at the budget used. This undermines one of the paper's three claimed methodological pillars. The paper should either (a) demonstrate conditions under which the GA actually improves results, or (b) more prominently acknowledge this is a convex-only pipeline in practice.

4. **Abstract claim slightly misleading**: The abstract states "Sparse-only pole recovery attains <25° error at 200 observations" — but checking the data, only Kleopatra achieves 24.5° at 200 points. Eros gets 93.4° and Gaspra gets 55.4° at 200 points. The abstract should say "for favorable targets" or similar qualification. The body text (Section 6.3) is properly qualified; the abstract is not.

5. **No real-data validation**: All validation uses synthetic observations generated by the same forward model. This is acknowledged (Section 7.6) but significantly limits the paper's contribution claims. The title claim of "surpassing state-of-the-art tools" is not substantiated — the paper provides no head-to-head comparison using the same real-world data.

6. **Betulia appears in both validation and target lists**: Betulia (1580) appears in Table 2 as a validation target with known ground truth AND in Table 6 as a "previously un-modeled" candidate target. This is contradictory and should be resolved.

7. **Missing Minkowski reconstruction formalism**: The vertex reconstruction method (converting optimized facet areas to vertex positions) is a critical step but is never formally described in the Method section. It is only mentioned in the Discussion as a "cube-root radial scaling heuristic" with known problems.

---

## Verdict: **REVISE**

### Required Revisions

1. **Fix L-BFGS-B citation** (Section 4.1, line 285): Replace `\citep{levenberg1944method}` with proper Byrd et al. (1995) reference. Add the correct BibTeX entry to `sources.bib`.

2. **Qualify the abstract sparse claim**: Change "Sparse-only pole recovery attains <25° error at 200 observations" to something like "Sparse-only pole recovery attains <25° error at 200 observations for favorable target geometries (1 of 3 tested targets)."

3. **Fix or replace Figure 3**: Either (a) replace the bar chart with actual iteration-by-iteration convergence curves from the `convex_history` data in the convergence JSON files, which would be far more informative, or (b) retitle/recaption to accurately convey what is shown (initial vs. final chi-squared, not a convergence trajectory). Also, fix the caption claim about "7.8–305x reduction" — verify this against actual initial/final values in the convergence histories.

4. **Address GA ineffectiveness more prominently**: Add a sentence to the abstract acknowledging the GA stage did not improve results at the budget used. In Section 6.2, explicitly state that `chi_squared_final == chi_squared_convex` for all targets and explain why (budget too small by 500x).

5. **Remove Betulia from the candidate list** (Table 6) or explain why a validation target with known ground truth is listed as "previously un-modeled."

6. **Add vertex reconstruction method**: In Section 4.1, after Algorithm 1 line 11 ("Reconstruct vertex positions from a* via radial scaling"), add a subsection or paragraph formally describing the cube-root radial scaling heuristic used for vertex reconstruction.

7. **Add L-BFGS-B reference to sources.bib**:
   ```bibtex
   @article{byrd1995limited,
     author  = {Byrd, Richard H. and Lu, Peihuang and Nocedal, Jorge and Zhu, Ciyou},
     title   = {A Limited Memory Algorithm for Bound Constrained Optimization},
     journal = {SIAM Journal on Scientific Computing},
     year    = {1995},
     volume  = {16},
     number  = {5},
     pages   = {1190--1208},
     doi     = {10.1137/0916069}
   }
   ```

### Recommended (Non-blocking) Improvements

- Add error bars or confidence intervals to Tables 4 and 5 using the bootstrap uncertainty quantification described in Section 4.4 (this capability exists in the pipeline but results are not reported).
- Figure 2: Fix the slight text overlap between "Acceptance threshold" label and the "0.707" annotation on the Betulia bar.
- Consider adding a table showing per-target inversion timing breakdown (convex stage vs. GA stage vs. mesh upsampling).
- The unused `marquardt1963algorithm` bib entry should be removed from `sources.bib`, or cited where L-M is mentioned.

---

**Overall Assessment**: This is a solid technical contribution with honest reporting, complete reproducibility artifacts, and genuine novelty in providing IoU benchmarks for photometry-only inversion. The required revisions are straightforward and addressable. The main structural issue — the non-functional GA stage — needs transparent acknowledgment rather than removal, as it represents a useful negative result. After addressing the above items, this paper would meet publication standards.
