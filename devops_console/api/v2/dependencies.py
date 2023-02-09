from fastapi import Header

from devops_sccs.typing.credentials import Credentials


class CommonHeaders:
    def __init__(
            self,
            x_plugin_id: str = Header(default='cbq'),
            x_username: str | None = Header(default=None),
            x_apikey: str | None = Header(default=None),
            x_author: str | None = Header(default=None),
            ):
        self.plugin_id = x_plugin_id
        if x_username is None or x_author is None or x_apikey is None:
            self.credentials = None
        else:
            self.credentials = Credentials(
                user=x_username,
                apikey=x_apikey,
                author=x_author,
                )
