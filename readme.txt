This directory holds the edpsci tool package:

(1) a subdirectory "author" with
- the EDP Sciences document class "edpsci.cls",
- the sample root file "edpsci_author_template.tex",
with preset class options, packages and coding examples;

These are the special commands we should follow before \maketitle:
- \institute ==> Address
- \abstract ==> Abstract
- \keywords ==> Keywords
- \subclass ==> Classifications
- \abstracttrans ==> Translated abstract
- \keywordstrans ==> Translated keyword

Tip: Copy all these files to your working directory, run LaTeX
and produce your own example *.dvi file; rename the template files as
you see fit and use them for your own input.

(2) Special elements 
- \acknowtext ==> Acknowledgements
- \glossary ==> Glossary
- \appendix ==> Appendix
- \funding ==> Funding
- \conflict ==> Conflict of Interest
- \dataavailability ==> Data Availability Statement
- \authorcontrib ==> Authors Contributions Statement
- \ethics ==> Ethical Approval
- \informedconsent ==> Informed Consent
- \supplementary ==> Supplementary Material

(3) Fast publishing suggestions given to author added in the documentation: instruction.pdf
