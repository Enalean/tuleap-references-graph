import unittest
from unittest.mock import Mock

from Tuleap.RestClient.Artifacts import Artifacts
from Tuleap.RestClient.Connection import Connection

from src.ApiClientAddon import APIConstants
from src.Graph.ArtifactsWalker import ArtifactsWalker
from src.ApiClientAddon.CommitAddon import Commits


class TestArtifactWalkerBaseCases(unittest.TestCase):
    def setUp(self) -> None:
        Connection.is_logged_in = Mock(return_value=False)
        self.mock_connection = Connection()

        mock_commit_getter = Commits(self.mock_connection)
        mock_artifact_getter = Artifacts(self.mock_connection)

        self.walker = ArtifactsWalker(mock_commit_getter, mock_artifact_getter)

    def test_walker_incorrect_id(self):
        self.assertEqual(self.walker.walk("0"), False)
        self.assertEqual(self.walker.get_vertices(), [])
        self.assertEqual(self.walker.get_edges(), [])

    def test_one_artifact(self):
        def mock_request_artifact(self_, art_id):
            if art_id == "1":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #1",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": []
                })
                return True
            return False

        Artifacts.request_artifact = mock_request_artifact

        self.assertEqual(self.walker.walk("1"), True)
        self.assertEqual(self.walker.get_vertices(), ["1"])
        self.assertEqual(self.walker.get_vertices_names(), ["art #1"])
        self.assertEqual(self.walker.get_edges(), [])

    def test_one_commit(self):
        def mock_request_commit(self_, art_id, repo_id):
            if art_id == "6e32c0528dc493edec278f43f2c1d7bf05985fcd":
                Commits.get_data = Mock(return_value={
                    APIConstants.CROSS_REFERENCE_GIT_NAME: []
                })
                return True
            else:
                return False

        Commits.get_path = Mock(return_value="repo/")
        Commits.is_repo_valid = Mock(return_value=True)
        Commits.request_commit = mock_request_commit

        self.assertEqual(self.walker.walk("6e32c0528dc493edec278f43f2c1d7bf05985fcd"), True)
        self.assertEqual(self.walker.get_vertices(), ["6e32c0528dc493edec278f43f2c1d7bf05985fcd"])
        self.assertEqual(self.walker.get_vertices_names(), ["git #repo/6e32c0528dc493edec278f43f2c1d7bf05985fcd"])


class TestArtifactWalker(unittest.TestCase):
    def setUp(self) -> None:
        Connection.is_logged_in = Mock(return_value=False)
        self.mock_connection = Connection()

        mock_commit_getter = Commits(self.mock_connection)
        mock_artifact_getter = Artifacts(self.mock_connection)

        self.walker = ArtifactsWalker(mock_commit_getter, mock_artifact_getter)

        def mock_request_commit(self_, art_id, repo_id):
            if art_id == "36d3e5dfab31ef2a6537c17fa73157fab2ab0fe3":
                Commits.get_data = Mock(return_value={
                    APIConstants.CROSS_REFERENCE_GIT_NAME:
                        [
                            {
                                "direction": "in",
                                "ref": "art #2"
                            }
                        ]
                })
                return True
            elif art_id == "1b47ce3eee6246b0dd759cdb4d9d6323a1c61a98":
                Commits.get_data = Mock(return_value={
                    APIConstants.CROSS_REFERENCE_GIT_NAME:
                        [
                            {
                                "direction": "in",
                                "ref": "art #2"
                            }
                        ]
                })
                return True
            elif art_id == "6add64b5d54ee893b3d0d252c061d64c78634239":
                Commits.get_data = Mock(return_value={
                    APIConstants.CROSS_REFERENCE_GIT_NAME:
                        [
                            {
                                "direction": "in",
                                "ref": "art #3"
                            }
                        ]
                })
                return True
            else:
                return False

        def mock_request_artifact(self_, art_id):
            if art_id == "1":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #1",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "links": [
                                {
                                    "type": None,
                                    "id": 2,
                                },
                                {
                                    "type": None,
                                    "id": 7,
                                },
                            ]
                        },
                        {
                            "type": "art_link",
                            "reverse_links": [
                                {
                                    "type": None,
                                    "id": 8,
                                },
                                {
                                    "type": None,
                                    "id": 4,
                                },
                                {
                                    "type": None,
                                    "id": 10,
                                },
                            ]
                        },
                    ]
                })
                return True
            elif art_id == "2":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #2",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "links": [
                                {
                                    "type": None,
                                    "id": 3,
                                },
                            ]
                        },
                        {
                            "type": "art_link",
                            "reverse_links": [
                                {
                                    "type": None,
                                    "id": 1,
                                },
                            ]
                        },
                        {
                            "type": "cross",
                            "value": [
                                {
                                    "ref": "git #repo/36d3e5dfab31ef2a6537c17fa73157fab2ab0fe3",
                                    "url": "https://tuleap-web.tuleap-aio-dev.docker/goto?key=git&val=compilateur%2F36d3e5dfab31ef2a6537c17fa73157fab2ab0fe3&group_id=101",
                                    "direction": "out"
                                },
                                {
                                    "ref": "git #repo/1b47ce3eee6246b0dd759cdb4d9d6323a1c61a98",
                                    "url": "https://tuleap-web.tuleap-aio-dev.docker/goto?key=git&val=compilateur%2F1b47ce3eee6246b0dd759cdb4d9d6323a1c61a98&group_id=101",
                                    "direction": "out"
                                },
                            ]
                        }

                    ]
                })
                return True

            elif art_id == "3":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #3",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "links": [
                                {
                                    "type": None,
                                    "id": 5,
                                },
                            ]
                        },
                        {
                            "type": "art_link",
                            "reverse_links": [
                                {
                                    "type": None,
                                    "id": 2,
                                },
                            ]
                        },
                        {
                            "type": "cross",
                            "value": [
                                {
                                    "ref": "git #repo/6add64b5d54ee893b3d0d252c061d64c78634239",
                                    "url": "https://tuleap-web.tuleap-aio-dev.docker/goto?key=git&val=compilateur%2F6add64b5d54ee893b3d0d252c061d64c78634239&group_id=101",
                                    "direction": "in"
                                },
                            ]
                        }
                    ]
                })
                return True
            elif art_id == "4":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #4",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "links": [
                                {
                                    "type": None,
                                    "id": 1,
                                },
                            ]
                        },
                        {
                            "type": "art_link",
                            "reverse_links": [
                                {
                                    "type": None,
                                    "id": 5,
                                },
                            ]
                        },
                    ]
                })
                return True
            elif art_id == "5":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #5",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "links": [
                                {
                                    "type": None,
                                    "id": 4,
                                },
                            ]
                        },
                        {
                            "type": "art_link",
                            "reverse_links": [
                                {
                                    "type": None,
                                    "id": 3,
                                },
                            ]
                        },
                    ]
                })
                return True
            elif art_id == "6":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #6",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": []
                })
                return True
            elif art_id == "7":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #7",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "links": [
                                {
                                    "type": None,
                                    "id": 8,
                                },
                            ]
                        },
                        {
                            "type": "art_link",
                            "reverse_links": [
                                {
                                    "type": None,
                                    "id": 1,
                                },
                            ]
                        },
                    ]
                })
                return True
            elif art_id == "8":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #8",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "links": [
                                {
                                    "type": None,
                                    "id": 1,
                                },
                                {
                                    "type": None,
                                    "id": 9,
                                },
                            ]
                        },
                        {
                            "type": "art_link",
                            "reverse_links": [
                                {
                                    "type": None,
                                    "id": 7,
                                },
                            ]
                        },
                    ]
                })
                return True
            elif art_id == "9":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #9",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "reverse_links": [
                                {
                                    "type": None,
                                    "id": 1,
                                },
                            ]
                        },
                    ]
                })
                return True
            elif art_id == "10":
                Artifacts.get_data = Mock(return_value={
                    "xref": "art #10",
                    "project": {
                        "id": 101,
                    },
                    "tracker": {
                        "id": 1,
                    },
                    "values": [
                        {
                            "type": "art_link",
                            "links": [
                                {
                                    "type": None,
                                    "id": 1,
                                },
                            ]
                        },
                    ]
                })
                return True
            return False

        Artifacts.request_artifact = mock_request_artifact

        Commits.get_path = Mock(return_value="repo/")
        Commits.is_repo_valid = Mock(return_value=True)
        Commits.request_commit = mock_request_commit

    def test_depth_1_forwards(self):
        self.assertEqual(self.walker.walk("1", depth_limit=1, through_reverse_links=False), True)
        self.assertCountEqual(self.walker.get_vertices(), ["1", "2", "7"])
        self.assertEqual(self.walker.get_vertices(), ["1", "2", "7"])
        self.assertEqual(self.walker.get_vertices_names(), ["art #1", "art #2", "art #7"])
        self.assertEqual(self.walker.get_edges(), [["1", "2", None], ["1", "7", None]])

    def test_depth_1_backward(self):
        self.assertEqual(self.walker.walk("1", depth_limit=1), True)
        self.assertListEqual(self.walker.get_vertices(), ["1", "2", "7", "8", "4", "10"])
        self.assertEqual(self.walker.get_vertices_names(), ["art #1", "art #2", "art #7", "art #8",
                                                            "art #4", "art #10"])
        self.assertEqual(self.walker.get_edges(), [["1", "2", None], ["1", "7", None], ["8", "1", None],
                                                   ["4", "1", None], ["10", "1", None]])

    def test_depth_2(self):
        self.assertEqual(self.walker.walk("5", depth_limit=2), True)

        self.assertListEqual(sorted(self.walker.get_vertices()),
                             sorted(["1", "2", "3", "4", "5", "6add64b5d54ee893b3d0d252c061d64c78634239"]))

        self.assertListEqual(sorted(self.walker.get_edges()),
                             sorted([["3", "5", None], ["6add64b5d54ee893b3d0d252c061d64c78634239", "3", "git"],
                                     ["2", "3", None], ["5", "4", None], ["4", "1", None]])
                             )

    def test_forward(self):
        self.assertEqual(self.walker.walk("1", through_reverse_links=False), True)

        self.assertListEqual(sorted(self.walker.get_vertices()),
                             sorted(["1", "2", "3", "4", "5", "7", "8", "9",
                                     "1b47ce3eee6246b0dd759cdb4d9d6323a1c61a98",
                                     "36d3e5dfab31ef2a6537c17fa73157fab2ab0fe3"]))

        self.assertListEqual(
            sorted(self.walker.get_edges()),
            sorted([["1", "2", None], ["2", "3", None], ["3", "5", None],
                    ["5", "4", None], ["4", "1", None], ["1", "7", None],
                    ["7", "8", None], ["8", "1", None], ["8", "9", None],
                    ["2", "1b47ce3eee6246b0dd759cdb4d9d6323a1c61a98", "git"],
                    ["2", "36d3e5dfab31ef2a6537c17fa73157fab2ab0fe3", "git"]])
        )


if __name__ == '__main__':
    unittest.main()
