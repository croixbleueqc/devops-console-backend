from fastapi import Header

from devops_sccs.typing.credentials import Credentials


class CommonHeaders:
    def __init__(
            self,
            plugin_id: str = Header(default='cbq'),
            username: str | None = Header(default=None),
            apikey: str | None = Header(default=None),
            author: str | None = Header(default=None),
            ):
        self.plugin_id = plugin_id
        if username is None or author is None or apikey is None:
            self.credentials = None
        else:
            self.credentials = Credentials(
                user=username,
                apikey=apikey,
                author=author,
                )
