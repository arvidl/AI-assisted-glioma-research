# Primary-source bibliography check

Checked during repository design on 6 October 2026. These are the primary
papers selected for the initial perspective, not a systematic literature
review. The manuscript's synthetic results are generated here and are not
attributed to these papers.

| Reference | Primary source | Use in this manuscript |
| --- | --- | --- |
| Isensee et al., Nature Methods 18, 203–211 (2021) | [nnU-Net](https://doi.org/10.1038/s41592-020-01008-z) | Context for learned biomedical image segmentation; the demo does not run nnU-Net |
| Suter et al., Scientific Data 9, 768 (2022) | [LUMIERE](https://doi.org/10.1038/s41597-022-01881-7) | Provenance of the longitudinal public-MRI example (notebook 03), its released metadata and RANO ratings (data records on Figshare, [doi:10.6084/m9.figshare.c.5904905.v1](https://doi.org/10.6084/m9.figshare.c.5904905.v1); images in article 21249516, [doi:10.6084/m9.figshare.21249516.v1](https://doi.org/10.6084/m9.figshare.21249516.v1), whose 36 Patient-048 files `make lumiere-fetch` pins), and the non-commercial use condition (Usage Notes) |
| Swanson et al., British Journal of Cancer 98, 113–119 (2008) | [Survival-prediction proof of principle](https://doi.org/10.1038/sj.bjc.6604125) | Notebook 03: convention that the T1Gd and T2 boundaries lie at about 80% and 16% of maximum tumour-cell density (checked 12 October 2026) |
| Wang et al., Cancer Research 69, 9133–9140 (2009) | [Growth kinetics of 32 glioblastomas](https://doi.org/10.1158/0008-5472.CAN-08-3863) | Notebook 03: median D 29.7 mm²/year and ρ 15/year as prescribed coefficients; units of D from the Methods and Table 2, where one results sentence says mm²/day (checked 12 October 2026) |
| Wen et al., Journal of Clinical Oncology 41, 5187–5199 (2023) | [RANO 2.0](https://doi.org/10.1200/JCO.23.01059) | Clinical response-assessment context; synthetic volume changes are not RANO classifications |
| Zhao et al., Genomics, Proteomics & Bioinformatics 19, 1–12 (2021) | [CGGA](https://doi.org/10.1016/j.gpb.2020.10.005) | Provenance of an optional public clinical-data reader |
| Kefeli and Tatonetti, Patterns 5, 100933 (2024) | [TCGA-Reports](https://doi.org/10.1016/j.patter.2024.100933) | Provenance and scope of the optional pathology-text resource |

Bibliographic fields were checked against primary publication records.
Scientific claims, citations in context, and completeness of the literature
coverage remain part of the investigator's review. No cited source establishes
the benefit of the research-assistance workflow developed in this repository.

## Biology-focused revision and imaging foundation: 6 October 2026

| Reference | Primary publication | Use and boundary |
| --- | --- | --- |
| Lundervold et al., Journal of Medical Engineering & Technology, 1–36 (2026), online 14 August | [Published paper](https://doi.org/10.1080/03091902.2026.2713703); [indexed record](https://pubmed.ncbi.nlm.nih.gov/42600071/) | Own segmentation and anatomical-profiling feasibility study; quoted aggregates, not a pipeline rerun or clinical-utility claim |
| Hara et al., Cancer Cell 39(6), 779–792.e11 (2021) | [State transitions](https://doi.org/10.1016/j.ccell.2021.05.002) | Experimental macrophage-associated MES-like transition; does not establish our reversible two-state rates |
| Hara et al., Cancer Cell 43(6), 1175–1176 (2025) | [Erratum](https://doi.org/10.1016/j.ccell.2025.05.007) | Corrected supplementary Figure S5C heatmap; no original experimental figure copied here |
| Wang et al., Cancer Cell 42(5), 815–832.e12 (2024) | [Hypoxic macrophage niches](https://doi.org/10.1016/j.ccell.2024.03.013) | Spatial macrophage/vascular context; no oxygen or immune-population model is claimed |
| Venkatesh et al., Nature 573, 539–545 (2019) | [Electrical and synaptic integration](https://doi.org/10.1038/s41586-019-1563-y) | Experimental neuron–glioma communication motivates the question, not the teaching equations |
| McAlpine et al., Nature Neuroscience 29(2), 350–357 (2026), online 26 November 2025 | [Human cortical-tissue experiments](https://doi.org/10.1038/s41593-025-02149-0) | Human-tissue activity, synaptic responses and proliferation; no mapping to the model's slow signal index |
| Krishna et al., Nature 617, 599–607 (2023) | [Human neural-circuit remodeling](https://doi.org/10.1038/s41586-023-06036-1) | Human recordings and clinical associations; association is kept distinct from treatment benefit |

Metadata and these limited claims were checked against accessible primary
publication abstracts and records; the segmentation PDF's abstract and
limitations were inspected directly. The Hara correction was also checked
against the authors' institutional publication record, which reports the
corrected duplicated heatmap and states that the conclusions are unaffected.
This is not a systematic review or a claim of complete experimental-paper
review. The journal year and first-online date for McAlpine are deliberately
distinguished. Parameters, reversibility and coupling forms are our prescribed
teaching choices, not values extracted from these publications.


## Astrocytes, fields and cognition: 6 October 2026

| Reference | Primary publication | Use and boundary |
| --- | --- | --- |
| Sibille, Pannasch and Rouach, J Physiol 592(1), 87–102 (2014); online 2013 | [Astroglial potassium clearance](https://doi.org/10.1113/jphysiol.2013.261735) | Hippocampal-slice evidence linking clearance and short-term synaptic responses; does not calibrate our rates |
| Watson et al., Nature Cancer 4, 648–664 (2023) | [Astrocyte mitochondrial transfer](https://doi.org/10.1038/s43018-023-00556-5) | GAP43-dependent transfer and tumorigenicity in experimental systems; distinct from potassium clearance |
| Buzsáki, Anastassiou and Koch, Nat Rev Neurosci 13, 407–420 (2012) | [Extracellular fields and currents](https://doi.org/10.1038/nrn3241) | Review of potential sources, geometry and synchrony; potential and spatial field are different quantities |
| Anastassiou et al., Nat Neurosci 14, 217–223 (2011) | [Ephaptic coupling](https://doi.org/10.1038/nn.2727) | Experimental cortical-slice membrane/timing effects; no inferred cognition or glioma effect |
| Miller, Brincat and Roy, J Neurosci 46(33), e0711262026 (2026) | [Analog Cognition and Consciousness](https://doi.org/10.1523/JNEUROSCI.0711-26.2026); [indexed record](https://pubmed.ncbi.nlm.nih.gov/42618509/) | Published review/theory, not a demonstrated consciousness mechanism or glioma validation |
| Pinotsis, Fridman and Miller, Prog Neurobiol 226, 102465 (2023) | [Cytoelectric coupling](https://doi.org/10.1016/j.pneurobio.2023.102465) | Field–cytoskeleton feedback hypothesis explicitly requiring direct tests; no fitted coupling coefficient |
| Osswald et al., Nature 528, 93–98 (2015) | [Tumor cell networks](https://doi.org/10.1038/nature16071) | Membrane tumor-microtube networks; different from intracellular tubulin microtubules |
| Smyth et al., Cell Death Dis 16, 388 (2025) | [Cx43–microtubule interactions](https://doi.org/10.1038/s41419-025-07514-2) | Perturbation of glioblastoma stem-like cells and xenografts; no direct LFP/cytoelectric test or clinical recommendation |

Metadata were checked against primary publisher and indexed records. Limited
claims were checked against accessible primary abstracts/sections; the local
published Miller review was read, including its theoretical framing. This is
not a systematic review or a claim that every experimental dataset was reanalyzed.
The published segmentation methods and figure captions were additionally inspected.
None of these sources establishes an LFP → microtubule → glioma-growth/cognition
causal chain. The teaching coefficients and static potential profiles are prescribed.

The investigator's 29 September 2026 HBF presentation supplies conceptual
context for the brief cognition discussion, not independent scientific evidence:
[published presentation](https://docs.google.com/presentation/d/e/2PACX-1vTPxkTkGg5c3IHRLUdMBJZf-9v7jfPixOn5hOzqrSTiO1uzqJjoabtHcKG5mPultgqEJVtuZtYQR_u6/pub).
Its source was not edited or copied into Git. Dense consciousness infographics
were not reused as evidence in the glioma talk.

## Empirical cognition and proposed prediction: 6 October 2026

| Reference | Primary source | Use and boundary |
| --- | --- | --- |
| Aerts, Van Vrekhem, Stas and Marinazzo, Psycho-Oncology 28(10), 2068–2075 (2019) | [Author institution record](https://biblio.ugent.be/publication/8625236); [publication DOI](https://doi.org/10.1002/pon.5195) | Exploratory repeated behavioral assessment; not a validated surgical effect or cognitive predictor |
| Aerts, Van Roost, Achten and Marinazzo, OSF supplementary resource (2019) | [Original release](https://osf.io/5kfw3/) | CC BY 4.0 source data and legend; creators differ from the final article's author list; revisions/hashes pinned in the source manifest |
| Aerts et al., Scientific Data 9, 676 (2022) | [MRI resource](https://doi.org/10.1038/s41597-022-01806-4) | T1/diffusion/BOLD, connectomes and modeled dynamics; MRI recruitment differs from behavioral availability; no direct LFP recording |
| Aerts et al., NeuroImage 213, 116738 (2020) | [Final publication record](https://biblio.ugent.be/publication/8654150); [publication DOI](https://doi.org/10.1016/j.neuroimage.2020.116738) | Virtual resection and variable postoperative FC agreement; not established cognitive prediction |
| CANTAB test definitions | [NIH data dictionary](https://nda.nih.gov/data_structure?short_name=cantab01); [provider SSP definition](https://cambridgecognition.com/spatial-span-ssp/); [provider RTI definition](https://cambridgecognition.com/reaction-time-rti/) | Native units and task interpretation; the release's five-choice RTI field does not identify mean versus median; no normative impairment thresholds inferred |

The source release, legend and non-imputed analysis script were acquired
explicitly and verified locally. Only shared measures and released precision
support the case figure. The regression script's date parsing was inspected;
its analyses were not executed or adopted as our prediction evaluation.
The MRI resource's behavioral domain definitions and cohort description were
checked directly, together with the final behavioral/virtual-resection
publication records. This is source verification for an illustrative example,
not a reanalysis of those studies or a systematic review. The proposed SSP
endpoint and model comparison are our design choices pending scientific review.

Added on 10 October 2026 for the forecasting motivation and the coefficient comparison, each checked against the publisher record or full text:

| Reference | Primary source | Use in this manuscript |
| --- | --- | --- |
| Wang et al., Cancer Research 69, 9133–9140 (2009) | [Growth kinetics](https://doi.org/10.1158/0008-5472.CAN-08-3863) | Scale comparison for the prescribed D and ρ; D read as mm²/yr (see notebook 02) |
| Yankeelov et al., Cancer Research 75, 918–923 (2015) | [Tumor forecasting](https://doi.org/10.1158/0008-5472.CAN-14-2233) | Weather-forecasting analogy for tumor growth |
| Price et al., Nature 637, 84–90 (2025) | [GenCast](https://doi.org/10.1038/s41586-024-08252-9) | Machine-learned probabilistic weather forecasting |
| Bodnar et al., Nature 641, 1180–1187 (2025) | [Aurora](https://doi.org/10.1038/s41586-025-09005-y) | Earth-system foundation model; cyclone tracks |
| Rasp et al., arXiv:2609.03582 (2026, preprint) | [WeatherNext 3](https://arxiv.org/abs/2609.03582) | Observation-driven hourly AI forecasting |
| Zarodniuk et al., PNAS 123, e2513172122 (2026) | [Compression](https://doi.org/10.1073/pnas.2513172122) | Tumor-to-brain mechanical effects in experimental models |

Added on 10 October 2026 for response assessment, tumor microtubes, cancer neuroscience and the reaction–diffusion model. Fields were taken from Crossref records for each DOI and the claims checked against the abstracts:

| Reference | Primary source | Use in this manuscript |
| --- | --- | --- |
| Albert et al., Lancet Oncol 25, e29–e41 (2024) | [PET RANO 1.0](https://doi.org/10.1016/S1470-2045(23)00525-9) | Amino-acid PET response criteria complementing MRI-based RANO 2.0 |
| Galldiks et al., Lancet Oncol 26, e436–e447 (2025) | [RANO/EANO PET update](https://doi.org/10.1016/S1470-2045(25)00193-7) | Clinical PET recommendations in glioma |
| van den Bent et al., Neuro-Oncology 27, 2209–2224 (2025) | [RANO progress report](https://doi.org/10.1093/neuonc/noaf118) | Scope of RANO, including extent of resection and AI; cited instead of the unchecked RANO resect paper |
| Weil et al., Neuro-Oncology 19, 1316–1326 (2017) | [Microtubes and resistance](https://doi.org/10.1093/neuonc/nox070) | Microtube networks resist surgical lesions and chemotherapy in experimental models |
| Venkataramani et al., Nature 573, 532–538 (2019) | [Glutamatergic input](https://doi.org/10.1038/s41586-019-1564-x) | Neuron–glioma synapses on tumor microtubes |
| Venkataramani et al., Cell 185, 2899–2917.e31 (2022) | [Neuronal mechanisms of invasion](https://doi.org/10.1016/j.cell.2022.06.054) | Neuron-like brain invasion |
| Hausmann et al., Nature 613, 179–186 (2023) | [Rhythmic network activity](https://doi.org/10.1038/s41586-022-05520-4) | KCa3.1-dependent pacemaker-like cells drive network growth |
| Hai et al., Nat Commun 15, 968 (2024) | [Connectivity signature](https://doi.org/10.1038/s41467-024-45067-8) | Connectivity estimated in patient samples; associations with subtype and survival |
| Taylor et al., Nature 623, 366–374 (2023) | [Glioma synapse plasticity](https://doi.org/10.1038/s41586-023-06678-1) | BDNF–TrkB plasticity; depolarization promotes proliferation in experimental models |
| Winkler et al., Cell 186, 1689–1707 (2023) | [Cancer neuroscience review](https://doi.org/10.1016/j.cell.2023.02.002) | Field review |
| Monje, Neuron 113, 2734–2739 (2025) | [Neuroscience of brain cancers](https://doi.org/10.1016/j.neuron.2025.07.012) | Field review |
| Pinotsis & Miller, Cereb Cortex 36, bhag098 (2026) | [Ephaptic coupling](https://doi.org/10.1093/cercor/bhag098) | Field-to-neuron influences in prefrontal recordings; not a glioma result |
| Fisher, Ann Eugen 7, 355–369 (1937) | [Wave of advance](https://doi.org/10.1111/j.1469-1809.1937.tb02153.x) | Origin of the reaction–diffusion equation |
| Kolmogorov, Petrovsky & Piskunov, Bull. Univ. Moscou A 1(6) (1937) | No DOI | Front-speed analysis; fields from secondary citations, pages omitted because they differ between them |
| Murray, Mathematical Biology II, 3rd ed., Springer (2003) | [Book](https://doi.org/10.1007/b98869) | Travelling waves and brain-tumor applications |
| Swanson, Alvord & Murray, Cell Prolif 33, 317–329 (2000) | [Grey/white motility](https://doi.org/10.1046/j.1365-2184.2000.00177.x) | Proliferation–invasion model with tissue-dependent migration |
| Swanson, Alvord & Murray, DCDS-B 4, 289–295 (2004) | [Therapeutic window](https://doi.org/10.3934/dcdsb.2004.4.289) | Treatment implications of the model; corrected in notebook 02, which had cited it for grey/white migration |

Added on 10 October 2026 for notebook 02's tissue-guided experiment (notebook only, not in the paper's bibliography); fields checked against Crossref:

| Reference | Primary source | Use in notebook 02 |
| --- | --- | --- |
| Hannisdal et al., npj Precis Oncol 10, 364 (2026) | [Recurrence patterns](https://doi.org/10.1038/s41698-026-01557-0) | Motivation for Figure 2: lobe-level recurrence, parietal tumors' recurrence in new sites, the authors' suggestion about posterior white matter; full text supplied by the investigator |
| Jbabdi et al., Magn Reson Med 54, 616–624 (2005) | [Anisotropic growth with DTI](https://doi.org/10.1002/mrm.20625) | Prior use of DTI-derived anisotropic diffusion for glioma growth |
| Clatz et al., IEEE Trans Med Imaging 24, 1334–1346 (2005) | [3-D growth with deformation](https://doi.org/10.1109/TMI.2005.857217) | Prior anisotropic, tissue-dependent glioma growth simulation |
| Painter & Hillen, J Theor Biol 323, 25–39 (2013) | [DTI and anisotropic invasion](https://doi.org/10.1016/j.jtbi.2013.01.014) | Prior use of DTI to model anisotropic invasion pathways |

Swanson, Alvord & Murray (2000), already listed above, is cited for tissue-dependent migration. On 12 October 2026 its full text ([PMC6621920](https://pmc.ncbi.nlm.nih.gov/articles/PMC6621920/)) was checked for notebook 03's 3D section: it estimates $D_w > 5 D_g$ from CT margins advancing two to three times faster across the corpus callosum and uses $D_w = 5 D_g$ throughout. Swanson et al., Br J Cancer 86, 14–18 (2002), [doi:10.1038/sj.bjc.6600021](https://doi.org/10.1038/sj.bjc.6600021) ([PMC2746525](https://pmc.ncbi.nlm.nih.gov/articles/PMC2746525/)), calls 5 "an arbitrary first approximation" within an estimated 2–100-fold range and imposes zero flux at CSF boundaries; notebook 03 cites it for both.

### Notebook 11 references (10 October 2026)

Checked against Crossref metadata (authors, year, title, journal, volume, pages) and the PubMed abstracts; claims in the notebook follow the abstracts. Not added to the paper.

| Reference | Primary source | Use in notebook 11 |
| --- | --- | --- |
| Catani & ffytche, Brain 128, 2224–2239 (2005) | [Disconnection syndromes](https://doi.org/10.1093/brain/awh622) | Disconnection as a framework for deficits from white-matter lesions |
| Alstott et al., PLoS Comput Biol 5, e1000408 (2009) | [Lesions in a connectome model](https://doi.org/10.1371/journal.pcbi.1000408) | Simulated lesions change functional connectivity among distant regions, often in both hemispheres |
| Honey et al., PNAS 106, 2035–2040 (2009) | [Structure predicts resting FC](https://doi.org/10.1073/pnas.0811168106) | Structural connectivity partly predicts resting FC; strong FC without a direct structural link |
| Ercsey-Ravasz et al., Neuron 80, 184–197 (2013) | [Exponential distance rule](https://doi.org/10.1016/j.neuron.2013.07.036) | Form of the distance-dependent weight; the 40 mm decay length is a teaching choice, not their value |
| Latora & Marchiori, Phys Rev Lett 87, 198701 (2001) | [Network efficiency](https://doi.org/10.1103/PhysRevLett.87.198701) | Definition of global efficiency |
| Fernández Galán, PLoS One 3, e2148 (2008) | [Architecture and spontaneous activity](https://doi.org/10.1371/journal.pone.0002148) | Linear network model linking connectivity to spontaneous activity patterns; the PubMed record carries an author-name erratum |

Aerts et al. (2020, NeuroImage) and Aerts et al. (2022, Sci Data), already in the paper's bibliography, are cited for pre-/post-operative modelling with The Virtual Brain and the open cohort.

### Notebook 11 references (15 October 2026)

Added with the graph-theory primer and the revised tracks. Each DOI was resolved through the Crossref API, and authors, year, title, journal, volume and pages were compared with the entry. "Abstract" means the PubMed abstract was read and the notebook's statement follows it; "metadata" means the work is cited for its general subject only. Griffis et al. (2019) and Duffau (2014) were also added to the paper, in the network section, for the statements given here.

| Reference | Primary source | Check | Use in notebook 11 |
| --- | --- | --- | --- |
| Katz, Psychometrika 18, 39–43 (1953) | [Status index](https://doi.org/10.1007/BF02289026) | Metadata | Walk counting attenuated by length; the same series as the model covariance |
| Watts & Strogatz, Nature 393, 440–442 (1998) | [Small-world networks](https://doi.org/10.1038/30918) | Metadata | History of network science |
| Newman, SIAM Rev 45, 167–256 (2003) | [Complex networks review](https://doi.org/10.1137/S003614450342480) | Metadata | Review of network science |
| Sporns, Tononi & Kötter, PLoS Comput Biol 1, e42 (2005) | [The human connectome](https://doi.org/10.1371/journal.pcbi.0010042) | Abstract | Proposal of a connection matrix of the human brain |
| Bullmore & Sporns, Nat Rev Neurosci 10, 186–198 (2009) | [Complex brain networks](https://doi.org/10.1038/nrn2575) | Metadata | Review of graph analysis of structural and functional networks |
| Rubinov & Sporns, NeuroImage 52, 1059–1069 (2010) | [Network measures](https://doi.org/10.1016/j.neuroimage.2009.10.003) | Metadata | Measures deliberately not used (clustering, modularity, hubs) |
| Zalesky et al., NeuroImage 50, 970–983 (2010) | [Choice of nodes](https://doi.org/10.1016/j.neuroimage.2009.12.027) | Abstract | Network parameters vary with nodal scale; compare only at the same scale |
| van den Heuvel & Sporns, Trends Cogn Sci 17, 683–696 (2013) | [Network hubs](https://doi.org/10.1016/j.tics.2013.09.012) | Abstract | Hubs support integration and are points of vulnerability |
| Fornito, Zalesky & Bullmore, Academic Press (2016) | [Textbook](https://doi.org/10.1016/C2012-0-06036-X) | Metadata; the Crossref record lists no authors, which were not checked against a registry | Textbook of brain network analysis |
| Bassett & Sporns, Nat Neurosci 20, 353–364 (2017) | [Network neuroscience](https://doi.org/10.1038/nn.4502) | Metadata | Network neuroscience as a field |
| Honey & Sporns, Hum Brain Mapp 29, 802–809 (2008) | [Lesions in cortical networks](https://doi.org/10.1002/hbm.20579) | Abstract | Lesion effects extend beyond the immediate neighbours in macaque-based models |
| Griffis et al., Cell Rep 28, 2527–2540.e9 (2019) | [Structural disconnection after stroke](https://doi.org/10.1016/j.celrep.2019.07.100) | Abstract | In 114 stroke patients, disconnection measures explained FC disruption better than focal damage; interhemispheric disconnection linked to deficits in several domains |
| Herbet & Duffau, Physiol Rev 100, 1181–1228 (2020) | [Meta-networking theory](https://doi.org/10.1152/physrev.00033.2019) | Abstract | Cognition from interacting distributed networks; accounts for postlesional compensation |
| Bartolomei et al., Clin Neurophysiol 117, 2039–2049 (2006) | [Graph analysis in brain tumour patients](https://doi.org/10.1016/j.clinph.2006.05.018) | Abstract | Resting MEG, 17 patients and 15 controls: non-focal FC changes and altered small-world architecture |
| Duffau, Cortex 58, 325–337 (2014) | [Plasticity and connectomics in glioma surgery](https://doi.org/10.1016/j.cortex.2013.08.005) | Abstract | Extensive cortical reorganisation, with white-matter connectivity as a main limit of plasticity |
| Derks, Reijneveld & Douw, Curr Opin Oncol 26, 627–633 (2014) | [Networks and cognitive deficits](https://doi.org/10.1097/CCO.0000000000000126) | Abstract | General cognitive deficits reflected in whole-brain network disturbances; network change after resection goes with cognitive outcome |
| Stam, Nat Rev Neurosci 15, 683–695 (2014) | [Network science of neurological disorders](https://doi.org/10.1038/nrn3801) | Abstract | Hub overload and failure as a possible common pathway |
| Fornito, Zalesky & Breakspear, Nat Rev Neurosci 16, 159–172 (2015) | [Connectomics of brain disorders](https://doi.org/10.1038/nrn3901) | Abstract | Diaschisis, degeneracy, reserve and compensation |
| Aerts et al., Brain 139, 3063–3083 (2016) | [Brain networks under attack](https://doi.org/10.1093/brain/aww194) | Abstract | Review of lesion studies including brain tumours; effects depend on the network position of the lesion |
| Deco, Jirsa & McIntosh, Nat Rev Neurosci 12, 43–56 (2011) | [Resting-state dynamics](https://doi.org/10.1038/nrn2961) | Metadata | Review of dynamical models of resting-state activity |
| Abdelnour, Voss & Raj, NeuroImage 90, 335–347 (2014) | [Network diffusion model](https://doi.org/10.1016/j.neuroimage.2013.12.039) | Abstract | A linear graph-diffusion model captured the structure–function relation better than earlier nonlinear approaches |

Euler's 1736 paper on the Königsberg bridges is mentioned in the notebook for history and is not cited.

### Notebook 12 (formerly 11b) references (10 October 2026)

Checked against Crossref metadata (authors, year, title, journal, volume, pages; abstract where deposited). Not added to the paper.

| Reference | Primary source | Use in notebook 12 |
| --- | --- | --- |
| Aerts et al., eNeuro 5(3), ENEURO.0083-18.2018 (2018) | [The Virtual Brain in brain tumour patients](https://doi.org/10.1523/ENEURO.0083-18.2018) | Describes the cohort (25 patients, 11 controls) and individual model fitting; cited by the source dataset |
| Smith et al., NeuroImage 119, 338–351 (2015) | [SIFT2](https://doi.org/10.1016/j.neuroimage.2015.06.092) | Streamline weights used for the structural matrices |
| Desikan et al., NeuroImage 31, 968–980 (2006) | [Desikan–Killiany atlas](https://doi.org/10.1016/j.neuroimage.2006.01.021) | Cortical parcellation of the 82 regions (with FreeSurfer subcortical labels) |

The two OpenNeuro dataset DOIs are taken from the source subset's `dataset_description.json`. Aerts et al. (2020) is cited for comparing virtual and actual post-operative networks with variable agreement, as already summarised above; its methods were not reproduced.

### Didactic notebooks 05 and 10 (10 October 2026)

Checked against Crossref metadata (authors, year, title, journal, volume, pages). Not added to the paper.

| Reference | Primary source | Use |
| --- | --- | --- |
| Neftel et al., Cell 178, 835–849.e21 (2019) | [Cellular states and plasticity in glioblastoma](https://doi.org/10.1016/j.cell.2019.06.024) | Notebook 05: four malignant cellular states (MES-, AC-, OPC- and NPC-like) and plasticity, as background for a two-state construction; no rate is taken from it |
| Jacobson and Truax, J Consult Clin Psychol 59, 12–19 (1991) | [Reliable change index](https://doi.org/10.1037/0022-006X.59.1.12) | Notebook 10: definition of the reliable change index; applied only to hypothetical inputs |
