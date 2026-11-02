# VQEBD — Hivatkozásjegyzék

| | |
|---|---|
| **Dokumentum** | `docs/references.md` |
| **Dokumentum-verzió** | 1.2.0 |
| **Dátum** | 2026-11-02 |
| **Készítők** | Kormos Attila, Claude AI (Anthropic, Claude Opus 5) |
| **Generálta** | `scripts/gen_references.py` |
| **Tételek** | 59 db, ebből **57** gépileg DOI-validált |

---

## Módszertani megjegyzés

Ebben a jegyzékben a szerzőlistákat, címeket, évszámokat, kötet- és oldalszámokat
**nem kézzel írtuk**: a DOI-ból oldottuk fel őket a Crossref (`api.crossref.org`),
illetve arXiv-DOI esetén a DataCite (`api.datacite.org`) REST API-val. Ami itt
szerepel, az a kiadó által regisztrált metaadat — ez kizárja a
hivatkozás-halucinációt.
A generálás megismételhető: `python scripts/gen_references.py`. A nyers API-válaszok
provenance céljából a `docs/testing/refs_crossref_raw.json` fájlban vannak.

Két tételnek nincs regisztrált DOI-ja; ezek forrása kézi, de bibliográfiailag
ellenőrzött,
és a *Megjegyzés* sor jelzi őket.

A generátor a beolvasott metaadatban **kiszűri a U+FFFD (replacement character)**
karaktereket: ha egy registry-rekord sérült, a generálás hibával leáll, hacsak nincs
hozzá kézzel ellenőrzött javítás. Az ilyen tételeket a *Metaadat-javítás* sor jelzi.

Az idézési év a **lapszám** éve (`published-print`), nem az online-first dátum
(pl. [romero2019] online 2018-10-19, lapszám 2019-01-01 → **2019**).

---

## VQE elmélet és alapok

**[peruzzo2014]** Peruzzo, A., McClean, J., Shadbolt, P., Yung, M., Zhou, X., Love, P., Aspuru-Guzik, A., O’Brien, J. (2014). A variational eigenvalue solver on a photonic quantum processor. *Nature Communications*, **5** 4213.
  DOI: [10.1038/ncomms5213](https://doi.org/10.1038/ncomms5213)
  *Felhasználás:* A VQE algoritmus eredeti közleménye.

**[mcclean2016]** McClean, J., Romero, J., Babbush, R., Aspuru-Guzik, A. (2016). The theory of variational hybrid quantum-classical algorithms. *New Journal of Physics*, **18** 023023.
  DOI: [10.1088/1367-2630/18/2/023023](https://doi.org/10.1088/1367-2630/18/2/023023)
  *Felhasználás:* A variációs hibrid algoritmusok elméleti kerete; a lövésszám-becslés alapja.

**[omalley2016]** O’Malley, P., Babbush, R., Kivlichan, I., Romero, J., McClean, J., Barends, R., Kelly, J., Roushan, P., Tranter, A., Ding, N., Campbell, B., Chen, Y., et al. (2016). Scalable Quantum Simulation of Molecular Energies. *Physical Review X*, **6** 031007.
  DOI: [10.1103/physrevx.6.031007](https://doi.org/10.1103/physrevx.6.031007)
  *Felhasználás:* H2 alapállapot szupravezető qubiteken — a Fázis 2 hardveres mérés irodalmi előzménye.

**[kandala2017]** Kandala, A., Mezzacapo, A., Temme, K., Takita, M., Brink, M., Chow, J., Gambetta, J. (2017). Hardware-efficient variational quantum eigensolver for small molecules and quantum magnets. *Nature*, **549** 242-246.
  DOI: [10.1038/nature23879](https://doi.org/10.1038/nature23879)
  *Felhasználás:* Hardware-efficient ansatz; a LiH és BeH2 választásunk irodalmi előzménye.

**[hempel2018]** Hempel, C., Maier, C., Romero, J., McClean, J., Monz, T., Shen, H., Jurcevic, P., Lanyon, B., Love, P., Babbush, R., Aspuru-Guzik, A., Blatt, R., et al. (2018). Quantum Chemistry Calculations on a Trapped-Ion Quantum Simulator. *Physical Review X*, **8** 031022.
  DOI: [10.1103/physrevx.8.031022](https://doi.org/10.1103/physrevx.8.031022)
  *Felhasználás:* Független hardverplatform (csapdázott ion) ugyanezekre a molekulákra — kereszthivatkozás.

**[barkoutsos2018]** Barkoutsos, P., Gonthier, J., Sokolov, I., Moll, N., Salis, G., Fuhrer, A., Ganzhorn, M., Egger, D., Troyer, M., Mezzacapo, A., Filipp, S., Tavernelli, I. (2018). Quantum algorithms for electronic structure calculations: Particle-hole Hamiltonian and optimized wave-function expansions. *Physical Review A*, **98** 022322.
  DOI: [10.1103/physreva.98.022322](https://doi.org/10.1103/physreva.98.022322)
  *Felhasználás:* Particle-hole Hamilton-operátor és optimalizált hullámfüggvény-kifejtések.

**[romero2019]** Romero, J., Babbush, R., McClean, J., Hempel, C., Love, P., Aspuru-Guzik, A. (2019). Strategies for quantum computing molecular energies using the unitary coupled cluster ansatz. *Quantum Science and Technology*, **4** 014008.
  DOI: [10.1088/2058-9565/aad3e4](https://doi.org/10.1088/2058-9565/aad3e4)
  *Felhasználás:* UCCSD ansatz-stratégiák — a Fázis 1 ansatz-választásának indoklása.

**[tilly2022]** Tilly, J., Chen, H., Cao, S., Picozzi, D., Setia, K., Li, Y., Grant, E., Wossnig, L., Rungger, I., Booth, G., Tennyson, J. (2022). The Variational Quantum Eigensolver: A review of methods and best practices. *Physics Reports*, **986** 1-128.
  DOI: [10.1016/j.physrep.2022.08.003](https://doi.org/10.1016/j.physrep.2022.08.003)
  *Felhasználás:* VQE összefoglaló review; best-practice forrás a teljes projektre.


## Kvantumkémia

**[hehre1969]** Hehre, W., Stewart, R., Pople, J. (1969). Self-Consistent Molecular-Orbital Methods. I. Use of Gaussian Expansions of Slater-Type Atomic Orbitals. *The Journal of Chemical Physics*, **51** 2657-2664.
  DOI: [10.1063/1.1672392](https://doi.org/10.1063/1.1672392)
  *Felhasználás:* Az STO-3G bázis eredeti definíciója — a projekt alapértelmezett bázisa.

**[cao2019]** Cao, Y., Romero, J., Olson, J., Degroote, M., Johnson, P., Kieferová, M., Kivlichan, I., Menke, T., Peropadre, B., Sawaya, N., Sim, S., Veis, L., et al. (2019). Quantum Chemistry in the Age of Quantum Computing. *Chemical Reviews*, **119** 10856-10915.
  DOI: [10.1021/acs.chemrev.8b00803](https://doi.org/10.1021/acs.chemrev.8b00803)
  *Felhasználás:* Kvantumkémia a kvantumszámítás korában — átfogó review.

**[mcardle2020]** McArdle, S., Endo, S., Aspuru-Guzik, A., Benjamin, S., Yuan, X. (2020). Quantum computational chemistry. *Reviews of Modern Physics*, **92** 015003.
  DOI: [10.1103/revmodphys.92.015003](https://doi.org/10.1103/revmodphys.92.015003)
  *Felhasználás:* Kvantumszámításos kémia review (Reviews of Modern Physics).

**[sun2018]** Sun, Q., Berkelbach, T., Blunt, N., Booth, G., Guo, S., Li, Z., Liu, J., McClain, J., Sayfutyarova, E., Sharma, S., Wouters, S., Chan, G. (2018). PySCF: the Python‐based simulations of chemistry framework. *WIREs Computational Molecular Science*, **8** e1340.
  DOI: [10.1002/wcms.1340](https://doi.org/10.1002/wcms.1340)
  *Felhasználás:* PySCF — a klasszikus referenciaszint (L0: Hartree–Fock, FCI) számítómotorja.

**[sun2020]** Sun, Q., Zhang, X., Banerjee, S., Bao, P., Barbry, M., Blunt, N., Bogdanov, N., Booth, G., Chen, J., Cui, Z., Eriksen, J., Gao, Y., et al. (2020). Recent developments in the PySCF program package. *The Journal of Chemical Physics*, **153** 024109.
  DOI: [10.1063/5.0006074](https://doi.org/10.1063/5.0006074)
  *Felhasználás:* PySCF újabb fejlesztések — a 2.x ág hivatkozása.

**[helgaker2000]** Helgaker, T., Jørgensen, P., Olsen, J. (2000). Molecular Electronic-Structure Theory. *John Wiley & Sons, Chichester. ISBN 978-0-471-96755-2*.
  *Felhasználás:* A „kémiai pontosság” (1 kcal/mol) fogalmának standard tankönyvi forrása.
  *Megjegyzés:* A kémiai pontosság (1 kcal/mol = 1.5936 mHa) hivatkozási alapja.


## Fermion → qubit leképezések

**[jordan1928]** Jordan, P., Wigner, E. (1928). Über das Paulische Äquivalenzverbot. *Zeitschrift für Physik*, **47** 631-651.
  DOI: [10.1007/bf01331938](https://doi.org/10.1007/bf01331938)
  *Felhasználás:* A Jordan–Wigner transzformáció eredeti közleménye.
  *Metaadat-javítás:* A Crossref által tárolt metaadat hibásan kódolt (U+FFFD). A helyes alak a folyóirat eredeti közleményéből, Z. Physik 47, 631–651 (1928).

**[bravyi2002]** Bravyi, S., Kitaev, A. (2002). Fermionic Quantum Computation. *Annals of Physics*, **298** 210-226.
  DOI: [10.1006/aphy.2002.6254](https://doi.org/10.1006/aphy.2002.6254)
  *Felhasználás:* A Bravyi–Kitaev leképezés.

**[seeley2012]** Seeley, J., Richard, M., Love, P. (2012). The Bravyi-Kitaev transformation for quantum computation of electronic structure. *The Journal of Chemical Physics*, **137** 224109.
  DOI: [10.1063/1.4768229](https://doi.org/10.1063/1.4768229)
  *Felhasználás:* A Bravyi–Kitaev transzformáció elektronszerkezeti alkalmazása.


## Hibaenyhítés

**[temme2017]** Temme, K., Bravyi, S., Gambetta, J. (2017). Error Mitigation for Short-Depth Quantum Circuits. *Physical Review Letters*, **119** 180509.
  DOI: [10.1103/physrevlett.119.180509](https://doi.org/10.1103/physrevlett.119.180509)
  *Felhasználás:* A ZNE eredeti közleménye (Temme–Bravyi–Gambetta).

**[li2017]** Li, Y., Benjamin, S. (2017). Efficient Variational Quantum Simulator Incorporating Active Error Minimization. *Physical Review X*, **7** 021050.
  DOI: [10.1103/physrevx.7.021050](https://doi.org/10.1103/physrevx.7.021050)
  *Felhasználás:* Aktív hibaminimalizálás — a ZNE független, egyidejű felfedezése.

**[endo2018]** Endo, S., Benjamin, S., Li, Y. (2018). Practical Quantum Error Mitigation for Near-Future Applications. *Physical Review X*, **8** 031027.
  DOI: [10.1103/physrevx.8.031027](https://doi.org/10.1103/physrevx.8.031027)
  *Felhasználás:* Gyakorlati hibaenyhítés; a kvázi-valószínűségi módszer (PEC) alapja.

**[giurgicatiron2020]** Giurgica-Tiron, T., Hindy, Y., LaRose, R., Mari, A., Zeng, W. (2020). Digital zero noise extrapolation for quantum error mitigation. *2020 IEEE International Conference on Quantum Computing and Engineering (QCE)* 306-316.
  DOI: [10.1109/qce49297.2020.00045](https://doi.org/10.1109/qce49297.2020.00045)
  *Felhasználás:* Digitális ZNE: unitáris hajtogatás (unitary folding) — a saját implementációnk alapja.

**[nation2021]** Nation, P., Kang, H., Sundaresan, N., Gambetta, J. (2021). Scalable Mitigation of Measurement Errors on Quantum Computers. *PRX Quantum*, **2** 040326.
  DOI: [10.1103/prxquantum.2.040326](https://doi.org/10.1103/prxquantum.2.040326)
  *Felhasználás:* Skálázható mérési hibaenyhítés (M3) — válasz az M5 megállapításra (readout-hiba).

**[larose2022]** LaRose, R., Mari, A., Kaiser, S., Karalekas, P., Alves, A., Czarnik, P., El Mandouh, M., Gordon, M., Hindy, Y., Robertson, A., Thakre, P., Wahl, M., et al. (2022). Mitiq: A software package for error mitigation on noisy quantum computers. *Quantum*, **6** 774.
  DOI: [10.22331/q-2022-08-11-774](https://doi.org/10.22331/q-2022-08-11-774)
  *Felhasználás:* A Mitiq szoftvercsomag — a ZNE referencia-implementációja a keresztvalidációhoz.

**[vandenberg2023]** van den Berg, E., Minev, Z., Kandala, A., Temme, K. (2023). Probabilistic error cancellation with sparse Pauli–Lindblad models on noisy quantum processors. *Nature Physics*, **19** 1116-1121.
  DOI: [10.1038/s41567-023-02042-2](https://doi.org/10.1038/s41567-023-02042-2)
  *Felhasználás:* PEC ritka Pauli–Lindblad modellel — az IBM Runtime PEC opciójának háttere.

**[cai2023]** Cai, Z., Babbush, R., Benjamin, S., Endo, S., Huggins, W., Li, Y., McClean, J., O’Brien, T. (2023). Quantum error mitigation. *Reviews of Modern Physics*, **95** 045005.
  DOI: [10.1103/revmodphys.95.045005](https://doi.org/10.1103/revmodphys.95.045005)
  *Felhasználás:* Hibaenyhítés összefoglaló review (Reviews of Modern Physics).

**[kim2023]** Kim, Y., Eddins, A., Anand, S., Wei, K., van den Berg, E., Rosenblatt, S., Nayfeh, H., Wu, Y., Zaletel, M., Temme, K., Kandala, A. (2023). Evidence for the utility of quantum computing before fault tolerance. *Nature*, **618** 500-505.
  DOI: [10.1038/s41586-023-06096-3](https://doi.org/10.1038/s41586-023-06096-3)
  *Felhasználás:* ZNE nagy skálán, valódi hardveren — a módszer gyakorlati határainak referenciája.


## Benchmarking

**[cross2019]** Cross, A., Bishop, L., Sheldon, S., Nation, P., Gambetta, J. (2019). Validating quantum computers using randomized model circuits. *Physical Review A*, **100** 032328.
  DOI: [10.1103/physreva.100.032328](https://doi.org/10.1103/physreva.100.032328)
  *Felhasználás:* Quantum Volume — a volumetrikus nézet (Fázis 7.4) előzménye.

**[blumekohout2020]** Blume-Kohout, R., Young, K. (2020). A volumetric framework for quantum computer benchmarks. *Quantum*, **4** 362.
  DOI: [10.22331/q-2020-11-15-362](https://doi.org/10.22331/q-2020-11-15-362)
  *Felhasználás:* Volumetrikus benchmark-keretrendszer — a Fázis 7.4 hőtérkép módszertani alapja.

**[lubinski2023]** Lubinski, T., Johri, S., Varosy, P., Coleman, J., Zhao, L., Necaise, J., Baldwin, C., Mayer, K., Proctor, T. (2023). Application-Oriented Performance Benchmarks for Quantum Computing. *IEEE Transactions on Quantum Engineering*, **4** 1-32.
  DOI: [10.1109/tqe.2023.3253761](https://doi.org/10.1109/tqe.2023.3253761)
  *Felhasználás:* Alkalmazás-orientált benchmarkok — a projekt benchmark-módszertanának mintája.


## Optimalizálók

**[nelder1965]** Nelder, J., Mead, R. (1965). A Simplex Method for Function Minimization. *The Computer Journal*, **7** 308-313.
  DOI: [10.1093/comjnl/7.4.308](https://doi.org/10.1093/comjnl/7.4.308)
  *Felhasználás:* Nelder–Mead szimplex módszer.

**[spall1992]** Spall, J. (1992). Multivariate stochastic approximation using a simultaneous perturbation gradient approximation. *IEEE Transactions on Automatic Control*, **37** 332-341.
  DOI: [10.1109/9.119632](https://doi.org/10.1109/9.119632)
  *Felhasználás:* SPSA — zajos célfüggvényhez ajánlott sztochasztikus optimalizáló.

**[powell1994]** Powell, M. (1994). A Direct Search Optimization Method That Models the Objective and Constraint Functions by Linear Interpolation. *Advances in Optimization and Numerical Analysis* 51-67.
  DOI: [10.1007/978-94-015-8330-5_4](https://doi.org/10.1007/978-94-015-8330-5_4)
  *Felhasználás:* COBYLA — deriváltmentes, korlátozásos optimalizáló.

**[kraft1988]** Kraft, D. (1988). A software package for sequential quadratic programming. *Technical Report DFVLR-FB 88-28, Deutsche Forschungs- und Versuchsanstalt für Luft- und Raumfahrt (DFVLR), Köln*.
  *Felhasználás:* Az SLSQP algoritmus eredeti technikai jelentése.
  *Megjegyzés:* A Crossrefben nem regisztrált (technikai jelentés, nem folyóiratcikk). A SciPy `method="SLSQP"` ezt az algoritmust implementálja.


## Szoftver

**[javadiabhari2024]** Javadi-Abhari, Ali, Treinish, Matthew, Krsulich, Kevin, Wood, Christopher J., Lishman, Jake, Gacon, Julien, Martiel, Simon, Nation, Paul D., Bishop, Lev S., Cross, Andrew W., Johnson, Blake R., Gambetta, Jay M. (2024). Quantum computing with Qiskit. *arXiv*.
  DOI: [10.48550/arXiv.2405.08810](https://doi.org/10.48550/arXiv.2405.08810)
  *Felhasználás:* A Qiskit hivatalos hivatkozása (arXiv-preprint, DataCite DOI).

**[harris2020]** Harris, C., Millman, K., van der Walt, S., Gommers, R., Virtanen, P., Cournapeau, D., Wieser, E., Taylor, J., Berg, S., Smith, N., Kern, R., Picus, M., et al. (2020). Array programming with NumPy. *Nature*, **585** 357-362.
  DOI: [10.1038/s41586-020-2649-2](https://doi.org/10.1038/s41586-020-2649-2)
  *Felhasználás:* NumPy — numerikus alapréteg.

**[virtanen2020]** Virtanen, P., Gommers, R., Oliphant, T., Haberland, M., Reddy, T., Cournapeau, D., Burovski, E., Peterson, P., Weckesser, W., Bright, J., van der Walt, S., Brett, M., et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. *Nature Methods*, **17** 261-272.
  DOI: [10.1038/s41592-019-0686-2](https://doi.org/10.1038/s41592-019-0686-2)
  *Felhasználás:* SciPy — a VQE optimalizáló-hurok implementációja.


## Adatkezelés

**[wilkinson2016]** Wilkinson, M., Dumontier, M., Aalbersberg, I., Appleton, G., Axton, M., Baak, A., Blomberg, N., Boiten, J., da Silva Santos, L., Bourne, P., Bouwman, J., Brookes, A., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*, **3** 160018.
  DOI: [10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18)
  *Felhasználás:* FAIR alapelvek — a Fázis 4 adatséma és a Fázis 9 publikálás irányelve.


## Statisztika és mérési módszertan

**[student1908]** Student (1908). The Probable Error of a Mean. *Biometrika*, **6** 1.
  DOI: [10.2307/2331554](https://doi.org/10.2307/2331554)
  *Felhasználás:* A t-eloszlás: kis mintás (N seed) konfidencia-intervallum (vqebd.stats, ADR-0007).

**[wecker2015]** Wecker, D., Hastings, M., Troyer, M. (2015). Progress towards practical quantum variational algorithms. *Physical Review A*, **92** 042303.
  DOI: [10.1103/physreva.92.042303](https://doi.org/10.1103/physreva.92.042303)
  *Felhasználás:* A VQE mérési költsége és a lövészaj skálázása; az ismétlés/lövésszám tervezés alapja.


## Szakirodalmi pozicionálás — VQE-összefoglalók és hardveres demonstrációk

**[cerezo2021]** Cerezo, M., Arrasmith, A., Babbush, R., Benjamin, S., Endo, S., Fujii, K., McClean, J., Mitarai, K., Yuan, X., Cincio, L., Coles, P. (2021). Variational quantum algorithms. *Nature Reviews Physics*, **3** 625-644.
  DOI: [10.1038/s42254-021-00348-9](https://doi.org/10.1038/s42254-021-00348-9)
  *Felhasználás:* Variációs kvantumalgoritmusok áttekintése (trainálhatóság, pontosság, hatékonyság nyitott kérdései).

**[bharti2022]** Bharti, K., Cervera-Lierta, A., Kyaw, T., Haug, T., Alperin-Lea, S., Anand, A., Degroote, M., Heimonen, H., Kottmann, J., Menke, T., Mok, W., Sim, S., et al. (2022). Noisy intermediate-scale quantum algorithms. *Reviews of Modern Physics*, **94** 015004.
  DOI: [10.1103/revmodphys.94.015004](https://doi.org/10.1103/revmodphys.94.015004)
  *Felhasználás:* NISQ-algoritmusok áttekintése; a VQE tágabb keretei.

**[preskill2018]** Preskill, J. (2018). Quantum Computing in the NISQ era and beyond. *Quantum*, **2** 79.
  DOI: [10.22331/q-2018-08-06-79](https://doi.org/10.22331/q-2018-08-06-79)
  *Felhasználás:* A „NISQ” korszak fogalmának és korlátainak alapműve.

**[kandala2019]** Kandala, A., Temme, K., Córcoles, A., Mezzacapo, A., Chow, J., Gambetta, J. (2019). Error mitigation extends the computational reach of a noisy quantum processor. *Nature*, **567** 491-495.
  DOI: [10.1038/s41586-019-1040-7](https://doi.org/10.1038/s41586-019-1040-7)
  *Felhasználás:* A hibaenyhítés hardveres kiterjesztése a zajos processzor elérhetőségére (ZNE hardveren).


## Szakirodalmi pozicionálás — hibaenyhítés és kiolvasási hiba

**[vandenberg2022trex]** van den Berg, E., Minev, Z., Temme, K. (2022). Model-free readout-error mitigation for quantum expectation values. *Physical Review A*, **105** 032620.
  DOI: [10.1103/physreva.105.032620](https://doi.org/10.1103/physreva.105.032620)
  *Felhasználás:* A TREX (twirled readout error extinction) eredeti közleménye: az IBM Runtime resilience 1 szintjének módszere.

**[majumdar2023]** Majumdar, Ritajit, Rivero, Pedro, Metz, Friederike, Hasan, Areeq, Wang, Derek S (2023). Best practices for quantum error mitigation with digital zero-noise extrapolation. *arXiv*.
  DOI: [10.48550/arXiv.2307.05203](https://doi.org/10.48550/arXiv.2307.05203)
  *Felhasználás:* Bevált gyakorlatok a digitális ZNE-hez (zajerősítés, extrapoláció, kompozíció) — preprint.

**[belaloui2025]** Belaloui, Nacer Eddine, Tounsi, Abdellah, Khamadja, Abdelmouheymen Rabah, Benkadour, Hamza, Louamri, Mohamed Messaoud, Benslama, Achour, Rouabah, Mohamed Taha (2025). Improving VQE Parameter Quality on Noisy Quantum Processors with Cost-Effective Readout Error Mitigation. *arXiv*.
  DOI: [10.48550/arXiv.2508.15072](https://doi.org/10.48550/arXiv.2508.15072)
  *Felhasználás:* VQE-paraméterek minősége kiolvasási hibaenyhítéssel valódi IBM-hardveren (T-REx) — preprint.

**[aharonov2025]** Aharonov, Dorit, Alberton, Ori, Arad, Itai, Atia, Yosi, Bairey, Eyal, Dov, Matan Ben, Berkovitch, Asaf, Brakerski, Zvika, Cohen, Itsik, Fuchs, Eran, Golan, Omri, Golan, Or, et al. (2025). Reliable high-accuracy error mitigation for utility-scale quantum circuits. *arXiv*.
  DOI: [10.48550/arXiv.2508.10997](https://doi.org/10.48550/arXiv.2508.10997)
  *Felhasználás:* Karakterizáció-alapú hibaenyhítés (QESEM) a ZNE-vel szemben — preprint.


## Szakirodalmi pozicionálás — optimalizálás zajban és kiválasztási torzítás

**[bonetmonroig2023]** Bonet-Monroig, X., Wang, H., Vermetten, D., Senjean, B., Moussa, C., Bäck, T., Dunjko, V., O'Brien, T. (2023). Performance comparison of optimization methods on variational quantum algorithms. *Physical Review A*, **107** 032407.
  DOI: [10.1103/physreva.107.032407](https://doi.org/10.1103/physreva.107.032407)
  *Felhasználás:* Gradiensmentes optimalizálók (SLSQP, COBYLA, CMA-ES, SPSA) összehasonlítása kis molekulákon.

**[singh2023]** Singh, H., Majumder, S., Mishra, S. (2023). Benchmarking of different optimizers in the variational quantum algorithms for applications in quantum chemistry. *The Journal of Chemical Physics*, **159** 044117.
  DOI: [10.1063/5.0161057](https://doi.org/10.1063/5.0161057)
  *Felhasználás:* Optimalizálók összehasonlítása kvantumkémiai VQA-ban, ideális és zajos szimulátoron, IBM-zajmodellel.

**[illesova2025]** Illésová, S., Novák, V., Bezděk, T., Possel, C., Beseda, M. (2025). Numerical Optimization Strategies for the Variational Hamiltonian Ansatz in Noisy Quantum Environments. *arXiv*.
  DOI: [10.48550/arXiv.2505.22398](https://doi.org/10.48550/arXiv.2505.22398)
  *Felhasználás:* Nyolc optimalizáló a H2, H4, LiH VHA-feladatán; a lövészaj átrendezi a sorrendet — preprint.

**[novak2025]** Novák, Vojtěch, Illésová, Silvie, Bezděk, Tomáš, Zelinka, Ivan, Beseda, Martin (2025). Reliable Optimization Under Noise in Quantum Variational Algorithms. *arXiv*.
  DOI: [10.48550/arXiv.2511.08289](https://doi.org/10.48550/arXiv.2511.08289)
  *Felhasználás:* Lövészaj okozta hamis minimumok és „winner's curse” torzítás VQE-ben — preprint.

**[li2023kitaev]** Li, A., Alam, M., Iadecola, T., Jahin, A., Job, J., Kurkcuoglu, D., Li, R., Orth, P., Özgüler, A., Perdue, G., Tubman, N. (2023). Benchmarking variational quantum eigensolvers for the square-octagon-lattice Kitaev model. *Physical Review Research*, **5** 033071.
  DOI: [10.1103/physrevresearch.5.033071](https://doi.org/10.1103/physrevresearch.5.033071)
  *Felhasználás:* VQE-benchmark a Kitaev-modellen; a mért energia a lövészaj miatt az alapállapot alá eshet.

**[wang2021]** Wang, S., Fontana, E., Cerezo, M., Sharma, K., Sone, A., Cincio, L., Coles, P. (2021). Noise-induced barren plateaus in variational quantum algorithms. *Nature Communications*, **12** 6961.
  DOI: [10.1038/s41467-021-27045-6](https://doi.org/10.1038/s41467-021-27045-6)
  *Felhasználás:* Zaj okozta barren plateau: a mély áramkörök zajos tanulhatatlansága (az UCCSD mélységi fal értelmezéséhez).


## Szakirodalmi pozicionálás — zajmodellek validálása

**[bautra2026]** Bautra, Edgars, Dimitrijevs, Maksims, Yakaryilmaz, Abuzer (2026). Evaluating Calibration-Based Digital Twins for IBM Quantum Hardware Simulation. *arXiv*.
  DOI: [10.48550/arXiv.2603.14607](https://doi.org/10.48550/arXiv.2603.14607)
  *Felhasználás:* Kalibrációból épített digitális ikrek összevetése valódi IBM-hardverrel — preprint.

**[ji2026]** Ji, Y., Roth, M., Kreplin, D., Polian, I., Wilhelm, F. (2026). Data-efficient quantum noise modeling via machine learning. *Physical Review Applied*, **25** 034051.
  DOI: [10.1103/5r9m-y6z6](https://doi.org/10.1103/5r9m-y6z6)
  *Felhasználás:* Adathatékony zajmodellezés gépi tanulással, gyártói kalibrációs adatból kiindulva.


## Szakirodalmi pozicionálás — benchmark-platformok és reprodukálhatóság

**[cirstoiu2023]** Cirstoiu, C., Dilkes, S., Mills, D., Sivarajah, S., Duncan, R. (2023). Volumetric Benchmarking of Error Mitigation with Qermit. *Quantum*, **7** 1059.
  DOI: [10.22331/q-2023-07-13-1059](https://doi.org/10.22331/q-2023-07-13-1059)
  *Felhasználás:* A hibaenyhítés volumetrikus benchmarkolása (Qermit) valódi eszközökön.

**[cosentino2026]** Cosentino, Alessandro, Li, Changhao, Russo, Vincent, Chase, Bradley A., Lubinski, Tom, Niu, Siyuan, Patel, Neer, Shammah, Nathan, Zeng, William J. (2026). Metriq: A Collaborative Platform for Benchmarking Quantum Computers. *arXiv*.
  DOI: [10.48550/arXiv.2603.08680](https://doi.org/10.48550/arXiv.2603.08680)
  *Felhasználás:* A Metriq nyílt, együttműködő benchmark-platform — preprint.

**[lall2025]** Lall, D., Agarwal, A., Zhang, W., Lindoy, L., Lindström, T., Webster, S., Hall, S., Chancellor, N., Wallden, P., Garcia-Patron, R., Kashefi, E., Kendon, V., et al. (2025). A Review and Collection of Metrics and Benchmarks for Quantum Computers: definitions, methodologies and software. *150th anniversary of the Metre Convention — From Units to the Universe*.
  DOI: [10.59161/azye8097](https://doi.org/10.59161/azye8097)
  *Felhasználás:* Kvantumszámítógép-metrikák és -benchmarkok áttekintése (definíciók, módszertan, szoftver).

**[koster2026]** Köster, Dominik, Franz, Maja, Zec, Benjamin, Hoess, Nicole, Ramsauer, Ralf, Mauerer, Wolfgang (2026). Works on My QPU: Reproducibility in Quantum Computing Research. *arXiv*.
  DOI: [10.48550/arXiv.2607.08348](https://doi.org/10.48550/arXiv.2607.08348)
  *Felhasználás:* A kvantumszámítási kutatás reprodukálhatósága nagy léptékben — preprint.


---

## Felhasznált szoftverek

A futásidőben ténylegesen betöltött verziókat a `requirements.lock` és minden
eredményrekord `*_version` mezői rögzítik. Az indoklást lásd:
[`docs/plan/00_master_plan.md`](plan/00_master_plan.md), 4. fejezet.

| Szoftver | Verzió | Licenc | Hivatkozás |
|---|---|---|---|
| Qiskit | 1.4.6 | Apache-2.0 | [javadiabhari2024] |
| Qiskit Aer | 0.17.2 | Apache-2.0 | [javadiabhari2024] |
| Qiskit Nature | 0.7.2 | Apache-2.0 | [javadiabhari2024] |
| Qiskit Algorithms | 0.3.1 | Apache-2.0 | [javadiabhari2024] |
| Qiskit IBM Runtime | 0.41.1 | Apache-2.0 | [javadiabhari2024] |
| Mitiq | 0.47.0 | **GPL-3.0** | [larose2022] |
| PySCF | 2.14.0 | Apache-2.0 | [sun2018], [sun2020] |
| NumPy | 1.26.4 | BSD-3-Clause | [harris2020] |
| SciPy | 1.13.1 | BSD-3-Clause | [virtanen2020] |
| Cirq (core) | 1.4.1 | Apache-2.0 | — (a Mitiq tranzitív függősége) |
| ply | 3.11 | BSD-3-Clause | — (a Mitiq QASM-elemzőjének rejtett függősége) |

> **Licencfigyelem.** A Mitiq **GPL-3.0** licencű, a VQEBD viszont MIT. Ezért a Mitiq
> **opcionális, futásidőben betöltött** komponens: nem linkeljük be és nem terjesztjük
> újra. A Mitiq-függő kódút egyetlen modulba, a `src/vqebd/mitigation/mitiq_zne.py`-be
> van zárva, és a `mitiq` extra nélkül a rendszer teljes funkcionalitással működik.
> Részletek: [`docs/adr/ADR-0003-mitigacios-architektura.md`](adr/ADR-0003-mitigacios-architektura.md).

---

## Online források

| Forrás | URL | Utolsó ellenőrzés |
|---|---|---|
| Qiskit dokumentáció | <https://quantum.cloud.ibm.com/docs> | 2026-09-22 |
| Qiskit Nature dokumentáció | <https://qiskit-community.github.io/qiskit-nature/> | 2026-09-22 |
| Mitiq dokumentáció | <https://mitiq.readthedocs.io/> | 2026-09-22 |
| PySCF dokumentáció | <https://pyscf.org/> | 2026-09-22 |
| Metriq benchmark-platform (Unitary Foundation) | <https://metriq.info/> | 2026-09-22 |
| Unitary Foundation | <https://unitary.foundation/> | 2026-09-22 |
| QOSF — Quantum Open Source Foundation | <https://qosf.org/> | 2026-09-22 |
| Zenodo | <https://zenodo.org/> | 2026-09-22 |
| Keep a Changelog 1.1.0 | <https://keepachangelog.com/en/1.1.0/> | 2026-09-22 |
| Semantic Versioning 2.0.0 | <https://semver.org/> | 2026-09-22 |
| Conventional Commits 1.0.0 | <https://www.conventionalcommits.org/en/v1.0.0/> | 2026-09-22 |
| Citation File Format (CFF) | <https://citation-file-format.github.io/> | 2026-09-22 |

---

## Változásnapló

| Verzió | Dátum | Változás |
|---|---|---|
| 1.0.0 | 2026-09-22 | Első kiadás. 37 tétel, ebből 35 gépileg DOI-validált. |
| 1.1.0 | 2026-09-25 | Fázis 5: +2 tétel (student1908, wecker2015) — statisztika és mérési módszertan. |
| 1.2.0 | 2026-11-02 | Szakirodalmi pozicionálás: +20 tétel (VQE-összefoglalók, hibaenyhítés és kiolvasás, optimalizálás zajban, zajmodellek, benchmark-platformok). |

*Készítők: Kormos Attila, Claude AI (Anthropic, Claude Opus 5) — MIT licenc*
