import subprocess
import os
from datetime import date

root_directory = os.path.dirname(os.path.realpath(__file__))
version_file_path = os.path.join(root_directory, "./version.txt")
semantic_levels = ['major', 'minor', 'patch']
version_number_levels = 2


def get_github_status():
    """
    Get status of the repo in which the script is run in. Return true if there
    are no uncommitted changes and false if there are changes. Additionally,
    print the uncommitted changes.
    Returns: bool
    """
    git_status_process = subprocess.run(["git", "status", "-s"],
                                        capture_output=True,
                                        cwd=root_directory)

    ret = git_status_process.stdout.decode('UTF-8')
    if not ret:
        print("Working tree is clean, ready to proceed.")
        return True

    print("There are uncommitted differences, cannot proceed.")

    print(ret)

    return False


def git_bump_and_pr(version_string: str):
    """
    Creates a new branch for bumping the version number, commits the updated
    version number.txt, pushes to the new branch, creates a pull request and
    checks out back into master and deletes the newly created local branch for
    the version bump.
    Args:
        version_string: string representation of the new version number.
    """
    git_create_branch = subprocess.run(["git", "checkout", "-b",
                                        f"bump_version_{version_string}"],
                                       capture_output=True,
                                       cwd=root_directory)
    ret_branch = git_create_branch.stdout.decode('UTF-8')
    print(ret_branch)

    subprocess.run(["git", "add", version_file_path])

    git_commit_process = subprocess.run(["git", "commit", "-m",
                                         f"Bump version to {version_string}"],
                                        capture_output=True,
                                        cwd=root_directory)
    ret_commit = git_commit_process.stdout.decode('UTF-8')
    print(ret_commit)

    print(f'Pushing to a new branch: bump_version_{version_string}')

    subprocess.run(["git", "push", "origin",
                    f"bump_version_{version_string}"], cwd=root_directory)

    subprocess.run(["gh", "pr", "create", "-B", "master", "-t",
                    f"Version bump to {version_string}", "-b",
                    "Version bump via script."], cwd=root_directory)

    print('Done creating a pull request.')

    subprocess.run(["git", "checkout", "master"], cwd=root_directory)

    subprocess.run(["git", "branch", "-D",
                    f'bump_version_{version_string}'], cwd=root_directory)

    return


def get_version_number():
    """
    Get version number from the version.txt file.
    Returns: version number as a string or None if problems are encountered.
    """
    try:
        version_file = open(version_file_path, "r")
        version_contents = version_file.read().splitlines()
        version_number_str = version_contents[0]
        version_file.close()
    except FileNotFoundError:
        print('version.txt not found!')
        return None
    except IndexError:
        print('Unexpected things in version.txt!')
        return None

    return version_number_str


def save_version_number(version_string: str):
    """
    Save version number and date of version to the version.txt file
    Args:
        version_string: the version number to be saved as a string.
    """
    version_date = date.today()
    version_file = open(version_file_path, "w")
    version_file.writelines([version_string, version_date])
    version_file.close()

    return


def parse_version_number(version_number_str: str):
    """
    Parse version number from a string.
    Args:
        version_number_str: string representing the version number. Should be in
    the format of semantic version numbers with desired number of levels.

    Returns: the parsed version number as a list of ints, or None if parsing is
        not successful.
    """
    parsing_successful = True
    version_number_split = version_number_str.split('.')
    version_number = []

    if len(version_number_split) > version_number_levels:
        print('Too many separators in version number!')
        parsing_successful = False

    if len(version_number_split) < version_number_levels:
        print('Too few separators in version number!')
        parsing_successful = False

    for element in version_number_split:
        try:
            version_number.append(int(element))
        except ValueError:
            print('There is something unexpected in the version number!')
            parsing_successful = False

    for element in version_number:
        if element < 0:
            print('No negative numbers in version number!')
            parsing_successful = False

    if not parsing_successful:
        return None

    return version_number


def update_version_number(current_version_number: list[int]):
    """
    Updates the version number based on user input. User can either input a
    hardcoded semantic level to bump the respective level, or their own version
    number. User can also cancel by entering 'c'.
    Args:
        current_version_number: current version number as a list of ints.

    Returns: an updated version number as a list of ints.
    """
    new_version_number = current_version_number.copy()
    input_accepted = False
    used_semantic_levels = []
    for i in range(version_number_levels):
        used_semantic_levels.append(semantic_levels[i])

    while not input_accepted:

        print('Enter either ' + ', '.join(used_semantic_levels) +
              ' to bump the respective semantic level, or enter your own '
              'version number. Enter c to cancel.')
        text_input = input().casefold()
        if text_input == 'c':
            input_accepted = True

        bump_level_found = False
        for i, semantic_level in enumerate(used_semantic_levels):
            if text_input == semantic_level:
                new_version_number[i] += 1
                bump_level_found = True
                input_accepted = True
                continue
            if bump_level_found:
                new_version_number[i] = 0

        if not bump_level_found and not input_accepted:
            parsed_version_number = parse_version_number(text_input)
            if parsed_version_number is not None:
                new_version_number = parsed_version_number
                input_accepted = True

    return new_version_number


def check_gh_cli_installation():
    """
    Checks if GitHub CLI is installed by running gh version command.
    Returns: bool, True if installation is found, false if not found.
    """
    gh_version_process = subprocess.run(["gh", "version"], capture_output=True, cwd=root_directory)
    ret_gh = gh_version_process.stdout.decode('UTF-8')
    if "gh version" in ret_gh:
        return True
    return False


def check_git_installation():
    """
    Checks if Git is installed by running git version command.
    Returns: bool, True if installation is found, false if not found.
    """
    git_version_process = subprocess.run(["git", "version"], capture_output=True, cwd=root_directory)
    ret_git = git_version_process.stdout.decode('UTF-8')
    if "git version" in ret_git:
        return True
    return False


def version_bump_process():
    """
    Function that manages the whole process of updating the version number.
    Returns:
    """
    if check_git_installation() is False:
        print("Git not installed. Install Git first. Aborting process.")
        return
    if check_gh_cli_installation() is False:
        print("GitHub CLI not installed. Install GitHub CLI first. "
              "Aborting process.")

    current_version_string = get_version_number()
    current_version_number = parse_version_number(current_version_string)
    if current_version_number is None:
        print('Aborting process.')
        return

    print(f'Current version number is {current_version_string}')

    working_tree_is_clean = get_github_status()
    if not working_tree_is_clean:
        return

    new_version_number = update_version_number(current_version_number)
    new_version_string = '.'.join(str(x) for x in new_version_number)

    if new_version_number == current_version_number:
        print('Version number bump cancelled.')
        return

    print(f'New version number would be {new_version_string}')
    print('Continue with this number y/n? Last chance to cancel.')
    continue_response = input().casefold()
    if continue_response == 'y':
        save_version_number(new_version_string)
        git_bump_and_pr(new_version_string)
    else:
        print('Version number bump cancelled.')

    return


if __name__ == "__main__":
    version_bump_process()
