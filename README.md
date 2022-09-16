# ARTIFACT REFERENCE GRAPH

This project aims to bring tools to better analyse the graph formed by artifacts and their links.
It is a standalone app that queries Tuleap's REST API to build a graph from a project.

See `demo.ipynb` for code examples

## What this app can do

- Locally rebuild and save the graph of artifacts and commits from a project, an artifact or a commit.
- Check whether there is a connection between two artifacts, show paths between them.
- Search for non-connected artifacts (forgotten reference ?).
- Search for all artifacts of a certain type (story for example) linked to a certain artifact.

## Limitations

- Does not take into account references other than those pointing to commits or artifacts.
- Cross-reference search from commits (when building the graph) can only be done from one git repository.
- When there is a reference from another repository, the repository path in the graph vertex is "unknown_repo".
- On graph building, does not check if referenced artifacts come from another project.
- 50 trackers max when building from project.
- no dynamic update, need to build the graph from scratch.

## GitHistory

The aim is to bring more traceability by adding the possibility to search for
all commits whose code have been overwritten by a given commit.
This is a side task that I did not have time to plug into the graph part and
it requires to have the repository locally.

## How to install
```sh
nix-shell
virtualenv venv
source venv/bin/activate
git clone https://github.com/djurodrljaca/tuleap-rest-api-client
(cd tuleap-rest-api-client && python setup.py install)
jupyter notebook
```
