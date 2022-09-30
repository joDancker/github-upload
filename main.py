"""Functions and workflow for analyzing dependencies between scientific bibliographies.

This project gives you recommendations of which scientific papers might be
of interest for you based on your own scientific bibliography. The idea standing behind
the recommendations is simple. The more often a paper is cited, the more
important it should be for your field of research.

MIT license

List of author(s)
Jonte Dancker

"""

import os
import warnings

import bibtexparser
import numpy as np
import pandas as pd
from bibtexparser.bibdatabase import as_text
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding
from d3graph import d3graph, vec2adjmat

from utils import access_API, add_literature, get_literature_keys

# %%

# read data from bib-file
with open("literature.bib") as bibtex_file:
    parser = BibTexParser()
    parser.customization = homogenize_latex_encoding
    bib_database = bibtexparser.load(bibtex_file, parser=parser)


# relationship / connections between papers
relationships = pd.DataFrame({"from": [], "to": []})
# paper information
all_papers = pd.DataFrame(
    {
        "paperID": [],
        "authors": [],
        "year": [],
        "doi": [],
        "title": [],
        "occurence": [],
    }
)

# %% Add Literature Data

counter_connected_papers = 1
# Save author, year, title and doi in dict-variable
for entries in bib_database.entries:

    if "doi" not in entries:  # IF entry does not have DOI
        continue

    # get DOI from Literature
    DOI = as_text(entries["doi"])

    # get json-file of literature via DOI
    resp = access_API("https://api.semanticscholar.org/v1/paper/" + DOI)

    # If user wants to exit after server is not allowing download break
    # whole download loop
    if resp is None:
        break

    # If something else went wrong.
    if resp.status_code != 200:
        continue

    # giving user status feedback
    print(f"Paper {counter_connected_papers} of {len(bib_database.entries)}")

    # another paper is added
    counter_connected_papers += 1

    # get keys of current paper available in bibtex-file
    availablePaper = get_literature_keys(resp.json(), "owned")

    # add available paper to all papers
    if any(
        all_papers["paperID"].isin(availablePaper["paperID"])
    ):  # IF available paper is already saved
        # count occurence of paper up by 1
        all_papers.loc[
            all_papers["paperID"] == availablePaper.loc[0, "paperID"], "occurence"
        ] += 1
        # change membership to owned
        all_papers.loc[
            all_papers["paperID"] == availablePaper.loc[0, "paperID"], "member"
        ] = "owned"
    else:
        # add available paper to all papers
        all_papers = pd.concat([all_papers, availablePaper], ignore_index=True)

    # loop through referenced literature and get key values
    for ref in range(len(resp.json()["references"])):
        referencedPaper = get_literature_keys(resp.json()["references"][ref], "new")
        all_papers, relationships = add_literature(
            all_papers, relationships, availablePaper, referencedPaper
        )

    # loop through cited literature and get key values
    citedLiterature = pd.DataFrame({})
    for ref in range(len(resp.json()["citations"])):
        cited_papers = get_literature_keys(resp.json()["citations"][ref], "new")
        all_papers, relationships = add_literature(
            all_papers, relationships, availablePaper, cited_papers
        )


# %% Clean Data by deleting uninteresting papers (less often cited/ referenced papers)
number_of_extracter_papers = len(all_papers)
# delete all new papers with a number of occurence that lie below a quantile threshold
idx_delete_papers = all_papers.index[
    (all_papers["occurence"] <= all_papers["occurence"].quantile(0.95))
    & (all_papers["member"] == "new")
]
all_papers.drop(idx_delete_papers, inplace=True)

# delete connections in graph
idx_delete_papers = np.flatnonzero(
    ~relationships["from"].isin(all_papers["paperID"])
    | ~relationships["to"].isin(all_papers["paperID"])
)
relationships.drop(idx_delete_papers, inplace=True)

# remove paper without connections
idx_delete_papers = all_papers.index[
    ~all_papers["paperID"].isin(relationships["from"])
    & ~all_papers["paperID"].isin(relationships["to"])
]
all_papers.drop(idx_delete_papers, inplace=True)


# %% identify new papers of possible interest
# interesting papers are identified by their number of occurences. The more often a
# paper is cited the better is must be and the higher its impact on the field can be
# assumed.
# change membership to recommended
all_papers.loc[
    (all_papers["occurence"] >= all_papers["occurence"].quantile(0.98))
    & (all_papers["member"] == "new"),
    "member",
] = "recommended"


# %% User feedback
print(
    f"{counter_connected_papers} of {len(bib_database.entries)}"
    "papers from bibtex-file were added to graph. \n"
)
print(
    f"{len(all_papers)} of {len(all_papers)+number_of_extracter_papers} "
    "extracted papers (cited and referenced) are shown in graph. \n"
)
print(
    f"The following {sum(all_papers['member']=='recommended')} "
    "papers might be of interest: \n"
)

recommended_papers = all_papers.loc[
    all_papers["member"] == "recommended",
    ["authors", "year", "doi", "title", "occurence"],
]

print(recommended_papers)

# save list of recommended papers
fname = "recommended_papers.csv"
overwrite = True
if not os.path.exists(fname) or overwrite:
    recommended_papers.to_csv(fname, index=False, float_format="%.2f")
else:
    warnings.warn(
        f"Not saving to {fname}, that file already exists and overwrite is {overwrite}."
    )

# %% PLOTTING
# Draw graph
# Set source and target nodes
source = relationships["from"]
target = relationships["to"]
weight = np.ones(len(relationships))

# Create adjacency matrix
adjmat = vec2adjmat(source, target, weight=weight)

# assign colors to nodes
colors = ["#a9a9a9", "#1e90ff", "#ff8c00"]  # ["darkgray", "dodgerblue", "darkorange"]
condition = [(all_papers["member"] == "owned"), (all_papers["member"] == "recommended")]
node_colors = np.select(condition, colors[1:], default=colors[0])

# Set node size by number of occurences in a variable manner so that paper with maximum
# number of occurence has always the same size independently of its number of occurence
maxValue = all_papers["occurence"].max()
minValue = all_papers["occurence"].min()
sizingFactor = 10 / (maxValue - minValue)
nodeSize = np.ceil((all_papers["occurence"] - minValue + 1) * sizingFactor).tolist()

# label papers by name of first author and year of publication
all_papers.loc[all_papers["authors"] == "", "authors"] = "X X"
all_papers["year"].fillna(0, inplace=True)
nodel_labels = [
    " ".join([author.split()[1], str(int(year))])
    for author, year in zip(all_papers["authors"], all_papers["year"])
]

# information of pop up window for each paper
tooltip = (
    "Authors: "
    + all_papers["authors"]
    + "\nYear: "
    + all_papers["year"].astype(int).astype(str)
    + "\nTitle: "
    + all_papers["title"]
    + "\nOccurences: "
    + all_papers["occurence"].astype(int).astype(str)
)
tooltip = tooltip.values

# Initialize and build force-directed graph
d3 = d3graph()
d3.graph(adjmat)

# Set node and edge properties
d3.set_node_properties(
    color=node_colors, size=nodeSize, label=nodel_labels, tooltip=tooltip
)

# show plot
fname = "paper_connections.html"
overwrite = True
if not os.path.exists(fname) or overwrite:
    d3.show(filepath=os.path.join(os.path.abspath(os.getcwd()), fname))
else:
    d3.show()
    warnings.warn(
        f"Not saving to {fname}, that file already exists and overwrite is {overwrite}."
    )
