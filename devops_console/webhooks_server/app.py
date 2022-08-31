import logging
from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from requests import JSONDecodeError

from devops_console.clients.client import CoreClient

from ..schemas.webhooks import (
    PRApprovedEvent,
    PRCreatedEvent,
    PRDeclinedEvent,
    PRMergedEvent,
    PRUpdatedEvent,
    RepoBuildStatusCreated,
    RepoBuildStatusUpdated,
    RepoPushEvent,
    WebhookEventKey,
)

app = FastAPI()

core = CoreClient()
client = core.sccs


@app.post("/", tags=["bitbucket_webhooks"])
async def handle_webhook_event(request: Request):
    """Receive and respond to a Bitbucket webhook event.

    This endpoint (ie: "/bitbucketcloud/hooks/repo") is the entry point for the
    default devops webhook subscriptions.
    """

    event_key = request.headers["X-Event-Key"]
    logging.info(f'Received webhook with event key "{event_key}"')

    try:
        body = await request.json()
    except JSONDecodeError as e:
        logging.warning(f"Error parsing JSON: {e}")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Error parsing JSON."
        )

    if type(body) is not dict:
        logging.warning(f"Invalid JSON: {body}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid JSON")

    match event_key:
        case WebhookEventKey.repo_push:
            return await handle_repo_push(event=RepoPushEvent(**body))
        case WebhookEventKey.repo_build_created:
            return handle_commit_status_created(event=RepoBuildStatusCreated(**body))
        case WebhookEventKey.repo_build_updated:
            return handle_build_status_updated(event=RepoBuildStatusUpdated(**body))
        case WebhookEventKey.pr_created:
            return handle_pr_created(event=PRCreatedEvent(**body))
        case WebhookEventKey.pr_updated:
            return handle_pr_updated(event=PRUpdatedEvent(**body))
        case WebhookEventKey.pr_approved:
            return handle_pr_approved(event=PRApprovedEvent(**body))
        case WebhookEventKey.pr_declined:
            return handle_pr_declined(event=PRDeclinedEvent(**body))
        case WebhookEventKey.pr_merged:
            return handle_pr_merged(event=PRMergedEvent(**body))
        case _:
            msg = (f"Unsupported event key: {event_key}",)
            logging.warning(msg)
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=msg,
            )


async def handle_repo_push(event: RepoPushEvent):
    """Compare hook data to cached values and update cache accordingly."""

    logging.info('Handling "repo:push" webhook event')

    # determine if the push event touches any of the cached values
    changes_matter = False
    for push_change in event.push["changes"]:
        if (
            push_change.new.type == "branch"
            and push_change.new.name in client.cd_branches_accepted
        ):
            changes_matter = True
            break

    # if the push event doesn't touch any of the cached values, we can skip it
    if not changes_matter:
        logging.info("Push event doesn't touch any of the cached values")
        return "OK"

    # if it does, we need to update the cache
    logging.info("Push event touches cached values, updating cache")

    client.get_repository.cache_clear()
    # TODO: determine which other cached functions to clear

    # TODO: react to the push event appropriately


def handle_commit_status_created(event: RepoBuildStatusCreated):
    logging.info('Handling "repo:build_created" webhook event')
    pass


def handle_build_status_updated(event: RepoBuildStatusUpdated):
    logging.info('Handling "repo:build_updated" webhook event')
    pass


def handle_pr_created(event: PRCreatedEvent):
    logging.info('Handling "pr:created" webhook event')
    pass


def handle_pr_updated(event: PRUpdatedEvent):
    logging.info('Handling "pr:updated" webhook event')
    pass


def handle_pr_merged(event: PRMergedEvent):
    logging.info('Handling "pr:merged" webhook event')
    pass


def handle_pr_approved(event: PRApprovedEvent):
    logging.info('Handling "pr:approved" webhook event')
    pass


def handle_pr_declined(event: PRDeclinedEvent):
    logging.info('Handling "pr:declined" webhook event')
    pass
