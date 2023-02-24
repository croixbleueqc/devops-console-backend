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
        if not x_username or not x_author or not x_apikey:
            self.credentials = None
        else:
            self.credentials = Credentials(
                user=x_username,
                apikey=x_apikey,
                author=x_author,
                )
