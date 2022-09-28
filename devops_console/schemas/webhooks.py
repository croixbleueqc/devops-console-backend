from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, TypedDict
from pydantic import UUID4, AnyHttpUrl, BaseModel, Extra, Field, HttpUrl

from .bitbucket import (
    Account,
    BaseCommit,
    BitbucketResource,
    Commit,
)

Links = dict[str, dict[str, str]]


class WebhookEventKey(str, Enum):
    issue_comment_created = "issue:comment_created"
    issue_comment_updated = "issue:comment_updated"
    issue_created = "issue:created"
    issue_updated = "issue:updated"
    pr_approved = "pullrequest:approved"
    pr_change_request_removed = "pullrequest:changes_request_removed"
    pr_changes_requested = "pullrequest:changes_request_created"
    pr_comment_created = "pullrequest:comment_created"
    pr_comment_deleted = "pullrequest:comment_deleted"
    pr_comment_updated = "pullrequest:comment_updated"
    pr_created = "pullrequest:created"
    pr_declined = "pullrequest:rejected"
    pr_merged = "pullrequest:fulfilled"
    pr_unapproved = "pullrequest:unapproved"
    pr_updated = "pullrequest:updated"
    project_updated = "project:updated"
    repo_build_created = "repo:commit_status_created"
    repo_build_updated = "repo:commit_status_updated"
    repo_commit_comment_created = "repo:commit_comment_created"
    repo_created = "repo:created"
    repo_deleted = "repo:deleted"
    repo_forked = "repo:fork"
    repo_imported = "repo:imported"
    repo_push = "repo:push"
    repo_transfer = "repo:transfer"
    repo_updated = "repo:updated"
    user_account_prop_changed = "user:account_property_changed"


class PayloadWorkspace(BaseModel):
    """The Workspace in event payloads"""

    type = "workspace"
    slug: str
    name: str
    uuid: UUID4
    links: Links = {}


class PayloadProject(BaseModel):
    """The Project in event payloads"""

    type = "project"
    name: str
    uuid: UUID4
    links: Links = {}
    key: str


class PayloadRepository(BaseModel):
    """Repository that received commits"""

    type = "repository"
    name: str
    full_name: str
    workspace: PayloadWorkspace
    uuid: UUID4
    links: Links = {}
    project: PayloadProject
    website: HttpUrl | None
    scm: Literal["git", "hg"]
    is_private: bool


class PullRequestState(str, Enum):
    open = "OPEN"
    merged = "MERGED"
    declined = "DECLINED"


class PayloadPullRequest(BaseModel):
    """The Pull Request in event payloads. In addition to the following fields, the pull request entity may include other fields as well."""

    id: int
    title: str
    description: str
    state: PullRequestState


class ReferenceState(BaseModel):
    """An object containing information about the state of the reference after the push."""

    type: Literal["branch", "tag"]
    name: str
    target: BaseCommit | Commit
    links: Links = {}


class CommitShort(TypedDict):
    type: Literal["commit"]
    hash: str
    message: str
    author: Account
    links: Links


class PushChange(BaseModel):
    """References that the push updated"""

    new: ReferenceState
    old: ReferenceState
    links: Links = {}
    created: bool
    forced: bool
    closed: bool
    commits: List[CommitShort] = Field(max_items=5)
    truncated: bool


class CommitState(str, Enum):
    in_progress = "INPROGRESS"
    successful = "SUCCESSFUL"
    failed = "FAILED"


class CommitStatus(BaseModel):
    """The details of the commit status"""

    name: str
    description: str
    state: CommitState
    key: str | None = None
    url: AnyHttpUrl
    type = "build"  # Currently, Bitbucket can only associate commit statuses with a build, so the only supported type is build
    created_on: datetime
    updated_on: datetime
    links: Links = {}


class WebhookEvent(BaseModel, extra=Extra.allow):
    """Base class for webhook events"""

    actor: Account | None
    repository: PayloadRepository


class RepositoryEvent(WebhookEvent):
    """Base class for events that occur in a repository"""


class RepoPushEvent(RepositoryEvent):
    """A user pushes 1 or more commits to a repository. This payload, has an event key of repo:push"""

    push: Dict[Literal["changes"], List[PushChange]]


class RepoBuildStatusCreated(RepositoryEvent):
    """A build system, CI tool, or another vendor recognizes that a user recently pushed a commit and updates the commit with its status. This payload has an event key of repo:commit_status_created"""

    commit_status: CommitStatus


class RepoBuildStatusUpdated(RepositoryEvent):
    """A build system, CI tool, or another vendor recognizes that a commit has a new status and updates the commit with its status. This payload has an event key of repo:commit_status_updated"""

    commit_status: CommitStatus


class PullRequestEvent(WebhookEvent):
    """Base class for events that occur on a pull request"""


class PRCreatedEvent(PullRequestEvent):
    """A user creates a pull request for a repository. This payload has an event key of pullrequest:created"""

    pullrequest: PayloadPullRequest


class PRUpdatedEvent(PullRequestEvent):
    """A user updates a pull request for a repository. This payload has an event key of pullrequest:updated"""

    pullrequest: PayloadPullRequest


class PRMergedEvent(PullRequestEvent):
    """A user merges a pull request for a repository. This payload has an event key of pullrequest:fulfilled"""

    pullrequest: PayloadPullRequest


class PRApprovedEvent(PullRequestEvent):
    """A user approves a pull request for a repository. This payload has an event key of pullrequest:approved"""

    pullrequest: PayloadPullRequest


class PRDeclinedEvent(PullRequestEvent):
    """A user declines a pull request for a repository. This payload has an event key of pullrequest:rejected"""

    pullrequest: PayloadPullRequest


class WebhookSubscription(BaseModel, extra=Extra.allow):
    """A webhook subscription"""

    uuid: UUID4
    url: AnyHttpUrl
    description: str = ""
    subject_type: Literal["repository", "workspace", "user", "team"] | None = None
    subject: BitbucketResource
    active: bool
    created_at: datetime
    events: List[WebhookEventKey] = Field(min_items=1, unique_items=True)
