import unittest

from src.Graph.ArtifactGraph import ArtifactGraph


class TestArtifactGraphErrorCases(unittest.TestCase):
    def test_connection_no_vertex(self):
        graph = ArtifactGraph()
        self.assertFalse(graph.check_artifacts_connection("0", "1"))


class TestArtifactGraph(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = ArtifactGraph()
        self.graph._ArtifactGraph__add_vertices(["v1", "v2", "v3", "v4", "v5"])
        self.graph._ArtifactGraph__add_edges([["v1", "v2"],
                                              ["v2", "v3"],
                                              ["v4", "v2"]],
                                             ["None", "child", "parent"])

    def test_connection_default(self):
        self.assertTrue(self.graph.check_artifacts_connection("v1", "v2"))
        self.assertTrue(self.graph.check_artifacts_connection("v2", "v3"))
        self.assertTrue(self.graph.check_artifacts_connection("v1", "v3"))
        self.assertFalse(self.graph.check_artifacts_connection("v1", "v4"))
        self.assertTrue(self.graph.check_artifacts_connection("v4", "v3"))
        self.assertFalse(self.graph.check_artifacts_connection("v1", "v1"))

    def test_connection_types(self):
        self.assertTrue(self.graph.check_artifacts_connection("v1", "v3", types=["None", "child"]))
        self.assertFalse(self.graph.check_artifacts_connection("v1", "v3", types=["None"]))
        self.assertFalse(self.graph.check_artifacts_connection("v1", "v3", types=["None"]))

    def test_connection_modes(self):
        self.assertFalse(self.graph.check_artifacts_connection("v1", "v3", mode="in"))

        self.assertTrue(self.graph.check_artifacts_connection("v1", "v3", mode="out"))
        self.assertListEqual(self.graph.get_paths(), [["v1", "v2", "v3"]])

        self.assertFalse(self.graph.check_artifacts_connection("v1", "v4", mode="in"))
        self.assertFalse(self.graph.check_artifacts_connection("v1", "v4", mode="out"))

        self.assertTrue(self.graph.check_artifacts_connection("v1", "v4", mode="all"))
        self.assertListEqual(self.graph.get_paths(), [['v1', 'v2', 'v4']])

    def test_connection_all(self):
        self.assertTrue(self.graph.check_artifacts_connection("v1", "v4", mode="all", types=["None", "parent"]))
        self.assertFalse(self.graph.check_artifacts_connection("v1", "v4", mode="all", types=["None"]))

    def test_non_connected(self):
        self.assertTrue(self.graph.request_non_connected_vertices())
        self.assertEqual(self.graph.get_artifacts(), [["v5"]])


if __name__ == '__main__':
    unittest.main()
