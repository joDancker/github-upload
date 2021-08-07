import pandas as pd


def get_literature_keys(literature, member):
    """Extract needed key values from literature data.

    This method extracts the needed key values

    Parameters
    ----------
    literature : dict
        contains all information about a paper extracted for semantic scholar.
    member : string
        identifies the membership of a paper. Can be "owned" if paper is part of the
        bibtex-file, "new" if paper is not part of the bibtex-file or "recommendend" if a
        "new" paper might be of interest for the reader.


    Returns
    -------
     data : dataframe
        contains needed key values of the paper

    """

    data = pd.DataFrame(
        {
            "paperID": literature["paperId"],
            "authors": [literature["authors"]],
            "year": literature["year"],
            "doi": literature["doi"],
            "title": literature["title"],
            "occurence": 1,
        }
    )

    # add category to paper
    raw_cat = pd.Categorical(
        member, categories=["owned", "new", "recommended"], ordered=False
    )
    data["member"] = raw_cat

    return data


def add_literature(all_papers, relationships, current_paper, newPaper):
    """Add new literature data and relationship to existing literature data.

    This method adds new papers to the existing, already saved, papers and also adds the
    relationsship between new papers and the paper extracted from the bibtex-file. If the
    new paper is already part of `all_papers` the paper is not added but its occurence is
    counted up by 1.

    Parameters
    ----------
    all_papers : dataframe
        contains information about all papers which were either part of the bibtex-file or
        were already downloaded from semanitc scholar, including paperID, authors, DOI,
        title, number of occurences
    relationships : dataframe
        contains information on how the papers in `all_papers` are related to each other.
    current_paper : dataframe
        contains information about the current paper from the bibtex-file
    newPaper : dataframe
        contains information about the paper which is related to `current_paper`

    Returns
    -------
     all_papers : dataframe
        contains updated information about all papers. The return value contains the
        additional information of `newPaper`
    relationships : dataframe
        contains updated information on how the papers in `all_papers` are related to each
        other including the additional information of `newPaper`

    """

    # add relationship between available and referenced paper
    relation = {
        "from": current_paper.loc[0, "paperID"],
        "to": newPaper.loc[0, "paperID"],
    }
    relationships = relationships.append(relation, ignore_index=True)

    # add referenced paper to all papers
    if any(
        all_papers["paperID"].isin(newPaper["paperID"])
    ):  # IF referenced paper is already saved
        # count occurence of paper up by 1
        all_papers.loc[
            all_papers["paperID"] == newPaper.loc[0, "paperID"], "occurence"
        ] += 1
    else:
        # add referenced paper to all papers
        all_papers = pd.concat([all_papers, newPaper], ignore_index=True)

    return all_papers, relationships
