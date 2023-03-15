import re
import uuid
from pathlib import Path

import pygit2
from atlassian.bitbucket.cloud.workspaces import Workspace
from loguru import logger
from requests.models import HTTPError

from devops_console.models.config.provision import (
    ConfigurationField,
    ConfigurationValue,
    NewRepositoryDefinition,
    ProvisionConfig,
    RepositoryTemplate,
    TemplateArgumentField,
    TemplateFieldType,
    TemplateFieldValue,
)
from devops_console.models.config.sccs_config import SccsPluginConfig
from devops_console.sccs.errors import SccsException
from devops_console.sccs.plugins.models.bitbucket import BranchMatchKind
from devops_console.sccs.typing.credentials import Credentials

from .git_credentials import GitCredentials
from .management_storage import ManagementStorage
from .storage_models import (
    RepositoryConfiguration,
    TemplateParams,
)


class ProvisionV2:
    def __init__(self, config: ProvisionConfig, plugin_config: SccsPluginConfig):
        self._config = config
        self._validator = Validator(self.config)
        self.checkout_base_path = Path(self._config.checkout_base_path)
        self.main_contract = self.config.main_contract
        self.repository_contract = self.config.repository_contract
        self.templates = self.config.repository_templates
        self.storage_access = ManagementStorage(plugin_config)

    @property
    def config(self):
        return self._config

    def new_repository(
        self,
        credentials: Credentials,
        workspace: Workspace,
        repository_definition: NewRepositoryDefinition,
        template_name: str,
        template_params: TemplateParams,
    ):
        self.validate_new_repository_data(
            repository_definition, template_name, template_params
        )

        # TODO Use admin account ?

        # TODO Update storage definitions/templates/configs ?

        repository_configuration = self.get_stored_repository_configuration(
            repository_definition.configuration.key
        )

        # Create repository
        try:
            new_repository = workspace.repositories.create(
                repo_slug=repository_definition.slug,
                project_key=repository_definition.project.key,
                is_private=repository_configuration.is_private,
                fork_policy=repository_configuration.forkPolicy,
            )
        except HTTPError as e:
            logger.warning(e)
            raise

        if new_repository is None:
            raise SccsException("failed to create repository")

        # https://developer.atlassian.com/cloud/bitbucket/rest/intro#resource-links
        ssh_url = self._get_ssh_url(new_repository)

        # clone newly created repo locally and apply the selected template
        logger.info(f"Provisioning repository {repository_definition.slug} ...")
        self.provision_new_repository(
            credentials, ssh_url, repository_definition, template_name, template_params
        )

        # Enforce security (permissions, branches strategy...)
        logger.info(
            f"Enforcing security for repository {repository_definition.slug} ..."
        )

        # - ssh keys
        for sshkey in self.storage_access.get_ssh_keys(repository_configuration):
            new_repository.post(
                path=f"{new_repository.url}/deploy-keys",
                json=sshkey,
            )

        # - Branches restrictions / strategy
        for branch_restriction in repository_configuration.branchRestrictions:
            for kind, value in self.storage_access.get_branch_restrictions.items():
                new_repository.branch_restrictions.create(
                    kind=kind,
                    value=value,
                    branch_pattern=branch_restriction.branch_pattern,
                    branch_match_kind=BranchMatchKind.GLOB,
                )

        # - Privileges
        for group, access in self.storage_access.get_repository_privileges(
            repository_definition.privileges.key
        ):
            group_slug = group.replace(" ", "-").lower()
            new_repository.put(
                path=f"{new_repository.url}/permissions-config/groups/{group_slug}",
                data={"permission": access},
                absolute=True,
            )

        # Pipeline
        if repository_configuration.pipelines.enabled:
            logger.debug(f"{repository_definition.slug}: enabling pipeline")
            new_repository.put(
                path=f"{new_repository.url}/pipelines_config",
                data={
                    "enabled": True,
                    "repository": {"type": new_repository.get_data("type")},
                },
                absolute=True,
            )

    def _get_ssh_url(self, created):
        links = created.get_data("links")
        if links is None or "clone" not in links:
            raise SccsException("failed to get clone links")
        clone_links = links["clone"]
        ssh_url = [link["href"] for link in clone_links if link["name"] == "ssh"][0]
        return ssh_url

    def validate_new_repository_data(
        self,
        repository_definition: NewRepositoryDefinition,
        template_name: str,
        template_params: TemplateParams,
    ):
        """Will raise a ValueError if the data does not comform to the configurations"""
        self._validator.validate_repository_definition(repository_definition)
        self._validator.validate_template(template_name, template_params)

    def get_stored_repository_configuration(self, key: str):
        return self.storage_access.get_repository_configuration(key)

    def provision_new_repository(
        self,
        credentials: Credentials,
        ssh_url: str,
        repository_definition: NewRepositoryDefinition,
        template_name: str,
        template_params: TemplateParams,
    ):
        if not template_name:
            logger.debug("No template specified, skipping provisioning")
            return

        repository_configuration = self.get_stored_repository_configuration(
            repository_definition.configuration.key
        )
        # make local clone that we'll modify according to the passed arguments
        git_credentials = self.storage_access.git_credentials.for_pygit2()
        callbacks = pygit2.RemoteCallbacks(credentials=git_credentials)
        clone, local_clone_path = self._clone_new_repository_locally(callbacks, ssh_url)

        if not template_name:
            return

        # pull in template
        template = self.templates[template_name]

        self._apply_remote_template_commit_to_main_branch(
            callbacks,
            clone,
            repository_configuration,
            template,
            template_name,
        )

        # run initialization command in a subprocess
        template_init_cmd = self._make_init_cmd(
            repository_definition, template_name, template_params
        )
        if template_init_cmd is not None:
            self._run_init_cmd(clone, credentials, local_clone_path, template_init_cmd)

        # additional branches
        self._create_additional_branches(clone, template)

        # push to remote
        self._push_changes(callbacks, clone, ssh_url, template)

    def _clone_new_repository_locally(self, callbacks, ssh_url: str):
        local_clone_path = str(self.checkout_base_path / str(uuid.uuid4()))
        clone = pygit2.clone_repository(ssh_url, local_clone_path, callbacks=callbacks)
        return clone, local_clone_path

    def _apply_remote_template_commit_to_main_branch(
        self,
        callbacks: pygit2.RemoteCallbacks,
        clone: pygit2.Repository,
        repository_configuration: RepositoryConfiguration,
        template: RepositoryTemplate,
        template_name: str,
    ):
        template_url = template.configuration.git_url
        template_main_branch = template.configuration.main_branch_name
        remote_template = clone.remotes.create("template", template_url)
        remote_template.fetch(callbacks=callbacks)

        # get the OID to the template's main branch
        template_main_oid = clone.lookup_reference(
            f"refs/remotes/template/{template_main_branch}"
        ).target

        # get the commit associated with the OID and apply it to the main branch
        template_commit = clone.get(template_main_oid)
        if template_commit is None:
            raise SccsException(
                f"Could not find commit for template: {template_name} OID: {template_main_oid}"
            )
        clone.create_branch(repository_configuration.mainBranch, template_commit)  # type: ignore
        clone.checkout(f"refs/heads/{repository_configuration.mainBranch}")

    def _run_init_cmd(
        self,
        clone,
        credentials: Credentials,
        local_clone_path,
        template_init_cmd,
    ):
        import subprocess

        process = subprocess.run(template_init_cmd, cwd=local_clone_path)
        process.check_returncode()

        # commit the changes
        committer_signature = GitCredentials.create_pygit2_signature(
            self.storage_access.git_credentials.author
        )
        if credentials.author is None:
            author_signature = committer_signature
        else:
            author_signature = GitCredentials.create_pygit2_signature(
                credentials.author
            )

        clone.index.add_all()
        clone.index.write()
        tree = clone.index.write_tree()
        clone.create_commit(
            "HEAD",
            author_signature,
            committer_signature,
            "initialized scaffold template",
            tree,
            [clone.head.target],
        )

    def _make_init_cmd(
        self,
        repository_definition: NewRepositoryDefinition,
        template_name: str,
        template_params: TemplateParams,
    ):
        """Create a command based on answers

        Args example:

        setup = {
            "cmd": [
                "python",
                "setup.py",
                "init"
            ],
            "args": {
                "name": {
                    "type": "string",
                    "description": "Project Name",
                    "required": true,
                    "default": null,
                    "validator": "^[a-z][a-z,-]*[a-z]$",
                    "arg": "--name={}"
                },
                "desc": {
                    "type": "string",
                    "description": "Description",
                    "required": true,
                    "default": null,
                    "validator": ".+",
                    "arg": "--desc='{}'"
                },
                "helloworld": {
                    "type": "bool",
                    "description": "Remove helloworld",
                    "default": true,
                    "arg": {
                        "true": "-c",
                        "false": null
                    }
                }
            }
        }

        answers = {
            "name": "test",
            "helloworld": True,
            "desc": "This is a test !"
        }
        """
        # Create the main command part.
        # We are trying to substitute repository_name that is the only variable supported for now
        template = self.templates.get(template_name)
        if template is None:
            raise ValueError(f"Invalid template: {template_name}")

        init_command = template.init_cmd
        cmd = []

        for name in init_command.cmd:
            cmd.append(name.format(repository_name=repository_definition.slug))

        if len(cmd) == 0:
            return None

        # Validate and append the additianal command arguments
        for name, field in init_command.args.items():
            value = template_params.get(name)

            if value is None:
                if field.default is not None:
                    value = field.default
                else:
                    continue

            match field.type:
                # nb assumes that we've validated the values beforehand
                case TemplateFieldType.string:
                    cmd.append(field.arg.format(value))  # type: ignore
                case TemplateFieldType.boolean:
                    if isinstance(value, bool):
                        new_value = "true" if value else "false"
                    elif isinstance(value, str):
                        new_value = value.lower()
                    else:
                        raise ValueError(f"Invalid value for boolean field: {value}")

                    if field.arg.get(new_value) is not None:  # type: ignore
                        cmd.append(field.arg.get(new_value))  # type: ignore

                case TemplateFieldType.integer:
                    cmd.append(value)
                case _:
                    raise NotImplementedError(f"Unknown field type: {field.type}")

        return cmd

    def _create_additional_branches(self, clone, template):
        def create_branch(branch_name: str):
            branch_oid = clone.lookup_reference(
                f"refs/remotes/template/{branch_name}"
            ).target
            commit = clone.get(branch_oid)
            if not commit:
                logger.warning(f"Could not find commit for branch: {branch_name}")
                return
            clone.create_branch(branch_name, commit)  # type: ignore

        for branch_name in template.configuration.other_branch_names:
            if branch_name == template.configuration.main_branch_name:
                continue
            create_branch(branch_name)
            # if a "deploy" branch, create an associated code branch
            if branch_name.startswith("deploy/"):
                create_branch(branch_name[len("deploy/") :])

    def _push_changes(self, callbacks, clone, ssh_url: str, template):
        remote_origin = None
        for repo in clone.remotes:
            if repo.name == "origin":
                remote_origin = repo
                break

        if remote_origin is None:
            raise SccsException(f"{ssh_url}: origin not found")

        remote_origin.push(
            [f"refs/heads/{template.configuration.main_branch_name}"], callbacks
        )
        for branch_name in template.configuration.other_branch_names:
            remote_origin.push([f"refs/heads/{branch_name}"], callbacks)


class Validator:
    def __init__(self, config: ProvisionConfig) -> None:
        self._config = config
        self.main_contract = config.main_contract
        self.repository_contract = config.repository_contract
        self.templates = config.repository_templates

    def validate_repository_definition(
        self,
        repository_definition: NewRepositoryDefinition,
    ):
        """Checks that the repository definition is valid.
        Raises a ValueError if the definition does not respect the constraints
        described in the configuration files.
        """
        self._validate_repository_slug(repository_definition.slug)
        self._validate_repository_configuration(repository_definition.configuration)
        self._validate_repository_privileges(repository_definition.privileges)
        self._validate_repository_project(repository_definition.project)

    def validate_template(self, template_name: str, template_params: TemplateParams):
        if not template_name and self.main_contract.template_required:
            raise ValueError("Template is required")

        template = self.templates[template_name]
        if template is None:
            raise ValueError(f"Invalid template: {template_name}")

        self._validate_template(template, template_params)

    def _validate_repository_slug(self, slug: str):
        try:
            self.validate_with_regex_validator(self.main_contract.slug_regex, slug)
        except ValueError:
            raise ValueError(f"Invalid repository slug: {slug}")

    def _validate_repository_configuration(self, configuration: ConfigurationValue):
        self.validate_configuration_field(
            self.repository_contract.configuration, configuration
        )

    def _validate_repository_privileges(self, privileges: ConfigurationValue):
        self.validate_configuration_field(
            self.repository_contract.privileges, privileges
        )

    def _validate_repository_project(self, project: ConfigurationValue):
        self.validate_configuration_field(self.repository_contract.project, project)

    @staticmethod
    def validate_configuration_field(
        field: ConfigurationField, value: ConfigurationValue
    ):
        if field.required and value is None:
            raise ValueError(f"Missing required field: {field.description}")

        if field.type == "suggestion":
            # check that the configuration exists in the list of suggested values
            if value.key not in [v.key for v in field.values]:
                raise ValueError(f"Invalid repository configuration: {value.key}")

    @staticmethod
    def _validate_template(
        template: RepositoryTemplate, template_params: TemplateParams
    ):
        args = template.init_cmd.args

        if args is None or template_params is None:
            return

        for arg_name, template_field in args.items():
            value = template_params.get(arg_name)
            Validator.validate_template_field(arg_name, template_field, value)

    @staticmethod
    def validate_template_field(
        arg_name: str, field: TemplateArgumentField, value: TemplateFieldValue | None
    ):
        if value is None:
            if field.required:
                raise ValueError(
                    f"Missing required template parameter: {field.description}"
                )
            else:
                return

        def raise_argument_typeerror(arg_name, expected, actual):
            raise TypeError(
                f"Invalid type for command argument: {arg_name} (expected {expected}, got {actual})"
            )

        match field.type:
            case TemplateFieldType.boolean:
                if not isinstance(value, bool):
                    raise_argument_typeerror(arg_name, "bool", type(value))
            case TemplateFieldType.string:
                if not isinstance(value, str):
                    raise_argument_typeerror(arg_name, "str", type(value))
                # validate syntax if a validator exists for this field
                if field.validator is not None and isinstance(value, str):
                    Validator.validate_with_regex_validator(field.validator, value)
            case TemplateFieldType.integer:
                if not isinstance(value, int):
                    raise_argument_typeerror(arg_name, "int", type(value))

    @staticmethod
    def validate_with_regex_validator(validator: str, value: str):
        if not re.match(validator, value):
            raise ValueError(f"Invalid value: {value}")
