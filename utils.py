import subprocess
import re
import argparse
import os

from typing import List, Dict
from enum import Enum


class CommitTypes(Enum):
    ADDED = "added"
    CHANGED = "changed"
    REMOVED = "removed"
    FIXED = "fixed"
    NOTES = "notes"
    MERGES = "merges"


# SCRIPT utils
def get_app_root_folder() -> str:
    file_path = __file__.split('/')
    app_root_path = '/'.join(file_path[:-1])

    return app_root_path


def setup_cli_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Set up the command line interface arguments for the given parser.

    Args:
        parser (argparse.ArgumentParser): The ArgumentParser object to set up.

    Returns:
        None
    """
    default_output_file = os.path.join(get_app_root_folder(), "CHANGELOG.md")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=default_output_file,
        help="The output file path. Defaults to pap-ex-px4/CHANGELOG.md")
    parser.add_argument("-f",
                        "--force",
                        action="store_true",
                        help="Overwrite the output file if it already exists.")


# CHANGELOG utils
def get_valid_tags() -> List[str]:
    """
    Get a list of valid tags from the git repository.

    Returns:
        List[str]: A list of valid tags, sorted in descending order.

    Raises:
        RuntimeError: If there is an error retrieving the git tags.
    """
    try:
        git_tags_output = subprocess.check_output(["git",
                                                   "tag"]).decode("utf-8")
        all_tags = git_tags_output.split("\n")

        tag_pattern = re.compile(r"^\d+\.\d+\.\d+(\-((alpha)|(beta)|(rc)))?")
        valid_tags = [tag for tag in all_tags if tag_pattern.match(tag)]

        valid_tags.sort(reverse=True)
        return valid_tags
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "Error: Could not get git tags from git tag command") from e


def get_git_logs_list(tag: str, divisor: str = "###") -> List[str]:
    """
    Generate a list of git logs based on a given tag.

    Args:
        tag (str): The tag to filter the git logs.

    Returns:
        List[str]: A list of git logs.
    """
    command = f"git log {tag} --pretty='format:%D{divisor}%s{divisor}%as' -n 200"
    logs_output = subprocess.check_output(command, shell=True).decode("utf-8")
    logs_list = logs_output.split("\n")
    return logs_list


def get_changelog_md_header(file_path: str, force: bool = False) -> str:
    if os.path.exists(file_path) and not force:
        with open(file_path, "r") as f:
            read_data = f.read()
            if len(read_data) > 0:
                return ""

    return """
# Changelog

This changelog format is based on [Keep a Changelog](https://keepachangelog.com/).

The versioning pattern is defined by MAJOR.MINOR.PATCH-[alpha,beta,rc]

- example: 0.1.1-beta

Meaning of:

- alpha -> tag for branch test releases
- beta -> tag for field test releases
- rc -> tag for release candidate releases

You can read more about version pattern on [this page](https://jassyapollo.atlassian.net/wiki/spaces/PA/pages/595886975/Nomenclatura+de+vers+es+de+Software+Firmware).

"""


def clear_commit_type_dict() -> Dict[CommitTypes, List[str]]:
    """
    Clears the commit type dictionary.

    Returns:
        A dictionary with empty lists for each commit type.
    """
    return {
        CommitTypes.ADDED: [],
        CommitTypes.CHANGED: [],
        CommitTypes.REMOVED: [],
        CommitTypes.FIXED: [],
        CommitTypes.NOTES: [],
        CommitTypes.MERGES: []
    }


def get_commit_type(commit_message: str) -> CommitTypes:
    """
    Determines the type of commit based on the commit message.

    Args:
        commit_message (str): The commit message to analyze.

    Returns:
        CommitTypes: The type of commit, which can be one of the following:
            - CommitTypes.MERGES: If the commit message contains common merge words.
            - CommitTypes.ADDED: If the commit message contains common words indicating an addition.
            - CommitTypes.REMOVED: If the commit message contains common words indicating a removal.
            - CommitTypes.FIXED: If the commit message contains common words indicating a fix.
            - CommitTypes.CHANGED: If none of the above conditions are met.
    """
    commit_message_lower = commit_message.lower()

    notes_common_words = ["merge"]
    for word in notes_common_words:
        if word in commit_message_lower:
            return CommitTypes.MERGES

    added_common_words = [
        "add", "added", "new", "create", "adicionado", "novo", "criado"
    ]
    for word in added_common_words:
        if word in commit_message_lower:
            return CommitTypes.ADDED

    removed_common_words = [
        "remove", "removed", "delete", "deletar", "remover", "deletado",
        "removido"
    ]
    for word in removed_common_words:
        if word in commit_message_lower:
            return CommitTypes.REMOVED

    fixed_common_words = [
        "hotfix", "bugfix", "corrected", "fix", "fixed", "fixes", "bug",
        "problem", "problema", "error", "errors", "erro", "erros"
        "arrumado", "corrigido", "corrigir", "arrumar", "consertar",
        "consertado"
    ]
    for word in fixed_common_words:
        if word in commit_message_lower:
            return CommitTypes.FIXED

    return CommitTypes.CHANGED


def get_changelog_tag_body(output_str: str, commit_type_dict: dict) -> str:
    """
    Generate the changelog tag body based on the commit type dictionary.

    Args:
        output_str (str): The initial string to append the changelog to.
        commit_type_dict (dict): A dictionary containing the commit types and their corresponding commits.

    Returns:
        str: The final string with the changelog tag body.
    """
    if commit_type_dict[CommitTypes.NOTES]:
        output_str += "### Notes\n\n"
        for commit in commit_type_dict[CommitTypes.NOTES]:
            output_str += f"* {commit}\n\n"

    if commit_type_dict[CommitTypes.ADDED]:
        output_str += "### Added\n\n"
        for commit in commit_type_dict[CommitTypes.ADDED]:
            output_str += f"* {commit}\n\n"

    if commit_type_dict[CommitTypes.CHANGED]:
        output_str += "### Changed\n\n"
        for commit in commit_type_dict[CommitTypes.CHANGED]:
            output_str += f"* {commit}\n\n"

    if commit_type_dict[CommitTypes.FIXED]:
        output_str += "### Fixed\n\n"
        for commit in commit_type_dict[CommitTypes.FIXED]:
            output_str += f"* {commit}\n\n"

    if commit_type_dict[CommitTypes.REMOVED]:
        output_str += "### Removed\n\n"
        for commit in commit_type_dict[CommitTypes.REMOVED]:
            output_str += f"* {commit}\n\n"

    if not any(commit_type_dict.values()):
        output_str += "### Notes\n\n"
        output_str += "* **No modifications were made**\n\n"

    return output_str


def find_pattern_in_text(text: str, pattern: str) -> re.Match[str] | None:
    """
    Find a pattern in a given text starting with "##\s".

    Args:
        text (str): The text in which to search for the pattern.
        pattern (str): The pattern to search for in the text.

    Returns:
        re.Match[str] | None: The match object if a match is found, otherwise None.
    """
    pattern = pattern.lstrip("^")
    pattern = r"##\s" + pattern
    pattern_regex = re.compile(pattern)
    return pattern_regex.search(text)


def list_tags_present_in_file(file_path: str,
                              version_pattern: str) -> List[str]:
    """
    Generate a list of tags present in a file that match a given version pattern.

    Parameters:
        - file_path (str): The path to the file.
        - version_pattern (str): The pattern to match against.

    Returns:
        - List[str]: A list of tags that match the version pattern.
    """
    output = []
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                matched = find_pattern_in_text(line, version_pattern)
                if matched:
                    tag = matched.group()[3:]
                    output.append(tag)

    return output


def write_new_content_to_changelog(file_path: str, content: str,
                                   version_pattern: str) -> None:
    """
    Write new content to the changelog file.

    Args:
        file_path (str): The path to the changelog file.
        content (str): The new content to be written to the changelog file.
        version_pattern (str): The pattern to match the version tag in the content.

    Returns:
        None: This function does not return anything.
    """
    output_str = ""
    first_tag_found = False

    content_tag = "0.0.0"
    content_tag_match = find_pattern_in_text(content, version_pattern)
    if content_tag_match:
        content_tag = content_tag_match.group()

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                if not first_tag_found:
                    matched = find_pattern_in_text(line, version_pattern)
                    if matched:
                        tag = matched.group()
                        if content_tag > tag:
                            first_tag_found = True
                            output_str += content

                output_str += line

    if not output_str.strip():
        output_str = content

    write_to_file(file_path, output_str)


def write_to_file(file_path: str, content: str):
    """
	Write the provided content to a file specified by the given path.

	Parameters:
		path (str): The path to the file.
		content (str): The content to write to the file.

	Returns:
		None
	"""
    with open(file_path, "w") as f:
        f.write(content)
