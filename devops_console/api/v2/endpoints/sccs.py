from http import HTTPStatus
from urllib.parse import urljoin

from anyio import create_task_group
from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel
from requests import HTTPError

from devops_console import schemas
from devops_console.clients import CoreClient
from devops_console.core import settings

router = APIRouter()

core = CoreClient()
client = core.sccs


@router.get("/")
async def home():
    return {"message": "Hello World"}


# ----------------------------------------------------------------------------------------------------------------------
# Webhooks
# ----------------------------------------------------------------------------------------------------------------------

class RepoList(BaseModel):
    repo_names: list[str] = []


def sanitize_webhook_target_url(url):
    target_url = url if url is not None else urljoin(
        settings.WEBHOOKS_HOST,
        settings.WEBHOOKS_PATH
        )
    if settings.WEBHOOKS_PATH not in target_url:
        target_url = urljoin(target_url, settings.WEBHOOKS_PATH)
    if not target_url.endswith("/"):
        target_url += "/"
    return target_url


async def get_repositories(credentials, plugin_id, repositories):
    result = None
    try:
        if len(repositories) == 0:
            result = await client.get_repositories(plugin_id=plugin_id, credentials=credentials)
        else:
            result = []

            async def append_repo(repo):
                result.append(
                    await client.get_repository(
                        plugin_id=plugin_id,
                        credentials=credentials,
                        repo_name=repo
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
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No repositories found")

    return result


@router.post("/repositories/verify_webhooks", tags=["webhooks"])
async def verify_webhooks(
        plugin_id: str,
        repo_list: RepoList,
        target_url: str | None = None,
        ):
    """Verify if a webhooks subscription exists for the given repositories.
    If no repositories are given, all will be checked.
    Returns a list of repositories that do not have a webhooks subscription."""

    credentials = None

    repositories = repo_list.repo_names

    if len(repositories) == 0:
        repos = await get_repositories(credentials, plugin_id, [])
        repositories = [r.name for r in repos]

    target_url = sanitize_webhook_target_url(target_url)

    result = []

    async def verify(repo_name):
        try:
            repo_subscriptions = await client.get_webhook_subscriptions(
                plugin_id=plugin_id, credentials=credentials, repo_name=repo_name
                )
            if not any(s["url"] == target_url for s in repo_subscriptions["values"]):
                result.append(repo_name)
        except HTTPError as e:
            logger.warning(f"Failed to get list of webhooks for {repo_name}: {e}")
            raise HTTPException(status_code=HTTPStatus.EXPECTATION_FAILED, detail=str(e))

    async with create_task_group() as tg:
        for repo_name in repositories:
            tg.start_soon(verify, repo_name)

    return result


@router.post("/repositories/create_webhooks", tags=["webhooks"])
async def create_webhooks(
        plugin_id: str,
        repo_list: RepoList,
        target_url: str | None = None
        ):
    """Subscribe to webhooks for each repository (must be idempotent)."""
    credentials = None

    repos = await get_repositories(credentials, plugin_id, repo_list.repo_names)

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
                        plugin_id=plugin_id, credentials=credentials, repo_name=repo.name
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
                    logger.warning(f"Webhook subscription already exists for {repo.name}.")
                    return

                # create the webhook
                try:
                    new_subscription = await client.create_webhook_subscription(
                        plugin_id=plugin_id,
                        credentials=credentials,
                        repo_name=repo.name,
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
                    logger.warning(f"Failed to create webhook subscription for {repo.name}.")
                    return

                subscriptions.append(schemas.WebhookSubscription(**new_subscription))

            tg.start_soon(_subscribe_if_not_set, repo)

    return subscriptions


@router.delete("/repositories/remove_webhooks", tags=["webhooks"])
async def remove_webhooks(
        plugin_id: str,
        repo_list: RepoList,
        target_url: str | None = None
        ):
    """Remove the default webhooks from all repositories."""

    credentials = None

    if len(repo_list.repo_names) == 0 and target_url is None:
        raise HTTPException(status_code=400, detail="No repositories or target_url provided.")

    target_url = sanitize_webhook_target_url(target_url)

    repos = await get_repositories(credentials, plugin_id, repo_list.repo_names)

    async with create_task_group() as tg:
        for repo in repos:  # type: ignore
            async def _remove_webhook(repo):
                try:
                    current_subscriptions = await client.get_webhook_subscriptions(
                        plugin_id=plugin_id, credentials=credentials, repo_name=repo.name
                        )
                except HTTPError as e:
                    logger.warning(
                        f"Failed to get webhook subscriptions for {repo.name}: {e.strerror}"
                        )
                    return

                if current_subscriptions is None or len(current_subscriptions["values"]) == 0:
                    logger.info(f"No webhook subscriptions for {repo.name}.")
                    return

                for subscription in current_subscriptions["values"]:
                    if subscription["url"] == target_url:
                        try:
                            await client.delete_webhook_subscription(
                                plugin_id=plugin_id,
                                credentials=credentials,
                                repo_name=repo.name,
                                subscription_id=subscription["uuid"],
                                )
                            logger.info(f"Deleted webhook subscription for {repo.name}.")
                        except HTTPError as e:
                            logger.warning(
                                f"Failed to delete webhook subscription for {repo.name}: {e.strerror}"
                                )
                            continue
                    logger.debug(f"Webhook subscription for {repo.name} not found.")

            tg.start_soon(_remove_webhook, repo)

# @router.get("/repositories")
# async def get_repositories(
#         session: tuple[str, Credentials] = Depends(yield_credentials),
# ):
#     plugin_id, credentials = session
#     try:
#         return await client.get_repositories(plugin_id=plugin_id, credentials=credentials)
#     except ApiError as e:
#         raise HTTPException(status_code=500, detail=e.reason)
#
#
# @router.get("/repositories/{name}")
# async def get_repository_by_name(
#         name: str, session: tuple[str, Credentials] = Depends(yield_credentials)
# ):
#     plugin_id, credentials = session
#     return await client.get_repository(plugin_id=plugin_id, credentials=credentials, repo_name=name)
#
#
# @router.post("/repositories")
# async def create_repository(
#         repo,
#         session: tuple[str, Credentials] = Depends(yield_credentials),
# ):
#     """
#     Create a new repository (if it doesn't exist) and set the webhooks.
#     """
#     plugin_id, credentials = session
#     responserepo = (
#         client.add_repository(
#             plugin_id=plugin_id,
#             credentials=credentials,
#             repository=repo,
#             template="empty-repo-for-applications",
#             template_params={},
#             args=None,
#         ),
#     )
#
#     if not responserepo:
#         raise HTTPException(status_code=400, detail="Failed to create repository")
#
#     # Set the default webhook
#     await client.create_webhook_subscription(
#         plugin_id=plugin_id,
#         credentials=credentials,
#         repo_name=repo.name,
#         url=urljoin(settings.WEBHOOKS_HOST, settings.WEBHOOKS_PATH),
#         active=True,
#         events=settings.WEBHOOKS_DEFAULT_EVENTS,
#         description=settings.WEBHOOKS_DEFAULT_DESCRIPTION,
#         args=None,
#     )
#
#     return responserepo
#
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
# ------------------------------------------------------------------------------
# Projects
# ------------------------------------------------------------------------------


# @router.get("/projects")
# async def get_projects(session: tuple[str, Credentials] = Depends(yield_credentials)):
#     plugin_id, credentials = session
#     try:
#         return await client.get_projects(plugin_id=plugin_id, credentials=credentials)
#     except HTTPError as e:
#         raise HTTPException(status_code=400, detail=e.strerror)
