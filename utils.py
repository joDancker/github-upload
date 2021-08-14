"""Utility functions for the scientific-paper-dependencies project."""
import time

import pandas as pd
import requests


def get_literature_keys(literature, member):
    """Extract needed key values from literature data.

    Parameters
    ----------
    literature : dict
        contains all information about a paper extracted for semantic scholar.
    member : str
        identifies the membership of a paper. Can be "owned" if paper is part of the
        bibtex-file, "new" if paper is not part of the bibtex-file or "recommendend" if
        a "new" paper might be of interest for the reader.

    Returns
    -------
    data : pd.dataframe
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

    This function adds new papers to the existing, already saved, papers and also adds
    the relationsship between new papers and the paper extracted from the bibtex-file.
    If the new paper is already part of `all_papers` the paper is not added but its
    occurence is counted up by 1.

    Parameters
    ----------
    all_papers : pd.dataframe
        contains information about all papers which were either part of the bibtex-file
        or were already downloaded from semanitc scholar, including paperID, authors,
        DOI, title, number of occurences
    relationships : pd.dataframe
        contains information on how the papers in `all_papers` are related to each other
    current_paper : pd.dataframe
        contains information about the current paper from the bibtex-file
    newPaper : pd.dataframe
        contains information about the paper which is related to `current_paper`

    Returns
    -------
     all_papers : pd.dataframe
        contains updated information about all papers. The return value contains the
        additional information of `newPaper`
    relationships : pd.dataframe
        contains updated information on how the papers in `all_papers` are related to
        each other including the additional information of `newPaper`

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


def access_API(url):
    """Access semantic scholar API repeatedly with a time delay.

    This function accesses the semantic scholar API via a given link and downloads the
    meta data of a respective paper. As the semantic scholar APi denies access if too
    many downloads per 5 minute window were tried, the function gives the user a
    feedback. The user can either wait or exit the download loop. If the user wants to
    wait, the functions tries to download the meta information for several times after
    a short time delay.

    Parameters
    ----------
    url : str
        contains string pointing to semantic scholar API for downloading the paper's
        metadata

    Returns
    -------
     resp : dict
        contains meta data of downloaded paper.

    """
    retries = 0
    timeout = 5
    while retries < 10:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp
        elif resp.status_code == 403 and retries == 0:
            # Check if server does not allow download on the first try
            user_input = input(
                "You exceeded 100 requests per 5 minute window. "
                "Do you want to wait (w) or exit (e)?: "
            )
            # if user wants to exit reading
            if user_input == "e":
                return None
            else:
                print(f"Sleeping for {timeout} seconds")
                time.sleep(timeout)
                retries += 1

        elif resp.status_code == 403:
            print(f"Access denied. Sleeping for another {timeout} seconds")
            time.sleep(timeout)
            retries += 1
        # If something else went wrong.
        else:
            print("Paper was not found in database")
            return resp
    return resp
