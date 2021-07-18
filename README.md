# scientific-paper-dependencies

This project gives you recommendations of which scientific papers might of interest for you based on your own bibliography. The idea standing behind the recommendation is simple. The more often a paper is cited, the more important it should be for the field of research.

The project extracts the papers of your bibliograhpy and gets their metadata (ID, referenced paper and papers citing the respective paper) via the paper's DOI from semanticscholar. Then all papers are linked and plotted, identifying which papers are mentioned often.

As the number of papers increases quickly, only the papers in your own bibliography are show and the papers which have the most links (currently the topmost 10 %). With this the graph is cleaned as much as possbile without missing to much information.

Finally, recommendations on possibly interesting papers are given. For this, the papers which are not included in your own bibliography but have the most links (currently the topmost 10 % as well) are pointed out for you to read.
