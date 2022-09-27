import json
import logging
from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError
from requests import JSONDecodeError

from devops_console.clients.client import CoreClient
from devops_console.clients.wscom import manager as ws_manager
from devops_console.schemas.legacy.ws import WsResponse
from devops_sccs.typing.cd import EnvironmentConfig

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
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Error parsing JSON.")

    if type(body) is not dict:
        logging.warning(f"Invalid JSON: {body}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid JSON")

    logging.debug(f"\nWebhook body:\n\n{json.dumps(body, indent=2)}\n\n")

    match event_key:
        case WebhookEventKey.repo_push:
            return await handle_repo_push(event=body)
        case WebhookEventKey.repo_build_created:
            return handle_repo_build_created(event=body)
        case WebhookEventKey.repo_build_updated:
            return handle_repo_build_updated(event=body)
        case WebhookEventKey.pr_created:
            return handle_pr_created(event=body)
        case WebhookEventKey.pr_updated:
            return handle_pr_updated(event=body)
        case WebhookEventKey.pr_approved:
            return handle_pr_approved(event=body)
        case WebhookEventKey.pr_declined:
            return handle_pr_declined(event=body)
        case WebhookEventKey.pr_merged:
            return handle_pr_merged(event=body)
        case _:
            msg = (f"Unsupported event key: {event_key}",)
            logging.warning(msg)
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=msg,
            )


def validation_exception_handler(e: ValidationError):
    logging.warning(f"Error validating webhook event: {e}")
    raise HTTPException(
        status_code=HTTPStatus.BAD_REQUEST, detail="Error validating webhook event."
    )


# TODO invalidate appropriate caches on in these handlers


async def handle_repo_push(event: dict):
    """Compare hook data to cached values and update cache accordingly."""

    logging.info('Handling "repo:push" webhook event')

    repopushevent: RepoPushEvent
    try:
        repopushevent = RepoPushEvent(**event)
    except ValidationError as e:
        validation_exception_handler(e)

    # determine if the push event touches any of the cached values
    changes_matter = False
    for push_change in repopushevent.push["changes"]:
        if push_change.new.type == "branch" and push_change.new.name in client.cd_branches_accepted:
            changes_matter = True
            break

    # if the push event doesn't touch any of the cached values, we can skip it
    if not changes_matter:
        return

    await ws_manager.broadcast(f"repo:push:{repopushevent.repository.name}")


async def handle_repo_build_created(event: dict):
    logging.info('Handling "repo:build_created" webhook event')

    repobuildstatuscreated: RepoBuildStatusCreated
    try:
        repobuildstatuscreated = RepoBuildStatusCreated(**event)
    except ValidationError as e:
        validation_exception_handler(e)

    await ws_manager.broadcast(f"repo:build_created:{repobuildstatuscreated.repository.name}")


async def handle_repo_build_updated(event: dict):
    logging.info('Handling "repo:build_updated" webhook event')

    repobuildstatusupdated: RepoBuildStatusUpdated
    try:
        repobuildstatusupdated = RepoBuildStatusUpdated(**event)
    except ValidationError as e:
        validation_exception_handler(e)

    # TODO: establish protocol for sending build status updates to clients
    await ws_manager.broadcast(f"repo:build_updated:{repobuildstatusupdated.repository.name}")
    # legacy
    await ws_manager.broadcast(
        WsResponse(
            "whitecard",
            {
                "pullrequest": repobuildstatusupdated.commit_status.links["html"]["href"],
            },
        ).json()
    )


async def handle_pr_created(event: dict):
    logging.info('Handling "pr:created" webhook event')

    prcreated: PRCreatedEvent
    try:
        prcreated = PRCreatedEvent(**event)
    except ValidationError as e:
        validation_exception_handler(e)

    await ws_manager.broadcast(f"pr:created:{prcreated.repository.name}")


async def handle_pr_updated(event: dict):
    logging.info('Handling "pr:updated" webhook event')

    prupdated: PRUpdatedEvent
    try:
        prupdated = PRUpdatedEvent(**event)
    except ValidationError as e:
        validation_exception_handler(e)

    await ws_manager.broadcast(f"pr:updated:{prupdated.repository.name}")


async def handle_pr_merged(event: dict):
    logging.info('Handling "pr:merged" webhook event')

    prmerged: PRMergedEvent
    try:
        prmerged = PRMergedEvent(**event)
    except ValidationError as e:
        validation_exception_handler(e)

    await ws_manager.broadcast(f"pr:merged:{prmerged.repository.name}")


async def handle_pr_approved(event: dict):
    logging.info('Handling "pr:approved" webhook event')

    prapproved: PRApprovedEvent
    try:
        prapproved = PRApprovedEvent(**event)
    except ValidationError as e:
        validation_exception_handler(e)

    await ws_manager.broadcast(f"pr:approved:{prapproved.repository.name}")


async def handle_pr_declined(event: dict):
    logging.info('Handling "pr:declined" webhook event')

    prdeclined: PRDeclinedEvent
    try:
        prdeclined = PRDeclinedEvent(**event)
    except ValidationError as e:
        validation_exception_handler(e)

    await ws_manager.broadcast(f"pr:declined:{prdeclined.repository.name}")
