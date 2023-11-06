import argparse
import re
import utils

parser = argparse.ArgumentParser(prog="Changelog Updater",
                                 description="Update the changelog.md file",
                                 add_help=True,
                                 allow_abbrev=True)

DIVSOR_CHAR = "###"
VERSION_PATTERN_STR = "\\d+\\.\\d+\\.\\d+(\\-((alpha)|(beta)|(rc)))?"
TAG_PATTERN = re.compile(f"^tag:\\s{VERSION_PATTERN_STR}")


def main(arguments: argparse.Namespace):
    valid_tags = utils.get_valid_tags()
    log_list = utils.get_git_logs_list(valid_tags[0], DIVSOR_CHAR)
    output_str = utils.get_changelog_md_header(arguments.output,
                                               arguments.force)
    commit_type_dict = utils.clear_commit_type_dict()
    existent_tags = utils.list_tags_present_in_file(arguments.output,
                                                    VERSION_PATTERN_STR)
    tag_exists = True
    update_commits = False

    for log in log_list:
        log_items = log.split(DIVSOR_CHAR)
        tag = log_items[0]
        commit = log_items[1]
        date = log_items[2]
        matched_tag = TAG_PATTERN.match(tag)

        if matched_tag:
            initial_index = matched_tag.span()[0] + 5
            tag = tag[initial_index:matched_tag.span()[1]]
            tag_exists = tag in existent_tags
            is_new_tag = True if not tag_exists and (
                len(existent_tags) == 0 or tag > existent_tags[0]) else False

            if update_commits:
                update_commits = False
                output_str = utils.get_changelog_tag_body(
                    output_str, commit_type_dict)
                commit_type_dict = utils.clear_commit_type_dict()

            if is_new_tag or arguments.force:
                output_str += "## {} - [{}]\n\n".format(tag, date, commit)
                update_commits = True

            if output_str.find("0.0.1-beta") > -1:
                output_str += "### Notes\n\n"
                output_str += "* **Start of J.Assy versioning system**\n\n"
                break

        commit_type = utils.get_commit_type(commit)

        if commit_type != utils.CommitTypes.MERGES:
            commit_type_dict[commit_type].append(commit)

    if arguments.force:
        utils.write_to_file(file_path=arguments.output, content=output_str)
    else:
        utils.write_new_content_to_changelog(arguments.output, output_str,
                                             VERSION_PATTERN_STR)


if __name__ == "__main__":
    utils.setup_cli_arguments(parser)
    arguments = parser.parse_args()
    main(arguments)
