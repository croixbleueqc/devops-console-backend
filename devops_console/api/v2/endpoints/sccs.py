import asyncio
import logging
from urllib.parse import urljoin

from atlassian.bitbucket import Cloud as BitbucketSession
from atlassian.errors import ApiError
from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from requests import HTTPError

from devops_console import schemas
from devops_console.api.deps import get_current_user
from devops_console.clients import CoreClient
from devops_console.core.config import settings
from devops_sccs.typing.credentials import Credentials

router = APIRouter()

core = CoreClient()
client = core.sccs


def yield_credentials(user: schemas.User = Depends(get_current_user)):
    credz = Credentials(
        user=user.bitbucket_username,
        apikey=user.bitbucket_app_password,
        author=f"{user.full_name} <{user.email}>",
    )

    plugin_id = user.plugin_id

    yield plugin_id, credz


@router.get("/")
async def home():
    return {"message": "Hello World"}


# ----------------------------------------------------------------------------------------------------------------------
# Repositories
# ----------------------------------------------------------------------------------------------------------------------


@router.get("/repositories")
async def get_repositories(
    session: tuple[str, Credentials] = Depends(yield_credentials),
):
    plugin_id, credentials = session
    try:
        return await client.get_repositories(plugin_id=plugin_id, credentials=credentials)
    except ApiError as e:
        raise HTTPException(status_code=500, detail=e.reason)


@router.get("/repositories/{name}", response_model=schemas.Repository)
async def get_repository_by_name(
    name: str, session: tuple[str, BitbucketSession] = Depends(yield_credentials)
):
    plugin_id, credentials = session
    return await client.get_repository(plugin_id=plugin_id, credentials=credentials, repo_name=name)


@router.post("/repositories")
async def create_repository(
    repo: schemas.RepositoryPost,
    session: tuple[str, Credentials] = Depends(yield_credentials),
):
    """
    Create a new repository (if it doesn't exist) and set the webhooks.
    """
    plugin_id, credentials = session
    responserepo = (
        client.add_repository(
            plugin_id=plugin_id,
            credentials=credentials,
            repository=repo.dict(),
            template="empty-repo-for-applications",
            template_params={},
            args=None,
        ),
    )

    if not responserepo:
        raise HTTPException(status_code=400, detail="Failed to create repository")

    # Set the default webhook
    await client.create_webhook_subscription(
        plugin_id=plugin_id,
        credentials=credentials,
        repo_name=repo.name,
        url=urljoin(settings.WEBHOOKS_HOST, settings.WEBHOOKS_PATH),
        active=True,
        events=settings.WEBHOOKS_DEFAULT_EVENTS,
        description=settings.WEBHOOKS_DEFAULT_DESCRIPTION,
        args=None,
    )

    return responserepo


@router.put("/repositories/{uuid}", response_model=schemas.Repository)
async def update_repository(uuid: UUID4):
    raise NotImplementedError


@router.delete("/repositories/{uuid}", status_code=204)
async def delete_repository(uuid: UUID4):
    raise NotImplementedError


@router.get("/repositories/create_default_webhooks")
async def create_default_webhooks(session: tuple[str, Credentials] = Depends(yield_credentials)):
    """Subscribe to webhooks for each repository (must be idempotent)."""

    plugin_id, credentials = session
    # get list of repositories
    repos = None
    try:
        repos = await client.get_repositories(plugin_id=plugin_id, credentials=credentials)
    except HTTPError as e:
        logging.warning(f"Failed to get list of repositories: {e}")
        raise HTTPException(status_code=e.request.status_code, detail=e)
    if repos is None or len(repos) == 0:
        logging.warning("No repositories found.")
        raise HTTPException(status_code=400, detail="No repositories found")

    subscriptions = []

    # we'll batch the requests since there are a lot of them, but note that the
    # rate limit for webhooks is 1000 reqs/hour, so just keep that in mind if
    # testing this out (there are roughly 400 repos at the time of writing)
    coros = []

    for repo in repos:  # type: ignore

        async def _subscribe_if_not_set(repo):
            # get list of webhooks for this repo
            current_subscriptions = None
            try:
                current_subscriptions = await client.get_webhook_subscriptions(
                    plugin_id=plugin_id, credentials=credentials, repo_name=repo.name
                )
            except ApiError as e:
                logging.warning(f"Failed to get webhook subscriptions for {repo.name}: {e.reason}")
                return
            if current_subscriptions is None or len(current_subscriptions) == 0:
                logging.warning(f"No webhook subscriptions found for {repo.name}.")
                return

            # check if the webhook is already set
            if any(
                [
                    subscription["url"] == urljoin(settings.WEBHOOKS_HOST, settings.WEBHOOKS_PATH)
                    and all(
                        [
                            event in subscription["events"]
                            for event in settings.WEBHOOKS_DEFAULT_EVENTS
                        ]
                    )
                    for subscription in current_subscriptions["values"]
                ]
            ):
                logging.warning(f"Webhook subscription already exists for {repo.name}.")
                return

            # create the webhook
            new_subscription = None
            try:
                new_subscription = await client.create_webhook_subscription(
                    plugin_id=plugin_id,
                    credentials=credentials,
                    repo_name=repo.name,
                    url=urljoin(settings.WEBHOOKS_HOST, settings.WEBHOOKS_PATH),
                    active=True,
                    events=settings.WEBHOOKS_DEFAULT_EVENTS,
                    description=settings.WEBHOOKS_DEFAULT_DESCRIPTION,
                )
                logging.warning(f"Subscribed to default webhook for {repo.name}.")
            except ApiError as e:
                logging.warning(
                    f"Failed to create webhook subscription for {repo.name}: {e.reason}"
                )
                return
            if new_subscription is None or len(new_subscription) == 0:
                logging.warning(f"Failed to create webhook subscription for {repo.name}.")
                return

            subscriptions.append(schemas.WebhookSubscription(**new_subscription))

        coros.append(_subscribe_if_not_set(repo))

    await asyncio.gather(*coros)

    return subscriptions


@router.get("/repositories/remove_default_webhooks")
async def remove_default_webhooks(session: tuple[str, Credentials] = Depends(yield_credentials)):
    """Remove the default webhooks from all repositories."""

    plugin_id, credentials = session

    # get list of repositories
    repos = None
    try:
        repos = await client.get_repositories(plugin_id=plugin_id, credentials=credentials)
    except ApiError as e:
        logging.warning(f"Failed to get list of repositories: {e.reason}")
        return
    if repos is None or len(repos) == 0:
        logging.warning("No repositories found.")
        raise HTTPException(status_code=400, detail="No repositories found")

    coros = []

    for repo in repos:  # type: ignore

        async def _remove_default_webhooks(repo):
            current_subscriptions = None
            try:
                current_subscriptions = await client.get_webhook_subscriptions(
                    plugin_id=plugin_id, credentials=credentials, repo_name=repo.name
                )
            except HTTPError as e:
                logging.warning(
                    f"Failed to get webhook subscriptions for {repo.name}: {e.strerror}"
                )
                return

            if current_subscriptions is None or len(current_subscriptions["values"]) == 0:
                logging.warning(f"No webhook subscriptions for {repo.name}.")
                return

            for subscription in current_subscriptions["values"]:
                if subscription["url"] == urljoin(settings.WEBHOOKS_HOST, settings.WEBHOOKS_PATH):
                    try:
                        await client.delete_webhook_subscription(
                            plugin_id=plugin_id,
                            credentials=credentials,
                            repo_name=repo.name,
                            subscription_id=subscription["uuid"],
                        )
                        logging.warning(f"Deleted webhook subscription for {repo.name}.")
                    except HTTPError as e:
                        logging.warning(
                            f"Failed to delete webhook subscription for {repo.name}: {e.strerror}"
                        )
                        continue

            logging.info(f"Removed default webhooks from {repo.name}.")

        coros.append(_remove_default_webhooks(repo))

    await asyncio.gather(*coros)


# ------------------------------------------------------------------------------
# Projects
# ------------------------------------------------------------------------------


@router.get("/projects", response_model=schemas.Paginated[schemas.Project])
async def get_projects(session: tuple[str, Credentials] = Depends(yield_credentials)):
    plugin_id, credentials = session
    try:
        return await client.get_projects(plugin_id=plugin_id, credentials=credentials)
    except HTTPError as e:
        raise HTTPException(status_code=400, detail=e.strerror)
