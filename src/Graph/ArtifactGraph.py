from collections import deque
from typing import List, Set

import matplotlib.pyplot as plt
from Tuleap.RestClient.Projects import Projects
from Tuleap.RestClient.Trackers import Tracker
from igraph import Graph, plot, load

from src.Graph.ArtifactsWalker import ArtifactsWalker


class ArtifactGraph:
    def __init__(self):
        self.__graph = Graph(directed=True,
                             vertex_attrs={"name": []},
                             edge_attrs={"type": []})
        self.__paths: List[List[int]] = []
        self.__artifacts: List[str] = []

    def get_artifacts(self) -> List[str]:
        """
        Returns artifacts from last successful request.
        :return:
        """
        return self.__artifacts

    def get_paths(self, n: int = float('inf')) -> List[List[str]]:
        """
        Returns at most the n firsts paths found by check_artifact_connection or search_all_paths_between_artifacts
        sorted by length.

        :param int n: Number of paths to retrieve, default all.
        :return List[List[str]]: the list of the paths.
        """
        string_paths: List[List[str]] = []
        for path in self.__paths:
            tmp_path = []
            for vertex in path:
                tmp_path.append(self.__graph.vs[vertex]["name"])
            string_paths.append(tmp_path)
        return sorted(string_paths, key=lambda p: len(p))[:min(len(self.__paths), n)]

    def fill_graph_from_artifact(self, art_id: str, walker: ArtifactsWalker, through_reverse_links=True,
                                 depth_limit: int = float('inf')) -> None:
        """
        Fills this graph with artifacts accessible from art_id.

        :param str art_id: artifact from which to start the walk or git reference
        :param through_reverse_links: whether to search though incoming links.
        :param depth_limit: limit of the search.
        :return:
        """
        if walker.walk(art_id, through_reverse_links, depth_limit):
            self.__add_convert_vertices_edges(walker)
        else:
            raise Exception("Cannot access the given reference")

    def __add_convert_vertices_edges(self, walker: ArtifactsWalker) -> None:
        self.__add_vertices([str(vertex) for vertex in walker.get_vertices_names()])

        types = [str(edge[2]) for edge in walker.get_edges()]

        self.__add_edges(get_edges_full_names(walker), types)

    def fill_graph_from_project(self, project_name: str, walker: ArtifactsWalker, project_getter: Projects,
                                tracker_getter: Tracker):
        """
        Fills the graph with all artifacts of the given project. Also retrieves links to and from commits.

        :param int project_name: the project name.
        :return:
        """

        if walker.retrieve_graph_from_project(project_name, tracker_getter, project_getter):
            self.__add_convert_vertices_edges(walker)
        else:
            raise Exception("Cannot access the given reference")

    def check_artifacts_connection(self, art_id1: str, art_id2: str, types=None, mode="out") -> bool:
        """
        Checks whether the two artifacts are connected by a path.
        The path is accessible with the method gat_paths.

        :param List[str] types: List of link types to search through. default keeps all types.
        :param str art_id1: starting artifact.
        :param str art_id2: ending artifact.
        :param mode: 'out': walking through edges the normal way.
                     'in': walking through edges backwards (i.e. reverting all edges).
                     'all': walking through edges both ways.
        :return: whether the two artifacts are connected or not.
        """
        # getting igraph's vertices id
        vertex_id1, vertex_id2 = -1, -1
        for vtx in self.__graph.vs:
            if art_id1 == vtx["name"]:
                vertex_id1 = vtx.index
            if art_id2 == vtx["name"]:
                vertex_id2 = vtx.index

        if vertex_id1 == -1 or vertex_id2 == -1 or vertex_id2 == vertex_id1:
            return False

        if types:
            edges = self.__graph.es.select(type_in=types)
            subgraph: Graph = self.__graph.subgraph_edges(edges, delete_vertices=False)
        else:
            subgraph: Graph = self.__graph
        reached_vertices, _, parents = subgraph.bfs(vertex_id1, mode=mode)

        if vertex_id2 not in reached_vertices:
            return False

        # building the path from the end
        path = []
        while parents[vertex_id2] != vertex_id2:
            path.append(vertex_id2)
            vertex_id2 = parents[vertex_id2]
        path.append(vertex_id2)
        self.__paths = [reversed(path)]
        return True

    def search_all_paths_between_artifacts(self, art_id1: str, art_id2: str, types=None, mode="out",
                                           cutoff: int = -1) -> bool:
        """
        Computes all simple paths between the two artifacts.
        The result is accessible with the method gat_paths.

        :param int cutoff: max length of the paths. Default -1 means no limit.
        :param List[str] types: List of link types to search through. default keeps all types.
        :param str art_id1: starting artifact.
        :param str art_id2: ending artifact.
        :param mode: 'out': walking through edges the normal way.
                     'in': walking through edges backwards (i.e. reverting all edges).
                     'all': walking through edges both ways.
        :return: whether the two artifacts are connected or not.
        """
        if art_id1 not in self.__graph.vs["name"] or art_id2 not in self.__graph.vs["name"]:
            return False

        if types:
            edges = self.__graph.es.select(type_in=types)
            subgraph: Graph = self.__graph.subgraph_edges(edges, delete_vertices=False)
        else:
            subgraph: Graph = self.__graph
        self.__paths = subgraph.get_all_simple_paths(art_id1, art_id2, mode=mode, cutoff=cutoff)
        return len(self.__paths) > 0

    def request_non_connected_vertices(self):
        self.__artifacts = [subgraph.vs["name"] for subgraph in self.__graph.components("weak").subgraphs() if
                            len(subgraph.vs) <= 1]
        return True

    def search_all_accessible_by_type(self, art_name: str, artifact_type: str, mode: str = "all") -> bool:
        """
        Return all vertices of the given type reachable y the given artifact, without going through firsts artifacts of
        the given type. It ignores parent.

        :param str art_name: Artifact from which to start the walk.
        :param str artifact_type: Artifact type to return. (ex: story, git, test...).
        :param str mode: Whether to go through "in", "out" or "all" edges.
        :return: whether the search succeeded or not.
        """

        if art_name not in self.__graph.vs["name"]:
            return False

        to_visit: deque[str] = deque()
        visited: Set[str] = set()
        target_vertices = set()

        to_visit.append(art_name)
        while to_visit:
            current_vertex = to_visit.popleft()
            if current_vertex in visited:
                continue

            visited.add(current_vertex)
            if not current_vertex.split(" ")[0] == artifact_type:
                neighbors = self.__get_filtered_neighbors(current_vertex, mode=mode)
                for neighbor in neighbors:
                    to_visit.append(neighbor)
            else:
                target_vertices.add(current_vertex)
        self.__artifacts = target_vertices
        return True

    def __get_filtered_neighbors(self, current_vertex: str, mode: str = "all") -> List[str]:
        """
        Returns neighbors except those accessible by an incoming _is_child edge.

        :param current_vertex:
        :param mode: in, out or all
        :return:
        """
        neighbors = []
        if mode in ["all", "in"]:
            in_edges_ids = self.__graph.incident(current_vertex, mode="in")
            in_edge = self.__graph.es[in_edges_ids]
            filtered_edges = in_edge.select(lambda edge: edge["type"] != "_is_child")
            in_edges_tuples = [edge.tuple for edge in filtered_edges]
            neighbors += [self.__graph.vs[edge[0]]["name"] for edge in in_edges_tuples]

        if mode in ["all", "out"]:
            out_edges_ids = self.__graph.incident(current_vertex, mode="out")
            out_edges_tuples = [edge.tuple for edge in self.__graph.es[out_edges_ids]]
            neighbors += [self.__graph.vs[edge[1]]["name"] for edge in out_edges_tuples]
        return neighbors

    def save_graph(self, filepath):
        self.__graph.save(filepath)

    def load_graph(self, filepath):
        self.__graph = load(filepath)

    def __add_vertices(self, names: List[str]):
        self.__graph.add_vertices(len(names), attributes={"name": names})

    def __add_edges(self, edges: List[List[str]], edge_type: List[str]):
        self.__graph.add_edges(edges, {"type": edge_type})

    def get_vertices(self):
        return self.__graph.vs["name"]

    def get_vertex_links(self, art_id: str):
        return [self.__graph.vs[edge.tuple[1]]["name"] for edge in self.__graph.es.select(_source=art_id)]

    def get_vertex_reverse_links(self, art_id: str):
        return [self.__graph.vs[edge.tuple[0]]["name"] for edge in self.__graph.es.select(_target=art_id)]

    def plot_graph(self):
        layout = self.__graph.layout_auto(dim=2)
        fig, ax = plt.subplots()
        plot(self.__graph, layout=layout, target=ax)
        plt.show()


def art_name_to_id(art_name: str) -> str:
    if art_name.startswith("git"):
        return art_name.split('/')[-1]
    else:
        return art_name.split("#")[1]


def get_edges_full_names(walker: ArtifactsWalker):
    """
    Converts edges with IDs (ie artifact ID or a commit sha1) to edges with names
    (ie git #path/sha1 or art #1234)
    :param walker:
    :return:
    """
    edges_with_names = []
    for edge in walker.get_edges():
        source, target = "", ""
        for vertex_name in walker.get_vertices_names():
            vertex_id = art_name_to_id(vertex_name)
            if edge[0] == vertex_id:
                source = vertex_name
            if edge[1] == vertex_id:
                target = vertex_name
            if source and target:
                break
        edges_with_names.append([source, target])

    return edges_with_names
