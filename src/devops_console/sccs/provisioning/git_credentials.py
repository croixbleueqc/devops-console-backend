import pygit2

from devops_console.sccs.errors import AuthorSyntax


class GitCredentials(object):
    """Credential for git

    Only support SSH key for now

    Args:
        user (str): Sccs username
        pub (str): Absolute path to the ssh public key
        key (str): Absolute path to the ssh private key
        author (str): Git author like "User <user@domain.tld>"
    """

    def __init__(self, user, pub, key, author):
        self.user = user
        self.pub = pub
        self.key = key
        self.author = author

    @classmethod
    def create_pygit2_signature(cls, author):
        """Create a signature based on git author syntax "User <user@domain.tld>"""

        # TODO: improve with a regex
        user_email = author.split("<")

        if len(user_email) != 2:
            raise AuthorSyntax(author)

        user = user_email[0].strip()
        email = user_email[1].replace(">", "").strip()
        return pygit2.Signature(user, email, 0, 0, "utf-8")

    def for_pygit2(self):
        """Use SSH key to connect with git"""
        return pygit2.Keypair(self.user, self.pub, self.key, "")
