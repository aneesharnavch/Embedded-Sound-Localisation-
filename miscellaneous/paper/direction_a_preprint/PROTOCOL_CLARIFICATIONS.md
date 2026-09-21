# Protocol wording clarification

The frozen protocol's phrase “fourth-order Butterworth” refers to the **prototype order** supplied to `scipy.signal.butter(4, [300, 3400], btype='bandpass', fs=48000, output='sos')`. Bandpass transformation yields four second-order sections and total filter order eight. The final manuscript uses this exact description. Source, noise, response descriptors and all experiments have always used this same implementation.

This is a wording correction, not a numerical-method change. The frozen protocol files and their original hashes are retained unchanged. No observations or comparisons need regeneration for this clarification. The source-code hashes in the result metadata unambiguously identify the filter actually applied.

The earlier duration/image-domain correction is different: it changed response support and therefore required a new protocol revision, new input namespaces, and a complete rerun. That correction and its failed/passed checks are preserved in `NUMERICAL_NOTES.md` and the supplement.
