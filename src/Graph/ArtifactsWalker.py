import re
from typing import List, Tuple

from Tuleap.RestClient.ArtifactParser import ArtifactParser
from Tuleap.RestClient.Artifacts import Artifacts
from Tuleap.RestClient.Projects import Projects
from Tuleap.RestClient.Trackers import Tracker

from src.ApiClientAddon.APIConstants import ARTIFACTS_LIMIT, TRACKERS_LIMIT
from src.ApiClientAddon.CommitAddon import Commits
from src.ApiClientAddon.CommitParser import CommitParser


class ArtifactsWalker:
    def __init__(self, commit_getter: Commits, artifact_getter: Artifacts):
        self.__artifact_getter = artifact_getter
        self.__commit_getter = commit_getter
        self.__artifacts_ids: List[str] = []
        self.__artifacts_names: List[str] = []
        self.__edges: List[List[str]] = []

    def get_vertices(self) -> List[str]:
        return self.__artifacts_ids

    def get_vertices_names(self) -> List[str]:
        return self.__artifacts_names

    def get_edges(self) -> List[List[str]]:
        return self.__edges

    def reset(self) -> None:
        """
        Empty vertices and edges.
        :return:
        """
        self.__artifacts_ids = []
        self.__artifacts_names = []
        self.__edges = []

    def walk(self, start_art_id: str, through_reverse_links=True, depth_limit: int = float('inf'),
             repository_id: int = None) -> bool:
        """
        Explore the graph from the given artifact, going through forward and backward links,
        depth first search.

        Saves vertices and edges (does not delete the ones from previous calls to this method).

        Goes through artifacts and git references (not through other references).

        :param repository_id: ID of the repository to search references in. Default None means that the walker won't
        search references from commits.
        :param int depth_limit: maximum depth to fetch artifacts.
        :param str start_art_id: artifact from which to start the walk. Can be a commit SHA1.
        :param bool through_reverse_links: whether to explore graph through incoming links.
        :return: whether the walk succeeded or not (ie artifact exists or not)
        """
        if not self.__get_artifact_data(start_art_id) and not self.__get_commit_data(start_art_id, repository_id):
            return False
        if start_art_id in self.__artifacts_ids:
            return True

        def visit_neighbors(art_id: str, depth: int) -> None:
            """
            Explore neighbors of the given artifact recursively, appending them to __vertices.

            :param int depth: current depth of search from the starting artifact.
            :param int art_id: the artifact from which exploring neighbors.
            :return: whether the walk succeeded or not
            """
            if art_id in self.__artifacts_ids:
                return

            parsed_commit = CommitParser(dict())
            parsed_artifact = ArtifactParser(dict())
            if is_sha(art_id):
                parsed_commit = self.__get_parsed_commit(art_id, repository_id)
                if self.__commit_getter.is_repo_valid() and parsed_commit.is_valid():
                    art_name = "git #" + self.__commit_getter.get_path() + art_id
                else:
                    art_name = "git #unknown_repo/" + art_id
            else:
                parsed_artifact = self.__get_parsed_artifact(art_id)
                if parsed_artifact.is_valid():
                    art_name = parsed_artifact.get_name()
                else:
                    art_name = "unsupported_reference #" + art_id

            self.__artifacts_names.append(art_name)
            self.__artifacts_ids.append(art_id)

            if depth >= depth_limit:
                return

            if is_sha(art_id) and self.__commit_getter.is_repo_valid() and parsed_commit.is_valid():
                links, reverse_links = get_links_from_commit(parsed_commit)
                self.__create_edges(art_id, links, ["git"] * len(links))
                for neighbor in links:
                    visit_neighbors(neighbor, depth + 1)

                self.__create_reverse_edges(art_id, reverse_links, ["git"] * len(reverse_links))
                for neighbor in reverse_links:
                    visit_neighbors(neighbor, depth + 1)

            else:
                links, reverse_links, link_types, reverse_link_types, git_refs, reverse_git_refs = \
                    get_links_and_types_from_art(parsed_artifact)

                self.__create_edges(art_id, links, link_types)
                for neighbor in links:
                    visit_neighbors(neighbor, depth + 1)

                if through_reverse_links:
                    self.__create_reverse_edges(art_id, reverse_links, reverse_link_types)
                    for neighbor in reverse_links:
                        visit_neighbors(neighbor, depth + 1)

                # Git References
                self.__create_edges(art_id, git_refs, ["git"] * len(git_refs))
                for neighbor in git_refs:
                    visit_neighbors(neighbor, depth + 1)

                if through_reverse_links:
                    self.__create_reverse_edges(art_id, reverse_git_refs, ["git"] * len(reverse_git_refs))
                    for neighbor in reverse_git_refs:
                        visit_neighbors(neighbor, depth + 1)

        visit_neighbors(start_art_id, 0)
        return True

    def retrieve_graph_from_project(self, project_name: str, tracker_getter: Tracker, project_getter: Projects):
        success = project_getter.search_project(project_name)
        if success:
            success = project_getter.request_trackers(project_getter.get_data()[0]["id"],
                                                      limit=TRACKERS_LIMIT)

        if not success:
            return False

        for tracker in project_getter.get_data():
            art_offset = 0

            while True:
                tracker_getter.request_artifact_list(tracker['id'], limit=ARTIFACTS_LIMIT, offset=art_offset)
                if tracker_getter.get_data():
                    for art in tracker_getter.get_data():
                        self.walk(str(art["xref"]))
                art_offset += ARTIFACTS_LIMIT

                if len(tracker_getter.get_data()) < ARTIFACTS_LIMIT:
                    break
        self.reset()
        return True

    def __get_artifact_data(self, art_id) -> dict:
        if self.__artifact_getter.request_artifact(art_id):
            return self.__artifact_getter.get_data()
        return dict()

    def __get_commit_data(self, commit_id: str, repository_id: int) -> dict:
        if self.__commit_getter.request_commit(commit_id, repository_id):
            return self.__commit_getter.get_data()
        return dict()

    def __get_parsed_artifact(self, art_id: str) -> ArtifactParser:
        art_data = self.__get_artifact_data(art_id)
        return ArtifactParser(art_data)

    def __get_parsed_commit(self, commit_id: str, repo_id) -> CommitParser:
        commit_data = self.__get_commit_data(commit_id, repo_id)
        return CommitParser(commit_data)

    def __create_edges(self, art_id, neighbors_ids, types) -> None:
        self.__edges += [[art_id, neighbor_id, link_type] for neighbor_id, link_type in zip(neighbors_ids, types)
                         if [art_id, neighbor_id, link_type] not in self.__edges]

    def __create_reverse_edges(self, art_id, neighbors_ids, types) -> None:
        self.__edges += [[neighbor_id, art_id, link_type] for neighbor_id, link_type in zip(neighbors_ids, types)
                         if [neighbor_id, art_id, link_type] not in self.__edges]


def get_links_and_types_from_art(parsed_artifact: ArtifactParser):
    links = [str(link) for link in parsed_artifact.get_links()]
    reverse_links = [str(link) for link in parsed_artifact.get_reverse_links()]
    git_refs = [ref.split("/")[-1] for ref in parsed_artifact.get_out_git_references()]
    reverse_git_refs = [ref.split("/")[-1] for ref in parsed_artifact.get_in_git_references()]
    link_types = parsed_artifact.get_links_types()
    reverse_link_types = parsed_artifact.get_reverse_links_types()

    return links, reverse_links, link_types, reverse_link_types, git_refs, reverse_git_refs


def get_links_from_commit(parsed_commit: CommitParser) -> Tuple[List[str], List[str]]:
    links, reverse_links = [], []
    for ref in parsed_commit.get_links():
        if ref.startswith("git #"):
            links.append(ref.split("/")[-1])
        elif is_artifact_reference(ref):
            links.append(ref.split("#")[-1])
    return links, reverse_links


def is_sha(string: str) -> bool:
    sha_regex = re.compile(r"^[\da-f]{40}$")
    if sha_regex.match(string):
        return True
    return False


def is_artifact_reference(string: str) -> bool:
    art_regex = re.compile(r"^\w+ #\d+$")
    if art_regex.match(string):
        return True
    return False
