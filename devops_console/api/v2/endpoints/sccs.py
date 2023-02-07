from http import HTTPStatus
from urllib.parse import urljoin

from anyio import create_task_group
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from pydantic import BaseModel
from requests import HTTPError

from devops_console import schemas
from devops_console.api.v2.dependencies import CommonHeaders
from devops_console.clients import CoreClient
from devops_console.core import settings
from devops_sccs.errors import SccsException
from devops_sccs.plugins.cache_keys import cache_key_fns
from devops_sccs.redis import RedisCache
from devops_sccs.schemas.config import RepoContractConfigValue, RepoContractProjectValue

cache = RedisCache()

router = APIRouter()

core = CoreClient()
client = core.sccs


@router.get("/")
async def home():
    return {"message": "Hello World"}


# ----------------------------------------------------------------------------------------------------------------------
# Collections
# ----------------------------------------------------------------------------------------------------------------------


@router.get("/repository-collections")
async def get_repository_collections():
    global repository_collections
    return repository_collections


# ----------------------------------------------------------------------------------------------------------------------
# Projects
# ----------------------------------------------------------------------------------------------------------------------


@router.get("/projects")
async def get_projects(common_headers: CommonHeaders = Depends()):
    credentials = common_headers.credentials
    plugin_id = common_headers.plugin_id

    try:
        return await client.get_projects(plugin_id=plugin_id, credentials=credentials)
    except HTTPError as e:
        raise HTTPException(status_code=400, detail=e.strerror)


# ----------------------------------------------------------------------------------------------------------------------
# Repositories
# ----------------------------------------------------------------------------------------------------------------------


class RepoList(BaseModel):
    repo_slugs: list[str] = []


@router.get("/repositories")
async def get_repositories(
        common_headers: CommonHeaders = Depends(),
        ):
    credentials = common_headers.credentials
    plugin_id = common_headers.plugin_id
    try:
        return await client.get_repositories(
            plugin_id=plugin_id, credentials=credentials
            )
    except HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories/{slug}")
async def get_repository(
        slug: str,
        common_headers: CommonHeaders = Depends(),
        ):
    credentials = None  # alias for admin
    plugin_id = common_headers.plugin_id
    return await client.get_repository(
        plugin_id=plugin_id,
        credentials=credentials,
        repo_slug=slug,
        )


@router.get("/repositories/{repo_slug}/cd")
async def get_cd_config(
        repo_slug: str,
        common_headers: CommonHeaders = Depends(),
        ):
    credentials = None  # alias for admin
    plugin_id = common_headers.plugin_id
    try:
        return await client.get_continuous_deployment_config(
            plugin_id=plugin_id, credentials=credentials, repo_slug=repo_slug
            )
    except HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories/{slug}/cd/versions")
async def get_cd_versions(
        slug: str,
        common_headers: CommonHeaders = Depends(),
        ):
    try:
        return await client.get_continuous_deployment_versions_available(
            plugin_id=common_headers.plugin_id,
            credentials=common_headers.credentials,
            repo_slug=slug,
            )
    except HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repositories/{repo_slug}/cd/{environment}/{version}")
async def trigger_cd(
        repo_slug: str,
        environment: str,
        version: str,
        common_headers: CommonHeaders = Depends(),
        ):
    credentials = common_headers.credentials
    plugin_id = common_headers.plugin_id

    try:
        res = await client.trigger_continuous_deployment(
            plugin_id=plugin_id,
            credentials=credentials,
            repo_slug=repo_slug,
            environment=environment,
            version=version,
            )

        # clear associated cache
        cache.delete(cache_key_fns["get_continuous_deployment_config"](repo_slug, []))

        return res
    except HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/add-repository-contract")
async def get_add_repository_contract(common_headers: CommonHeaders = Depends()):
    credentials = common_headers.credentials
    plugin_id = common_headers.plugin_id

    try:
        return await client.get_add_repository_contract(
            plugin_id=plugin_id, credentials=credentials
            )
    except HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))


class AddRepositoryDefinition(BaseModel):
    name: str
    configuration: RepoContractConfigValue
    privileges: RepoContractConfigValue
    project: RepoContractProjectValue


class AddRepositoryRequestBody(BaseModel):
    repository: AddRepositoryDefinition
    template: str
    template_params: dict[str, bool | str]


@router.post("/repositories")
async def add_repository(
        # TODO type arguments
        body: AddRepositoryRequestBody,
        common_headers: CommonHeaders = Depends(),
        ):
    """
    Create a new repository (if it doesn't exist) and set the webhooks.
    """
    credentials = common_headers.credentials
    plugin_id = common_headers.plugin_id

    try:
        responserepo = (
            await client.add_repository(
                plugin_id=plugin_id,
                credentials=credentials,
                repository=body.repository.dict(),
                template=body.template,
                template_params=body.template_params,
                ),
            )

        if not responserepo:
            raise HTTPException(status_code=400, detail="Failed to create repository")

        # clear the repositories cache
        cache.delete_namespace("repositories")
    except (HTTPError, SccsException) as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Set the default webhook
    # await client.create_webhook_subscription(
    #     plugin_id=plugin_id,
    #     credentials=credentials,
    #     repo_name=repo.name,
    #     url=urljoin(settings.WEBHOOKS_HOST, settings.WEBHOOKS_PATH),
    #     active=True,
    #     events=settings.WEBHOOKS_DEFAULT_EVENTS,
    #     description=settings.WEBHOOKS_DEFAULT_DESCRIPTION,
    #     args=None,
    # )
    #
    return responserepo


#
# @router.put("/repositories/{uuid}")
# async def update_repository(uuid: UUID4):
#     raise NotImplementedError
#
#
# @router.delete("/repositories/{uuid}", status_code=204)
# async def delete_repository(uuid: UUID4):
#     raise NotImplementedError
#


# ----------------------------------------------------------------------------------------------------------------------
# Repository Webhooks
# ----------------------------------------------------------------------------------------------------------------------


@router.post("/repositories/verify_webhooks", tags=["webhooks"])
async def verify_webhooks(
        repo_list: RepoList,
        target_url: str | None = None,
        plugin_id: str = "cbq",
        ):
    """Verify if a webhooks subscription exists for the given repositories.
    If no repositories are given, all will be checked.
    Returns a list of repositories that do not have a webhooks subscription."""

    credentials = None

    repositories = repo_list.repo_slugs

    if len(repositories) == 0:
        repos = await _get_repositories(credentials, plugin_id, [])
        repositories = [r.name for r in repos]

    target_url = sanitize_webhook_target_url(target_url)

    result = []

    async def verify(repo_slug):
        try:
            repo_subscriptions = await client.get_webhook_subscriptions(
                plugin_id=plugin_id, credentials=credentials, repo_slug=repo_slug
                )
            if not any(s["url"] == target_url for s in repo_subscriptions["values"]):
                result.append(repo_slug)
        except HTTPError as e:
            logger.warning(f"Failed to get list of webhooks for {repo_slug}: {e}")
            raise HTTPException(
                status_code=HTTPStatus.EXPECTATION_FAILED, detail=str(e)
                )

    async with create_task_group() as tg:
        for repo_slug in repositories:
            tg.start_soon(verify, repo_slug)

    return result


@router.post("/repositories/create_webhooks", tags=["webhooks"])
async def create_webhooks(
        repo_list: RepoList,
        target_url: str | None = None,
        plugin_id: str = "cbq",
        ):
    """Subscribe to webhooks for each repository (must be idempotent)."""
    credentials = None  # alias for admin

    repos = await _get_repositories(credentials, plugin_id, repo_list.repo_slugs)

    target_url = sanitize_webhook_target_url(target_url)

    subscriptions = []

    # we'll batch the requests since there are a lot of them, but note that the
    # rate limit for webhooks is 1000 reqs/hour, so just keep that in mind if
    # testing this out (there are roughly 400 repos at the time of writing)
    coros = []

    async with create_task_group() as tg:
        for repo in repos:  # type: ignore

            async def _subscribe_if_not_set(repo):
                # get list of webhooks for this repo
                try:
                    current_subscriptions = await client.get_webhook_subscriptions(
                        plugin_id=plugin_id,
                        credentials=credentials,
                        repo_slug=repo.slug,
                        )
                except HTTPError as e:
                    logger.warning(
                        f"Failed to get webhook subscriptions for {repo.name}: {str(e)}"
                        )
                    return
                if current_subscriptions is None:
                    current_subscriptions = []

                # check if the webhook is already set
                if any(
                        [
                            subscription["url"] == target_url
                            and all(
                                [
                                    event in subscription["events"]
                                    for event in settings.WEBHOOKS_DEFAULT_EVENTS
                                    ]
                                )
                            for subscription in current_subscriptions["values"]
                            ]
                        ):
                    logger.warning(
                        f"Webhook subscription already exists for {repo.name}."
                        )
                    return

                # create the webhook
                try:
                    new_subscription = await client.create_webhook_subscription(
                        plugin_id=plugin_id,
                        credentials=credentials,
                        repo_slug=repo.slug,
                        url=target_url,
                        active=True,
                        events=settings.WEBHOOKS_DEFAULT_EVENTS,
                        description=settings.WEBHOOKS_DEFAULT_DESCRIPTION,
                        )
                    logger.info(f"Subscribed to default webhook for {repo.name}.")
                except HTTPError as e:
                    logger.warning(
                        f"Failed to create webhook subscription for {repo.name}: {str(e)}"
                        )
                    return
                if new_subscription is None or len(new_subscription) == 0:
                    logger.warning(
                        f"Failed to create webhook subscription for {repo.name}."
                        )
                    return

                subscriptions.append(schemas.WebhookSubscription(**new_subscription))

            tg.start_soon(_subscribe_if_not_set, repo)

    return subscriptions


@router.delete("/repositories/remove_webhooks", tags=["webhooks"])
async def remove_webhooks(
        repo_list: RepoList,
        target_url: str | None = None,
        plugin_id: str = "cbq",
        ):
    """Remove the default webhooks from all repositories."""

    credentials = None  # alias for admin

    if len(repo_list.repo_slugs) == 0 and target_url is None:
        raise HTTPException(
            status_code=400, detail="No repositories or target_url provided."
            )

    target_url = sanitize_webhook_target_url(target_url)

    repos = await _get_repositories(credentials, plugin_id, repo_list.repo_slugs)

    async with create_task_group() as tg:
        for repo in repos:  # type: ignore

            async def _remove_webhook(repo):
                try:
                    current_subscriptions = await client.get_webhook_subscriptions(
                        plugin_id=plugin_id,
                        credentials=credentials,
                        repo_slug=repo.slug,
                        )
                except HTTPError as e:
                    logger.warning(
                        f"Failed to get webhook subscriptions for {repo.name}: {e.strerror}"
                        )
                    return

                if (
                        current_subscriptions is None
                        or len(current_subscriptions["values"]) == 0
                ):
                    logger.info(f"No webhook subscriptions for {repo.name}.")
                    return

                for subscription in current_subscriptions["values"]:
                    if subscription["url"] == target_url:
                        try:
                            await client.delete_webhook_subscription(
                                plugin_id=plugin_id,
                                credentials=credentials,
                                repo_slug=repo.slug,
                                subscription_id=subscription["uuid"],
                                )
                            logger.info(
                                f"Deleted webhook subscription for {repo.name}."
                                )
                        except HTTPError as e:
                            logger.warning(
                                f"Failed to delete webhook subscription for {repo.name}: {e.strerror}"
                                )
                            continue
                    logger.debug(f"Webhook subscription for {repo.name} not found.")

            tg.start_soon(_remove_webhook, repo)


def sanitize_webhook_target_url(url):
    target_url = (
        url
        if url is not None
        else urljoin(settings.WEBHOOKS_HOST, settings.WEBHOOKS_PATH)
    )
    if settings.WEBHOOKS_PATH not in target_url:
        target_url = urljoin(target_url, settings.WEBHOOKS_PATH)
    if not target_url.endswith("/"):
        target_url += "/"
    return target_url


async def _get_repositories(credentials, plugin_id, repositories):
    result = None
    try:
        if len(repositories) == 0:
            result = await client.get_repositories(
                plugin_id=plugin_id, credentials=credentials
                )
        else:
            result = []

            async def append_repo(repo):
                result.append(
                    await client.get_repository(
                        plugin_id=plugin_id, credentials=credentials, repo_slug=repo
                        )
                    )

            async with create_task_group() as tg:
                for repo in repositories:
                    tg.start_soon(append_repo, repo)
    except HTTPError as e:
        logger.warning(f"Failed to get list of repositories: {e}")
        raise HTTPException(status_code=HTTPStatus.EXPECTATION_FAILED, detail=e)
    if result is None or len(result) == 0:
        logger.warning("No repositories found.")
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="No repositories found"
            )

    return result


repository_collections = {
    "assistance": {
        "name": "Assistance",
        "repositories": [
            "assistance-integration-test",
            "assistance-salesforce-edge-api",
            "assistance-salesforce-event-listener",
            "assistance-salesforce-system-api",
            "fax-system-api",
            "insured-eligibility-service",
            "product-benefit-service",
            "acocan-system-api",
            "payment-service",
            "holidays-service",
            ],
        "environments": [
            {"enabled": False, "name": "master"},
            {"enabled": True, "name": "development"},
            {"enabled": True, "name": "qa"},
            {"enabled": True, "name": "acceptation"},
            {"enabled": True, "name": "production"},
            ],
        },
    "healthcare": {
        "name": "Healthcare Claims",
        "repositories": [
            "healthcare-claims-edi-service",
            "healthcare-claims-invoice-service",
            "healthcare-claims-salesforce-event-listener",
            "healthcare-claims-salesforce-system-api",
            "healthcare-claims-service",
            "document-fusion-service",
            "transfert-service",
            "sharepoint-system-api",
            "healthcare-claims-integration-test",
            "healthcare-claims-match-service",
            "star-system-api",
            "factcan-system-api",
            "exchange-rate-service",
            "healthcare-claims-report-service",
            ],
        "environments": [
            {"enabled": False, "name": "master"},
            {"enabled": True, "name": "development"},
            {"enabled": True, "name": "qa"},
            {"enabled": True, "name": "acceptation"},
            {"enabled": True, "name": "production"},
            ],
        },
    "reclamation": {
        "name": "Réclamation Digitale",
        "repositories": [
            "claims-travel-frontend-web",
            "claims-travel-edge-api",
            "claims-travel-orchestrator-system-api",
            "salesforce-system-api",
            "salesforce-edge-api",
            "salesforce-event-listener",
            "sharepoint-system-api",
            "usermanager-system-api",
            "star-edge-api",
            "email-system-api",
            "document-viewer",
            "document-viewer-edge-api",
            "salesforce-core",
            "financial-institution-service",
            "document-fusion-service",
            "univers-system-api",
            "sharepoint-edge-api",
            ],
        "environments": [
            {"enabled": True, "name": "master"},
            {"enabled": False, "name": "development"},
            {"enabled": True, "name": "qa"},
            {"enabled": False, "name": "training"},
            {"enabled": True, "name": "acceptation"},
            {"enabled": True, "name": "production"},
            ],
        },
    "amf": {
        "name": "Document Manage - AMF",
        "repositories": ["document-manager-frontend-web", "document-manager-edge-api"],
        "environments": [
            {"name": "master", "enabled": False},
            {"name": "development", "enabled": True},
            {"name": "qa", "enabled": True},
            {"name": "acceptation", "enabled": True},
            {"name": "production", "enabled": True},
            ],
        },
    }
