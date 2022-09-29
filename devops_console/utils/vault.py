"""
Vault Helper

env:
- VAULT_ADDR: Vault address
- VAULT_TOKEN: Token for the account
- VAULT_ROLE: Role used to login
"""

import os

from loguru import logger
from hvac import Client
from hvac.adapters import Request
from hvac.adapters import JSONAdapter
from devops_console.schemas.vault import VaultBitbucket, VaultConfig


class IstioRequest(JSONAdapter, Request):
    """workaround for an HTTP/2 issue with LIST/istio/vault on k8s"""

    def request(self, method, url, headers=None, raise_exception=True, **kwargs):
        """override request function to change the LIST method to a GET one"""

        if method == "list":
            method = "get"
            url = url + "?list=true"

        return super().request(
            method, url, headers=headers, raise_exception=raise_exception, **kwargs
        )


class Vault:
    """Vault helper

    Purpose is to find the proper context to connect to the vault and to provide read functions.
    """

    DEFAULT_K8S_AUTH_NONPROD = "kubernetes-nonprod"
    DEFAULT_K8S_AUTH_PROD = "kubernetes"
    token: str
    client: Client

    def __init__(self):
        self.k8s = False
        self.k8s_auth = self.DEFAULT_K8S_AUTH_NONPROD

        self.addr = os.environ.get("VAULT_ADDR", "http://localhost:8200")
        logger.info(f"VAULT_ADDR: {self.addr}")

        self.role = os.environ.get("VAULT_ROLE", "default")
        logger.info(f"VAULT_ROLE: {self.role}")

        self.mount = os.environ.get("VAULT_MOUNT")
        if self.mount is None:
            raise Exception("Please set VAULT_MOUNT!")
        logger.info(f"VAULT_MOUNT: {self.mount}")

        try:
            self.token = self.get_sa_token_from_pod()
            self.k8s = True
            if self.role.endswith("-prod"):
                self.k8s_auth = self.DEFAULT_K8S_AUTH_PROD
            logger.info(f"Token set from kubernetes [auth: {self.k8s_auth}].")
            return
        except Exception:
            pass

        try:
            self.token = self.get_token_from_env()
            logger.info("Token set from env.")
            return
        except Exception:
            pass

    def connect(self):
        """Connect to the Vault"""
        if isinstance(self.client, Client):
            return

        client = Client(url=self.addr, adapter=IstioRequest)

        if self.k8s:
            client.auth_kubernetes(self.role, self.token, mount_point=self.k8s_auth)
        elif self.token is not None:
            client.token = self.token

        if not client.is_authenticated:
            raise Exception("Auth failure")

        self.client = client
        logger.info("Vault auth succeeded!")

    @staticmethod
    def get_sa_token_from_pod():
        """Get the SA token from a Pod"""

        with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
            jwt = f.read()
        return jwt

    @staticmethod
    def get_token_from_env():
        """Get a token set in environment variables"""

        return os.environ["VAULT_TOKEN"]

    def assert_valid_client(self):
        if not self.client:
            raise Exception("Please connect() before.")
        self.client: Client

    def list_secrets(self, path):
        """List secrets in the specified path"""

        self.assert_valid_client()

        list_response = self.client.secrets.kv.v2.list_secrets(path, mount_point=self.mount)
        return list_response["data"]["keys"]

    def list_secrets_recursive(self, path):
        """List secrets recursively from the specified path"""

        self.assert_valid_client()

        secrets = {}

        keys = self.list_secrets(path)
        for key in keys:
            if key.endswith("/"):
                # this is a path
                secrets[key[:-1]] = self.list_secrets_recursive(path + key)
            else:
                # this is a kv secret
                secrets[key] = None

        return secrets

    def read_secret(self, path):
        """Read a secret"""

        self.assert_valid_client()

        response = self.client.secrets.kv.v2.read_secret_version(path, mount_point=self.mount)
        return response["data"]["data"]


def get_environment_kubeconfigs(config: dict, environment: str) -> dict:
    """Get secrets to use Croix Bleue Kubernetes infrastructure
    Returns a dict in the form:
        {
            "nonprod": {
                ...kubeconfig...
            },
            ...
        }
    """

    vault = Vault()
    vault.connect()

    configs = {}

    logger.info(f"Getting kubeconfigs for environment: {environment}")

    for secret in vault.list_secrets(f"infra/k8s/devops-console-backend/{environment}"):
        configs[secret] = vault.read_secret(
            f"infra/k8s/devops-console-backend/{environment}/{secret}"
        )["kubeconfig"]

    logger.info(f"Got kubeconfigs: {[*configs.keys()]}")
    return configs


def get_bb_su_creds(config: VaultConfig) -> VaultBitbucket:
    if config.skip_vault:
        return VaultBitbucket(**config.dict())

    vault = Vault()
    vault.connect()

    return VaultBitbucket(**vault.read_secret(config.vault_secret))


def write_keys(path: str, private_key: str, public_key: str):
    os.makedirs(path, exist_ok=True)

    pri_path = os.path.join(path, "bitbucket")
    pub_path = os.path.join(path, "bitbucket.pub")

    try:
        with open(pri_path, "w") as f:
            f.write(private_key)
        with open(pub_path, "w") as f:
            f.write(public_key)
    except Exception as e:
        logger.error(f"Couldn't write files: {e}")
