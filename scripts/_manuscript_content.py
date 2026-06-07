# -*- coding: utf-8 -*-
"""
New manuscript content for the merged LRE submission:
Title page, Abstract, Keywords, Introduction (1), Discussion (7), Conclusion (8),
Declarations, merged & deduplicated References (Springer author-date), Appendix A.

Inline italics are marked with the sentinels [[I]] ... [[/I]] and rendered as
italic runs by the assembler. Citations are already in Springer author-date
style: (Author Year), (Author and Author Year), (Author et al. Year).
"""

TITLE = ("How Well Do State-of-the-Art Large Language Models Write Ancient Greek? "
         "A Chunk-Level Stylometric Resource and Evaluation")

AUTHOR = "George K. Mikros"

# Title-page lines beneath the author name. Bracketed items are placeholders the
# author must confirm before submission.
AFFIL_LINES = [
    "[Affiliation — department, institution, city, country to be confirmed]",
    "ORCID: [0000-0000-0000-0000 — to be confirmed]",
    "Corresponding author. E-mail: [email to be confirmed]",
]

ABSTRACT = (
    "We release a chunk-level corpus of human Attic-orator prose paired with rewrites produced by "
    "two state-of-the-art large language models, GPT-5.5 and Claude 4.8, under two prompting regimes "
    "— a close-rewrite (Restricted) regime and a meaning-preserving but flexible (Free) regime — "
    "together with an older-generation baseline that supports a longitudinal view. The resource comprises "
    "6,610 chunk-level texts (1,322 human and 5,288 machine) spanning the ten canonical Attic orators, "
    "with a datasheet, the generation prompts and the full analysis code. Using it, we evaluate how closely "
    "the generated Ancient Greek reproduces human style across 84 stylometric features and two families of "
    "neural document embeddings, with linear mixed-effects models that respect the nesting of chunks within "
    "documents and authors. Human and machine Ancient Greek differ on a majority of features (36 of 69 "
    "estimable features are significant after false-discovery-rate correction), but every effect is small "
    "(all Cohen’s [[I]]d[[/I]] below 0.34): the models write denser, lexically richer and more finely "
    "segmented prose, while the orators favour longer, more periphrastic sentences. The pooled contrast "
    "conceals a sharp gradient — model choice and especially prompting regime move the texts at least as "
    "much as the human/machine distinction — so that the most constrained configuration (Claude 4.8, "
    "Restricted) is statistically indistinguishable from genuine Attic oratory under a stylometric classifier, "
    "whereas the freest (GPT-5.5, Free) is trivially detectable. State-of-the-art models can therefore write "
    "stylometrically human-like Ancient Greek, but only under prompting that constrains length, segmentation "
    "and register."
)

KEYWORDS = [
    "Ancient Greek",
    "Stylometry",
    "Large language models",
    "Language resources",
    "Machine-generated text detection",
    "Computational philology",
]

# Provenance passage inserted as a second paragraph of Section 3.1 (Source corpus).
PROVENANCE_31 = (
    "These texts derive from the Perseus Digital Library (Crane n.d.), specifically its openly released "
    "TEI XML corpus PerseusDL/canonical-greekLit, from which we extracted running plain text. Each source "
    "document is named by its canonical Thesaurus Linguae Graecae (TLG) author identifier — Aeschines 0026, "
    "Andocides 0027, Antiphon 0028, Demosthenes 0014, Dinarchus 0029, Hyperides 0030, Isaeus 0017, "
    "Isocrates 0010, Lycurgus 0034 and Lysias 0540 — and the extracted text is full polytonic Greek in the "
    "Perseus orthographic convention, which we normalised before feature extraction (Section 3.4). The "
    "Perseus Greek texts are distributed under the Creative Commons Attribution-ShareAlike 4.0 International "
    "(CC BY-SA 4.0) licence; the released human-derived chunks therefore inherit this share-alike "
    "condition, as recorded in the accompanying datasheet."
)

# ---------------------------------------------------------------------------
# Each block is a (level, text) tuple. level in {h1, h2, body}.
# ---------------------------------------------------------------------------

INTRODUCTION = [
    ("h1", "1  Introduction"),
    ("body",
     "Large language models now produce fluent, controllable prose in dozens of languages, and their "
     "few-shot and instruction-following abilities make it possible to elicit text in a target language and "
     "register through prompting alone (Brown et al. 2020; Bommasani et al. 2021; Wei et al. 2022). Their "
     "competence is, however, distributed very unevenly: performance remains markedly weaker for low-resource "
     "languages (Zhu et al. 2024), and the historical languages of the scholarly canon — attested only in a "
     "finite, centuries-old corpus and largely absent from everyday web text — are among the most data-scarce "
     "of all. Ancient Greek is the paradigm case. It is at once a high-prestige object of study, with a "
     "continuous philological tradition and a large readership of students and scholars, and a genuinely "
     "low-resource target for natural-language processing. The question this paper addresses is not whether a "
     "model can read or translate Ancient Greek, which a growing body of work already examines, but whether it "
     "can [[I]]write[[/I]] it: produce original prose that reproduces the measurable stylistic profile of a "
     "specific historical register."),
    ("body",
     "The question matters in three distinct communities. For classical pedagogy and the construction of "
     "language resources, models that generate stylistically faithful Greek would offer a new source of graded "
     "reading material, exercises and — most consequentially for natural-language processing — synthetic data "
     "to augment the small annotated corpora on which Ancient Greek tools are trained (Bamman and Crane 2011; "
     "Vatri and McGillivray 2018; Keersmaekers 2021). For stylometry and authorship analysis, the same "
     "capability is a challenge rather than an opportunity: if a model can write convincingly in the manner of "
     "a fourth-century orator, the provenance of digital text becomes harder to establish, and the detection "
     "of machine-generated text — already a fast-moving field for modern English (Crothers et al. 2023; "
     "Tang et al. 2024) — must be extended to historical languages and to the forensic questions that "
     "classics will increasingly face (Mikros 2025b). And for the study of the models themselves, a historical "
     "register with a rich, well-described stylistic signature is an unusually demanding and well-instrumented "
     "testbed for controllability: how far, and under what prompting, a general-purpose model can be steered "
     "toward a precise stylistic target."),
    ("body",
     "Ancient Greek is also an informative case because it is hard in ways that bear directly on measurement. "
     "Its rich fusional morphology and relatively free word order push much of its stylistic signal below the "
     "lexical surface — into case and mood distributions, dependency structure and particle usage — where "
     "authorship signals are correspondingly harder to recover than in less inflected languages (Juola et al. "
     "2019). Syntactic stylometry over dependency treebanks can nonetheless identify the authors of short Greek "
     "texts without recourse to vocabulary (Gorman 2020), which makes morphosyntactic features the natural "
     "instrument for a human-versus-machine comparison. The most directly relevant precedent is cautionary: an "
     "earlier-generation model’s attempts to imitate individual authors stayed measurably separable from genuine "
     "human writing (Mikros 2025a). Whether the latest generation of models closes that gap, and under what "
     "prompting, remains an open question."),
    ("body",
     "It is open in part because the evidence needed to answer it does not yet exist. Prior work concentrates "
     "on understanding or translating historical text, or on imitating modern authors; no study, to our "
     "knowledge, evaluates at corpus scale how closely contemporary large language models reproduce the style "
     "of a historical language, using a statistical design that respects the nested structure of the data and "
     "accompanied by a released resource that others can reuse. This paper is built to fill that gap."),
    ("body",
     "We assemble and release a chunk-level parallel corpus of human Attic-orator prose and state-of-the-art "
     "machine rewrites, and we use it to evaluate stylistic fidelity rigorously. The human side comprises 119 "
     "texts from the ten canonical Attic orators, segmented into 1,322 length-controlled chunks. Each chunk is "
     "rewritten by two current models, GPT-5.5 and Claude 4.8, under two prompting regimes — a Restricted "
     "regime that asks for a close, length- and order-preserving rewrite, and a Free regime that preserves "
     "meaning but allows idiomatic licence — yielding a balanced two-by-two design and a corpus of 6,610 "
     "chunk-level texts. The resource additionally includes an older-generation baseline (GPT-4o and Claude "
     "3.5) to support future longitudinal study of model progress; because that material is anchored on whole "
     "documents rather than re-chunked, it is released with the corpus but is not analysed here. We compare "
     "human and machine prose across 84 stylometric and linguistic features and two families of "
     "Ancient-Greek neural document embeddings, using linear mixed-effects models with random intercepts for "
     "author and document, false-discovery-rate control, bootstrap confidence intervals, and author-grouped "
     "classifiers."),
    ("body",
     "Three research questions organise the evaluation. RQ1: how closely does the Ancient Greek produced by "
     "state-of-the-art models match the style of the human orators, measured both by interpretable stylometric "
     "features and by neural embeddings? RQ2: how is that fidelity modulated by the choice of model and, "
     "especially, by the prompting regime? RQ3: which authors and which linguistic features are hardest for "
     "the models to reproduce, and what does the residual difference consist of?"),
    ("body",
     "In answering them the paper makes four contributions. First, it releases a documented language resource "
     "— the parallel human/machine corpus, a datasheet, the generation prompts, and the complete "
     "feature-extraction, embedding and analysis pipeline — designed for reuse in stylometry, "
     "machine-generated-text detection and historical-language natural-language processing. Second, it "
     "introduces a chunk-level methodology that solves the length-reproduction problem of whole-document "
     "rewriting and fixes the segmentation granularity through an explicit calibration experiment. Third, it "
     "provides a rigorous, reproducible evaluation that respects the nested and heavily imbalanced structure "
     "of the oratorical canon through author-level random effects and author-grouped cross-validation. Fourth, "
     "it reports a clear empirical result: the difference between human and machine Ancient Greek is pervasive "
     "but uniformly small, and it is strongly modulated by prompting, to the point where the most constrained "
     "configuration is statistically indistinguishable from genuine Attic oratory while the freest is "
     "trivially detectable."),
    ("body",
     "The remainder of the paper is organised as follows. Section 2 reviews the five research strands on which "
     "the study builds. Sections 3 to 5 describe the resource — corpus construction, feature extraction and "
     "document embeddings, and the evaluation methodology. Section 6 reports the results, and Sections 7 and 8 "
     "discuss their implications and conclude."),
]

DISCUSSION = [
    ("h1", "7  Discussion"),
    ("h2", "7.1  A small but coherent residual difference"),
    ("body",
     "The central result is one of magnitude. Across the 69 estimable stylometric features, 36 separate human "
     "from machine prose after false-discovery-rate correction, yet no effect exceeds |[[I]]d[[/I]]| = 0.34 and "
     "the great majority are far smaller (Section 6.2). A difference that is statistically pervasive but "
     "uniformly small is exactly the signature of two text populations drawn from nearly — but not quite — the "
     "same stylistic distribution. The residual is not noise, however: it is a coherent stylistic axis. The "
     "models write denser, more lexically varied and more finely segmented prose — shorter sentences, more "
     "sentences, higher lexical density and type-token ratios, longer mean dependency distance — while the "
     "orators write longer, more periphrastic sentences with greater reliance on auxiliary and copular "
     "constructions. Even when dressed in Attic morphology and vocabulary, in other words, machine prose "
     "retains a faint trace of a more essayistic packaging of information: it distributes content over more, "
     "tighter clausal units than the periodic style of the human orators. This is a subtle but interpretable "
     "fingerprint, and it is consistent with what one would expect of models whose default register is shaped "
     "by modern expository text."),
    ("h2", "7.2  Stylistic fidelity is steerable: prompt and model outweigh the human/machine divide"),
    ("body",
     "The pooled human-versus-machine contrast conceals a much sharper internal gradient. Partitioning the "
     "machine texts by system and by prompt yields more discriminating features (52 and 54, respectively) than "
     "the 36 that distinguish human from machine overall: the choice of model, and above all the prompting "
     "regime, moves the texts at least as much as the human/machine distinction itself. The direction is "
     "consistent across every lens we apply. The Restricted prompt, which constrains length, clause order and "
     "segmentation, pulls the machine texts toward human values on exactly the features that carry the residual "
     "difference, and Claude 4.8 sits closer to the human authors than GPT-5.5. The convergence is the "
     "strongest part of the evidence: a supervised classifier, the morphological Jensen-Shannon divergence, a "
     "composite separation score, and an unsupervised silhouette all rank the four conditions identically, "
     "from the trivially detectable GPT-5.5 Free (classifier AUROC 0.95) to the near-indistinguishable "
     "Claude 4.8 Restricted (AUROC 0.52, that is, chance). Because four methodologically independent measures "
     "agree, the gradient is a property of the generated texts and not an artefact of any single modelling "
     "choice. The practical implication is considerable: the detectability of machine Ancient Greek is not a "
     "fixed capability ceiling but a quantity that can be dialled up or down by the prompt. State-of-the-art "
     "models can already produce Attic prose that a stylometric classifier cannot distinguish from the genuine "
     "article — but only when the prompt actively constrains them toward the source’s length, segmentation and "
     "register; left free, they revert to the denser, more segmented profile that gives them away."),
    ("h2", "7.3  What the two views capture, and which styles resist imitation"),
    ("body",
     "Neural document embeddings are slightly more discriminative than the interpretable stylometric features "
     "(AUROC 0.745 for Ancient-Greek-BERT against 0.701 for the feature set), consistent with their capturing "
     "distributional lexical and contextual regularities that the hand-designed features do not encode; but "
     "both remain far below ceiling, and the two views agree on the overall picture of heavy overlap. The "
     "complementarity, rather than the superiority of either, is the methodological lesson, and it echoes the "
     "finding that stylometric and transformer representations are most powerful in combination for "
     "machine-generated-text detection (Mikros et al. 2023). The residual difference is concentrated, finally, "
     "in two places that are mutually illuminating. Morphologically, it lives in verbal mood far more than in "
     "case — the two diverge by an order of magnitude and are essentially uncorrelated — so the last thing the "
     "models get wrong is the distribution of moods, the most pragmatically and rhetorically loaded part of "
     "the Greek verb. By author, the models approach the plainer styles most closely and the most marked "
     "styles least: Isocrates, with his long, periodic, rhythmically governed sentences, and Antiphon, the "
     "earliest and most idiosyncratic of the orators, sit at the edge of the reachable stylistic space, whereas "
     "the plainer orators cluster near its centre. Tellingly, the authors with the largest residual mood "
     "divergence — Hyperides and Lysias — are among the most under-represented in the surviving canon, which "
     "points to scarcity of training signal, rather than any intrinsic unreachability of the style, as the "
     "driver of the residual. This is an encouraging diagnosis: it implies that the gap is a function of data "
     "and constraint, not of a hard limit on what the models can imitate."),
    ("h2", "7.4  Implications"),
    ("body",
     "For classical studies and language resources, the result is enabling but qualified. Under close-rewrite "
     "prompting, the best current model produces Attic prose whose stylometric profile is, on the measures used "
     "here, indistinguishable from human oratory — which makes machine generation a credible source of "
     "synthetic data for augmenting the small corpora that Ancient Greek tools depend on, and a plausible aid "
     "for producing register-appropriate examples in teaching. The qualification is that fidelity is highest "
     "precisely when the model is given a human passage to follow closely; the further the prompt departs from "
     "the source, the more the characteristic machine profile re-emerges, and the morphological evidence shows "
     "that mood — the rhetorically decisive part of the verb — is the first thing to drift. Generated Greek is "
     "therefore not a substitute for the philological record, and should be labelled and handled as the "
     "derived, model-conditioned material it is, not as a gold edition."),
    ("body",
     "For machine-generated-text detection and the forensic linguistics of historical languages, the study "
     "offers both a method and a warning. The method is to treat the cross-validated detectability of a "
     "human-versus-machine classifier not as an end in itself but as a graded, interpretable measure of "
     "stylistic distance, and to read it alongside distributional divergences and embedding geometry. The "
     "warning is that detectability is controllable and, for the best model under constraint, can be driven to "
     "chance: robust detection in this setting cannot rely on a single signal, and is vulnerable — as it is "
     "for modern English (Sadasivan et al. 2023) — to the very prompting strategies that improve fidelity. As "
     "generative models become part of the classicist’s toolkit, questions of authenticity and provenance that "
     "the field has previously confined to antiquity will arise for contemporary digital text as well "
     "(Mikros 2025b)."),
    ("body",
     "For stylometric methodology, the study is a reminder that the structure of the data must be built into "
     "the evaluation. The oratorical canon is dominated by a single author — Demosthenes supplies half of all "
     "human chunks — and treating chunks as independent would let that imbalance, and the memorisation of "
     "individual authors, inflate any apparent separation. Author-level random effects and author-grouped "
     "cross-validation are what keep the detectability estimates honest, and the same precautions will be "
     "necessary for any human-versus-machine comparison in a heavily imbalanced, morphologically rich corpus, "
     "in Greek or beyond."),
    ("h2", "7.5  Limitations"),
    ("body",
     "Several limitations bound these conclusions. First, the corpus is confined to a single genre and "
     "register, Attic prose oratory; we make no claim about verse, dialogue, technical prose, or other dialects "
     "and periods, where both the human stylistic targets and the models’ competence may differ. Second, the "
     "design measures faithful [[I]]rewriting[[/I]] rather than free composition: every machine text is "
     "conditioned on a specific human source that supplies its content and anchors its length, so the results "
     "speak to how closely models can follow a model passage, not to how well they would compose Attic prose "
     "unprompted. Third, and relatedly, the orators are canonical and almost certainly present in the models’ "
     "pre-training data, so high fidelity may partly reflect recall of memorised material rather than "
     "generative competence; the two cannot be fully separated here, and the very strong performance of the "
     "constrained configurations should be read with this in mind. Fourth, the morphosyntactic features are "
     "produced by an automatic parser trained on human treebank Greek (the Stanza PROIEL model), which may tag "
     "machine text with systematic, label-dependent error; we mitigate this by computing the lexical and "
     "length features from an independent tokenizer and by reporting only small, false-discovery-rate-"
     "controlled effects, but a residue of tagging artefact cannot be excluded. Fifth, our fidelity measures "
     "are stylometric and distributional, not judgements of grammaticality, idiom or philological acceptability "
     "by expert readers; a human evaluation in the spirit of recent expert assessments of machine-translated "
     "technical Greek (Zainaldin et al. 2026) would complement them. Finally, the longitudinal axis is enabled "
     "by the released baseline but not analysed here, and the embedding analysis compresses each encoder to "
     "fifty principal components; neither choice affects the cross-sectional conclusions but both bound their "
     "scope."),
    ("h2", "7.6  Future work"),
    ("body",
     "These limitations map directly onto a programme of future work: extending the resource and the "
     "evaluation to other genres, dialects and periods of Greek and to other historical languages; comparing "
     "source-anchored rewriting with free, prompt-only composition; commissioning expert philological "
     "evaluation of the generated prose alongside the stylometric measures; carrying out the longitudinal "
     "model-progress analysis that the released baseline supports; and pursuing a targeted error analysis of "
     "verbal mood, the feature on which the residual human/machine difference is most concentrated. The "
     "corpus, code and prompts are released to make each of these directly actionable."),
]

CONCLUSION = [
    ("h1", "8  Conclusion"),
    ("body",
     "This paper set out to determine how closely state-of-the-art large language models can write Ancient "
     "Greek, and to leave behind the resource needed to keep asking the question. We assembled and released a "
     "chunk-level parallel corpus of human Attic-orator prose and machine rewrites — 6,610 texts spanning the "
     "ten canonical orators, produced by GPT-5.5 and Claude 4.8 under close-rewrite and free prompting, with "
     "an older-generation baseline for longitudinal study — together with a datasheet, the generation prompts, "
     "and the full feature-extraction, embedding and analysis pipeline. Using a statistical design that "
     "respects the nested, heavily imbalanced structure of the oratorical canon, we evaluated stylistic "
     "fidelity across 84 stylometric features and two families of Ancient-Greek document embeddings."),
    ("body",
     "The evaluation yields a clear and coherent answer. Human and machine Ancient Greek differ on a majority "
     "of features, but every difference is small: the models write denser, lexically richer and more finely "
     "segmented prose, while the orators favour longer, more periphrastic sentences. This faint residual is why "
     "dimensionality reduction and clustering fail to separate the two and why both stylometric and embedding "
     "classifiers plateau in the 0.70-0.75 range of area under the ROC curve. Yet the pooled comparison "
     "conceals a sharp gradient: the choice of model and, above all, of prompting regime moves the texts at "
     "least as much as the human/machine distinction itself, and four independent measures agree that fidelity "
     "rises from a trivially detectable GPT-5.5 under free prompting to a Claude 4.8 under close-rewrite "
     "prompting that a stylometric classifier cannot distinguish from genuine Attic oratory. State-of-the-art "
     "models can therefore write stylometrically human-like Ancient Greek — but stylistic fidelity is a "
     "steerable quantity, achieved only when the prompt constrains length, segmentation and register, and the "
     "residual difference, where it survives, concentrates in verbal mood and in the most marked authorial "
     "styles."),
    ("body",
     "Beyond the specific finding, the study offers the wider community a reusable resource and a template for "
     "evaluating historical-language generation rigorously: detectability read as graded stylistic distance, "
     "triangulated across interpretable features and neural embeddings, under a design that takes the structure "
     "of the corpus seriously. We hope the released corpus and pipeline will support the longitudinal, "
     "cross-genre and human-evaluation studies that the present cross-sectional results invite, in Greek and in "
     "other languages whose style is worth measuring."),
]

# Declarations. Bracketed text marks author-confirmable placeholders.
DECLARATIONS = [
    ("h1", "Declarations"),
    ("h2", "Funding"),
    ("body",
     "[To be confirmed.] The author received no specific grant for this research from any funding agency in "
     "the public, commercial or not-for-profit sectors."),
    ("h2", "Competing interests"),
    ("body", "The author declares no competing interests."),
    ("h2", "Ethics approval"),
    ("body",
     "Not applicable. The study did not involve human participants, their identifiable data, or animals; the "
     "human texts are published works of the classical canon."),
    ("h2", "Consent to participate and consent for publication"),
    ("body", "Not applicable."),
    ("h2", "Data availability"),
    ("body",
     "The resource — the human chunks and machine rewrites, the per-chunk feature matrix, the document "
     "embeddings and all analysis artefacts — is documented by an accompanying datasheet and will be archived "
     "in a public repository with a citable DOI upon acceptance, at which point the repository will be made "
     "public. The human source texts derive from the Perseus Digital Library (Crane n.d.) under the Creative "
     "Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) licence, and the released "
     "human-derived chunks inherit this share-alike condition; the code is released under the MIT licence, and "
     "the licensing of every released component is recorded in the accompanying datasheet. The materials are "
     "available to the editors and reviewers on request during peer review."),
    ("h2", "Code availability"),
    ("body",
     "The complete pipeline (chunking, generation, orthographic normalization, feature extraction, embeddings "
     "and the numbered analyses) is released under the MIT licence in the same repository as the data."),
    ("h2", "Author contributions"),
    ("body",
     "G. K. Mikros is the sole author and conceived the study, built the corpus and software, performed the "
     "analyses, and wrote the manuscript."),
    ("h2", "Use of large language models"),
    ("body",
     "Large language models are the object of study in this paper: GPT-5.5 and Claude 4.8, together with the "
     "older-generation GPT-4o and Claude 3.5 baseline, were used to generate the machine Ancient Greek texts "
     "analysed here, exactly as described in Section 3. [To be confirmed by the author.] Beyond their role as "
     "the object of study, generative AI tools were used to assist with language editing and the drafting of "
     "portions of the manuscript; the author reviewed and verified all such content and takes full "
     "responsibility for it. No AI system is listed as an author, in line with the journal’s authorship "
     "policy."),
]

# ---------------------------------------------------------------------------
# Merged, deduplicated reference list in Springer author-date house style.
# 59 unique entries (51 from the literature review + 8 method/tool references;
# the 4 overlaps are collapsed). Alphabetised by first author.
# ---------------------------------------------------------------------------
REFERENCES = [
    "Argamon S (2008) Interpreting Burrows’s Delta: geometric and probabilistic foundations. Literary and Linguistic Computing 23(2):131–147. https://doi.org/10.1093/llc/fqn003",
    "Bamman D, Burns PJ (2020) Latin BERT: a contextual language model for classical philology. arXiv:2009.10053",
    "Bamman D, Crane G (2011) The Ancient Greek and Latin dependency treebanks. In: Sporleder C, van den Bosch A, Zervanou K (eds) Language technology for cultural heritage. Springer, Berlin, pp 79–98. https://doi.org/10.1007/978-3-642-20227-8_5",
    "Benjamini Y, Hochberg Y (1995) Controlling the false discovery rate: a practical and powerful approach to multiple testing. Journal of the Royal Statistical Society: Series B 57(1):289–300",
    "Bommasani R et al (2021) On the opportunities and risks of foundation models. arXiv:2108.07258",
    "Brown TB et al (2020) Language models are few-shot learners. In: Advances in neural information processing systems 33. Curran Associates, Red Hook, NY, pp 1877–1901",
    "Burrows J (2002) ‘Delta’: a measure of stylistic difference and a guide to likely authorship. Literary and Linguistic Computing 17(3):267–287. https://doi.org/10.1093/llc/17.3.267",
    "Celano GGA (2024) A state-of-the-art morphosyntactic parser and lemmatizer for Ancient Greek. arXiv:2410.12055",
    "Cohen J (1988) Statistical power analysis for the behavioral sciences, 2nd edn. Lawrence Erlbaum Associates, Hillsdale, NJ",
    "Crane GR (ed) (n.d.) Perseus Digital Library. Tufts University, Medford, MA. Greek texts of the Attic orators from the PerseusDL/canonical-greekLit repository, https://github.com/PerseusDL/canonical-greekLit, licensed under CC BY-SA 4.0",
    "Crothers EN, Japkowicz N, Viktor HL (2023) Machine-generated text: a comprehensive survey of threat models and detection methods. IEEE Access 11:70977–71002. https://doi.org/10.1109/ACCESS.2023.3294090",
    "Eder M, Rybicki J, Kestemont M (2016) Stylometry with R: a package for computational text analysis. The R Journal 8(1):107–121. https://doi.org/10.32614/RJ-2016-007",
    "Evert S, Proisl T, Jannidis F, Reger I, Pielström S, Schöch C, Vitt T (2017) Understanding and explaining Delta measures for authorship attribution. Digital Scholarship in the Humanities 32(Suppl 2):ii4–ii16. https://doi.org/10.1093/llc/fqx023",
    "Gehrmann S, Strobelt H, Rush AM (2019) GLTR: statistical detection and visualization of generated text. In: Proceedings of the 57th annual meeting of the Association for Computational Linguistics: system demonstrations. Association for Computational Linguistics, pp 111–116. https://doi.org/10.18653/v1/P19-3019",
    "Gorman R (2020) Author identification of short texts using dependency treebanks without vocabulary. Digital Scholarship in the Humanities 35(4):812–825. https://doi.org/10.1093/llc/fqz070",
    "Gorman VB, Gorman RJ (2016) Approaching questions of text reuse in Ancient Greek using computational syntactic stylometry. Open Linguistics 2(1):500–510. https://doi.org/10.1515/opli-2016-0026",
    "Grieve J (2007) Quantitative authorship attribution: an evaluation of techniques. Literary and Linguistic Computing 22(3):251–270. https://doi.org/10.1093/llc/fqm020",
    "Guo B et al (2023) How close is ChatGPT to human experts? Comparison corpus, evaluation, and detection. arXiv:2301.07597",
    "Hämäläinen M (2024) DAG: dictionary-augmented generation for disambiguation of sentences in endangered Uralic languages using ChatGPT. In: Proceedings of the 9th international workshop on computational linguistics for Uralic languages. Association for Computational Linguistics, pp 36–40",
    "Haug DTT, Jøhndal ML (2008) Creating a parallel treebank of the old Indo-European Bible translations. In: Proceedings of the second workshop on language technology for cultural heritage data (LaTeCH 2008). European Language Resources Association, pp 27–34",
    "Holmes DI (1998) The evolution of stylometry in humanities scholarship. Literary and Linguistic Computing 13(3):111–117. https://doi.org/10.1093/llc/13.3.111",
    "Ippolito D, Duckworth D, Callison-Burch C, Eck D (2020) Automatic detection of generated text is easiest when humans are fooled. In: Proceedings of the 58th annual meeting of the Association for Computational Linguistics. Association for Computational Linguistics, pp 1808–1822. https://doi.org/10.18653/v1/2020.acl-main.164",
    "Jawahar G, Abdul-Mageed M, Lakshmanan LVS (2020) Automatic detection of machine generated text: a critical survey. In: Proceedings of the 28th international conference on computational linguistics. International Committee on Computational Linguistics, pp 2296–2309. https://doi.org/10.18653/v1/2020.coling-main.208",
    "Johnson KP, Burns PJ, Stewart J, Cook T, Besnier C, Mattingly WJB (2021) The Classical Language Toolkit: an NLP framework for pre-modern languages. In: Proceedings of the 59th annual meeting of the Association for Computational Linguistics and the 11th international joint conference on natural language processing: system demonstrations. Association for Computational Linguistics, pp 20–29. https://doi.org/10.18653/v1/2021.acl-demo.3",
    "Juola P (2006) Authorship attribution. Foundations and Trends in Information Retrieval 1(3):233–334. https://doi.org/10.1561/1500000005",
    "Juola P, Mikros GK, Vinsick S (2019) A comparative assessment of the difficulty of authorship attribution in Greek and in English. Journal of the Association for Information Science and Technology 70(1):61–70. https://doi.org/10.1002/asi.24073",
    "Keersmaekers A (2021) The GLAUx corpus: methodological issues in designing a long-term, diverse, multi-layered corpus of Ancient Greek. In: Proceedings of the 2nd international workshop on computational approaches to historical language change 2021. Association for Computational Linguistics, pp 39–50. https://doi.org/10.18653/v1/2021.lchange-1.6",
    "Keersmaekers A, Mercelis W (2024) Adapting transformer models to morphological tagging of two highly inflectional languages: a case study on Ancient Greek and Latin. In: Proceedings of the 1st workshop on machine learning for ancient languages (ML4AL 2024). Association for Computational Linguistics, pp 165–176. https://doi.org/10.18653/v1/2024.ml4al-1.17",
    "Keersmaekers A, Mercelis W, Swaelens C, Van Hal T (2019) Creating, enriching and valorizing treebanks of Ancient Greek. In: Proceedings of the 18th international workshop on treebanks and linguistic theories (SyntaxFest 2019). Association for Computational Linguistics, pp 109–117. https://doi.org/10.18653/v1/W19-7812",
    "Kestemont M, Stover J, Koppel M, Karsdorp F, Daelemans W (2016) Authenticating the writings of Julius Caesar. Expert Systems with Applications 63:86–96. https://doi.org/10.1016/j.eswa.2016.06.029",
    "Kirchenbauer J, Geiping J, Wen Y, Katz J, Miers I, Goldstein T (2023) A watermark for large language models. In: Proceedings of the 40th international conference on machine learning, PMLR, vol 202, pp 17061–17084",
    "Koppel M, Schler J, Argamon S (2009) Computational methods in authorship attribution. Journal of the American Society for Information Science and Technology 60(1):9–26. https://doi.org/10.1002/asi.20961",
    "Lin J (1991) Divergence measures based on the Shannon entropy. IEEE Transactions on Information Theory 37(1):145–151",
    "Manousakis N (2020) Prometheus Bound: a separate authorial trace in the Aeschylean corpus. Trends in classics – supplementary volumes, vol 98. De Gruyter, Berlin. https://doi.org/10.1515/9783110687675",
    "McCarthy PM, Jarvis S (2010) MTLD, vocd-D, and HD-D: a validation study of sophisticated approaches to lexical diversity assessment. Behavior Research Methods 42(2):381–392",
    "McInnes L, Healy J, Melville J (2018) UMAP: uniform manifold approximation and projection for dimension reduction. arXiv:1802.03426",
    "Michaelson S, Morton AQ (1972) The new stylometry: a one-word test of authorship for Greek writers. The Classical Quarterly 22(1):89–102. https://doi.org/10.1017/S0009838800034054",
    "Mikros GK (2025a) Beyond the surface: stylometric analysis of GPT-4o’s capacity for literary style imitation. Digital Scholarship in the Humanities 40(2):587–600. https://doi.org/10.1093/llc/fqaf035",
    "Mikros GK (2025b) Large language models and forensic linguistics: navigating opportunities and threats in the age of generative AI. arXiv:2512.06922",
    "Mikros GK, Koursaris A, Bilianos D, Markopoulos G (2023) AI-writing detection using an ensemble of transformers and stylometric features. In: Proceedings of the Iberian languages evaluation forum (IberLEF 2023), CEUR workshop proceedings, vol 3496. CEUR-WS. https://ceur-ws.org/Vol-3496/autextification-paper9.pdf",
    "Mikros GK, Perifanos K (2013) Authorship attribution in Greek tweets using author’s multilevel n-gram profiles. In: Analyzing microtext: papers from the 2013 AAAI spring symposium, technical report SS-13-01. AAAI Press, pp 17–23",
    "Mireshghallah N, Mattern J, Gao S, Shokri R, Berg-Kirkpatrick T (2024) Smaller language models are better zero-shot machine-generated text detectors. In: Proceedings of the 18th conference of the European chapter of the Association for Computational Linguistics (volume 2: short papers). Association for Computational Linguistics, pp 278–293. https://doi.org/10.18653/v1/2024.eacl-short.25",
    "Mitchell E, Lee Y, Khazatsky A, Manning CD, Finn C (2023) DetectGPT: zero-shot machine-generated text detection using probability curvature. In: Proceedings of the 40th international conference on machine learning, PMLR, vol 202, pp 24950–24962",
    "Pavlopoulos J, Konstantinidou M (2023) Computational authorship analysis of the Homeric poems. International Journal of Digital Humanities 5(1):45–64. https://doi.org/10.1007/s42803-022-00046-7",
    "Pedregosa F et al (2011) Scikit-learn: machine learning in Python. Journal of Machine Learning Research 12:2825–2830",
    "Qi P, Zhang Y, Zhang Y, Bolton J, Manning CD (2020) Stanza: a Python natural language processing toolkit for many human languages. In: Proceedings of the 58th annual meeting of the Association for Computational Linguistics: system demonstrations. Association for Computational Linguistics, pp 101–108. https://doi.org/10.18653/v1/2020.acl-demos.14",
    "Riemenschneider F, Frank A (2023a) Exploring large language models for classical philology. In: Proceedings of the 61st annual meeting of the Association for Computational Linguistics (volume 1: long papers). Association for Computational Linguistics, pp 15181–15199. https://doi.org/10.18653/v1/2023.acl-long.846",
    "Riemenschneider F, Frank A (2023b) Graecia capta ferum victorem cepit: detecting Latin allusions to Ancient Greek literature. In: Proceedings of the ancient language processing workshop. INCOMA, pp 30–38",
    "Sadasivan VS, Kumar A, Balasubramanian S, Wang W, Feizi S (2023) Can AI-generated text be reliably detected? arXiv:2303.11156",
    "Seabold S, Perktold J (2010) Statsmodels: econometric and statistical modeling with Python. In: Proceedings of the 9th Python in science conference, pp 92–96",
    "Singh P, Rutten G, Lefever E (2021) A pilot study for BERT language modelling and morphological analysis for ancient and medieval Greek. In: Proceedings of the 5th joint SIGHUM workshop on computational linguistics for cultural heritage, social sciences, humanities and literature. Association for Computational Linguistics, pp 128–137. https://doi.org/10.18653/v1/2021.latechclfl-1.15",
    "Solaiman I et al (2019) Release strategies and the social impacts of language models. arXiv:1908.09203",
    "Stamatatos E (2009) A survey of modern authorship attribution methods. Journal of the American Society for Information Science and Technology 60(3):538–556. https://doi.org/10.1002/asi.21001",
    "Stover JA, Winter Y, Koppel M, Kestemont M (2016) Computational authorship verification method attributes a new work to a major 2nd century African author. Journal of the Association for Information Science and Technology 67(1):239–242. https://doi.org/10.1002/asi.23460",
    "Tang R, Chuang YN, Hu X (2024) The science of detecting LLM-generated text. Communications of the ACM 67(4):50–59. https://doi.org/10.1145/3624725",
    "van der Maaten L, Hinton G (2008) Visualizing data using t-SNE. Journal of Machine Learning Research 9:2579–2605",
    "Vatri A, McGillivray B (2018) The Diorisis Ancient Greek corpus. Research Data Journal for the Humanities and Social Sciences 3(1):55–65. https://doi.org/10.1163/24523666-01000013",
    "Wei J et al (2022) Chain-of-thought prompting elicits reasoning in large language models. In: Advances in neural information processing systems 35. Curran Associates, Red Hook, NY, pp 24824–24837",
    "Zainaldin JL, Pattison C, Marai M, Wu J, Schiefsky MJ (2026) Evaluating LLM-based translation of a low-resource technical language: the medical and philosophical Greek of Galen. arXiv:2602.24119",
    "Zhu S et al (2024) Multilingual large language models: a systematic survey. arXiv:2411.11072",
]

APPENDIX_INTRO = [
    ("h1", "Appendix A  Generation prompts"),
    ("body",
     "Both prompts were issued as a system message followed by a user message. The placeholders in braces "
     "(for example, {target_words}, {min_words}, {max_words}, {source_words} and {source_text}) were filled at "
     "generation time from each source chunk; the tolerance band was ±15% of the source length. The verbatim "
     "prompt texts are reproduced below and are released with the resource."),
]
