from typing import List

from src.ApiClientAddon.APIConstants import CROSS_REFERENCE_GIT_NAME, REFERENCE_DIRECTION_IN, REFERENCE_DIRECTION_OUT


class CommitParser(object):
    """
    Parses the artifact and extract the relevant data

    Fields type information:
    :type __commit: dict
    :type __links: list[int]
    :type __valid: bool
    """

    def __init__(self, item: dict):
        """
        :param item: the commit item to be parsed
        :type item: dict

        """
        self.__commit = item
        self.__links: List[str] = []
        self.__reverse_links: List[str] = []

        self.__valid = self.__extract_links()

    def get_links(self) -> List[str]:
        """
        Get the list of all references made in the commit.

        :return: list of direct artifact links
        :rtype: list[str]
        """
        return self.__links

    def get_reverse_links(self) -> List[str]:
        """
        Get the list of all references that points to the commit.

        :return: list of direct artifact links
        :rtype: list[str]
        """
        return self.__reverse_links

    def is_valid(self):
        """
        Returns whether the commit is valid or not.
        :return:
        """
        return self.__valid

    # Private-------------------------------------------------------------------------------------------

    def __extract_links(self) -> bool:
        """
        Search for and extract the commit links. These can be either forward or reverse links.
        """
        if self.__commit and CROSS_REFERENCE_GIT_NAME in self.__commit:
            self.__parse_cross_references()
            return True
        return False

    def __parse_cross_references(self) -> None:
        for reference in self.__commit[CROSS_REFERENCE_GIT_NAME]:
            if reference["direction"] == REFERENCE_DIRECTION_IN:
                self.__reverse_links.append(reference["ref"])
            elif reference["direction"] == REFERENCE_DIRECTION_OUT:
                self.__links.append(reference["ref"])
