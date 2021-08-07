import pandas as pd

# function extracting needed key values from literature data
def get_literature_keys(literature, member):
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


# function extracting needed key values from literature data
def add_literature(all_papers, relationships, current_paper, newPaper):
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