import json


class Commits(object):
    """
    Add-on to Git class of the API client.
    """

    def __init__(self, connection, repository_id: int = None):
        """
        Constructor
        :param connection: connection object (must already be logged in)
        :type connection: Tuleap.RestClient.Connection.Connection
        """
        self._connection = connection
        self.__repository_id: int = repository_id
        self.__path: str = ""
        self._data = None
        self.__valid = self.__request_path()

    def is_repo_valid(self):
        return self.__valid

    def get_data(self):
        """
        Get data received in the last response message.

        :return: Response data
        :rtype: dict | list[dict]
        :note: One of the request method should be successfully executed before this method is
               called!
        """
        return self._data

    def get_path(self):
        return self.__path

    def request_commit(self, commit_reference: str, repository_id: int = None):
        """
        Requests a commit from a repository.

        :param repository_id: Git Repository ID
        :param commit_reference: commit SHA1
        :return: success: Success or failure
        :rtype: bool
        """
        # Check if we are logged in
        if not self._connection.is_logged_in():
            return False

        repository_id = repository_id or self.__repository_id
        # Get repository
        relative_url = "/git/{repo}/commits/{ref}".format(repo=repository_id, ref=commit_reference)
        success = self._connection.call_get_method(relative_url)

        # Parse response
        if success:
            self._data = json.loads(self._connection.get_last_response_message().text)

        return success

    def __request_path(self):
        if not self._connection.is_logged_in():
            return False

        relative_url = "/git/{repo}".format(repo=self.__repository_id)
        success = self._connection.call_get_method(relative_url)

        if success:
            data = json.loads(self._connection.get_last_response_message().text)
            self.__path = data["name"] + "/"

        return success
