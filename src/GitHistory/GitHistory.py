import os
import re
from pprint import pprint
from subprocess import run, PIPE
from typing import List, Tuple, Set

DIFF_U0_PATH = os.path.dirname(__file__) + "/scripts/git_dif_uo.sh"
BLAME_PATH = os.path.dirname(__file__) + "/scripts/git_blame.sh"
LOG_PATH = os.path.dirname(__file__) + "/scripts/git_log.sh"


class GitHistory:
    def __init__(self, repo_path: str):
        self.__repo_path = repo_path
        self.__commits: Set[str] = set()
        self.__references: Set[int] = set()
        self.__modifications: List[Tuple[str, str, str, str]] = []

    def __request_commits_from_file(self, file_path_in_repo: str, commit_sha: str, line_index: int,
                                    line_count: int) -> bool:
        """
        Gets commits returned by git blame on the parent of commit_sha in given lines.

        :param str file_path_in_repo: File to run blame on (can be a deleted file if the file existed prior to
                                      commit_sha).
        :param str commit_sha: Commit SHA1 hash (can be shortened if not ambiguous).
        :param int line_index: First line to blame.
        :param int line_count: Number of lines to blame from line_index.
        :return: Whether the command succeeded or not.
        """
        last_modified_line = line_index + line_count - 1
        process = run(["sh", BLAME_PATH, self.__repo_path, file_path_in_repo, commit_sha, str(line_index),
                       str(last_modified_line)],
                      stdout=PIPE)
        if process.returncode != 0:
            return False
        sha1_regex = re.compile(r"([\da-f]{40})?.+")
        for line in (line for line in process.stdout.decode().split("\n") if line):
            sha1 = sha1_regex.match(line)
            if sha1.group(1):
                self.__commits.add(sha1.group(1))
        return True

    def __parse_git_diff_uo(self, commit_sha: str):
        """
        Gets all file modifications brought by the given commit (file paths and line ranges).

        :param str commit_sha: Commit SHA1 hash (can be shortened if not ambiguous).
        :return: Whether the command succeeded or not.
        """
        process = run(["sh", DIFF_U0_PATH, self.__repo_path, commit_sha],
                      stdout=PIPE)
        if process.returncode != 0:
            return False

        new_file_file_name, previous_file_name = "", ""
        line_number_regex = re.compile(
            r"@+ -(\d+)(?:,(\d+))? \+\d+(?:,(\d+))? @+[\w\W]*?")  # catches line ranges in '@@ -24,3 +43,0 @@ blah'
        for line in process.stdout.decode().split("\n"):

            if line.startswith("+++"):
                new_file_file_name = line[6:]
            if line.startswith("---"):
                previous_file_name = line[6:]

            if line.startswith("@"):
                match = line_number_regex.match(line)
                src_line_index, src_line_count, dst_line_count = match.group(1, 2, 3)
                if not src_line_count or src_line_count != "0":  # ie not a created line/file
                    if new_file_file_name == "ev/null":
                        dst_line_count = "-1"  # means file was deleted
                    self.__modifications.append((previous_file_name, src_line_index, src_line_count, dst_line_count))

        return True

    def request_overwritten_commits(self, commit_sha: str) -> bool:
        """
        Gets all commits that have been overwritten by the given commit.

        i.e. If a line has been modified or deleted in the given commit, this method searches for
        the commit in which the line has been last modified or introduced before the modification.
        Results are given by get_commits method.

        :param str  commit_sha: Commit SHA1 hash (can be shortened if not ambiguous).
        :return: whether the method succeeded or not.
        """
        if not self.__parse_git_diff_uo(commit_sha):
            return False

        for file, src_line_index, src_line_count, dest_line_count in self.__modifications:
            if not src_line_count:
                src_line_count = "1"
            if not self.__request_commits_from_file(file, commit_sha, int(src_line_index), int(src_line_count)):
                return False
        return True

    def __request_references_from_commit_text(self, text):
        reference_regex = re.compile(
            r"(?P<key>\w+)\s\#(?P<project_name>[\w\-]+:)?(?P<value>(?:(?:(\w|&amp;|&|-|_|\.)+\/)*)?(\w|&amp;|&)+?)("
            r"?P<after_reference>&(?:\#(?:\d+|[xX][[:xdigit:]]+)|quot);|(?=[^\w&\/])|$)")

        findall = reference_regex.findall(text)
        self.__references |= set((result[0] + " #" + result[2] for result in findall))

    def request_linked_artifacts(self):
        for commit in self.__commits:
            process = run(["sh", LOG_PATH, self.__repo_path, commit],
                          stdout=PIPE)
            if process.returncode != 0:
                return False
            self.__request_references_from_commit_text(process.stdout.decode())
        return True

    def get_references(self):
        return self.__references

    def get_commits(self):
        return self.__commits
