# Internal review and repairs

This review was performed by the same AI assistant that implemented and drafted the work. It is not independent peer review or a claim of experimental validation.

1. **Joint response support was insufficient in the initial campaign — repaired by rerunning.** Separate refinement checks passed, but extending duration and image support together changed ten of 960 estimates by more than 0.05°, with a maximum of 0.16551°. The target was retained, the complete initial run was archived, and the model was extended to 1.2 seconds / extent76 / propagation32. A joint 1.5-second / extent96 check passes at 0.01273° maximum. The full scientific matrix was rerun using disjoint input namespaces. No initial estimates are pooled into final results.

2. **Reflection-domain construction cost — optimized without changing valid paths.** A conservative axial bound removes tiles that cannot lie within the radial cutoff. Six archived responses and their path counts match bit for bit after the optimization. Final full-extent independent enumeration/phase checks also pass. The release preserves the previous builder so this optimization check is reproducible without distributing a large cache.

3. **Filter-order wording — corrected without changing the computation.** SciPy prototype order four yields four second-order sections, or bandpass order eight. The final manuscript states this explicitly. The original frozen text/hashes remain intact, with `PROTOCOL_CLARIFICATIONS.md` documenting the wording correction. All source code and numerical observations used the same filter throughout.

4. **Overstated source-history and uncertainty interpretations — bounded.** Onset is a single start for a whole recording; repeated frame resets are separately labeled exploratory diagnostics. Confidence intervals resample complete records, not frames, and condition on the fixed scenes. Low/high subsets differ in placement as well as absorption. Averaging is tested on independent records and is not described as a universal asymptotic floor.

5. **Changed statistical outcomes between runs — reflected in the manuscript.** The final v2 reflected-field rounding contrast and rounding-by-reflection interaction have positive intervals. The earlier v1 intervals spanning zero are not retained as final conclusions. Final training eligibility is 49 scenes, and every reported value, figure label and table is updated to v2.

6. **Criterion and baseline scope — explicit.** The geometry bound includes shared-microphone dependence and applies to ideal arrivals, not arbitrary GCC pair errors. SRP uses continuous predicted delays and a refined angular grid with matching front-end processing. The difference between RMSE and exceedance-rate ranking is reported rather than selecting a favorable metric.

7. **Provenance and publication status — retained.** The forced 77% historical illustration, unsupported hardware timing/power claims, and unverified recording-based accuracy are excluded. Bibliographic checks distinguish abstract and full-text reading. The manuscript is labeled an unreviewed preprint for author review, with accurate assistance disclosure, self-funding, no affiliation and pending conflicts. No publication status, public DOI, affiliation, license or author approval is invented.

The final document check inspected all nine main and five supplementary PDF pages and passed the missing-reference, overflow and stale-value checks. A separate clean environment reproduced the specified reference checks, all 8,640 estimates from three complete scenes exactly, and all six main PNG figures byte for byte; the report states its scope without calling it a second full revised campaign. Any remaining author-review matters are listed in `AUTHOR_REVIEW.md`.
