#====================================
# Crawler on Pydigger + Git. by DK
# To be used on user's own risk, author takes no responsibility whatsoever.

# Aug 12 2024.
# # Ver 10. Last updates:
#          - Logs only not previously logged projects
#
#  The purpose of this module is to run through pydigger.com/stats -> "Has VCS but no author" page.
#  The page shows list of projects with no "authors=<name>" line in setup.py file. This program is used to
#  narrow all projects down to whose where "authors=<name>" line would be recommended to add (setup.py is present,
#  pyproject.toml, which contains authors normally, is not used).
#
#  1. goes to https://pydigger.com/search/has-vcs-no-author and reads all entries there
#  2. checks individual json file on each entry and extracts links to /github projects if available
#  3. checks each /github link and keeps those which have setup.py file
#  4. filters out all projects with pyproject.toml files
#  5. makes final list and writes to logfile
# =====================================

import sys
import requests
import re
import datetime


def get_link_from_pdig(page: str) -> list:
    """
    Looks for pattern:
    ----------------------
    <td><a href="/pypi/xxx-xxxx-xxxx...xxx"
    ----------------------
    :param page: 'master' page on pydigger.com containing projects
    :return: list of links to projects' json files
    """
    # checking if web page opens
    response = requests.get(page)
    if response.status_code != 200:
        print('Failed to retrieve the webpage. Status code:', response.status_code)
        return

    json_link_list = []
    matches = re.findall(r'<td><a href="/pypi/([\w-]+)', response.text)
    for link in matches:
        json_link_list.append('https://pydigger.com/pypi/' + link)
    return json_link_list


def get_link_from_json(json_site: str) -> list:
    """
    Looks for pattern
    -------------------------
      "project_urls": {
      "Homepage": "https://github.com/iqmo-org/iql",
      "Issues": "https://github.com/iqmo-org/iql/issues",
      "Repository": "https://github.com/iqmo-org/iql"
    }
    -------------------------
    in json file, containing links to Github. If the pattern is present, links to Github be returned as a list
    with 1 or 2 elements representing Homepage, or Repository, or Homepage and Repository both
    (only if they are different).
    If project_urls pattern isn't found, [] will be returned.

    :param json_site - link to webpage where json file is displayed
    :return: git_list - list of 0, or 1, or 2 addresses to "Homepage", and "Repository"
    """
    git_response = requests.get(json_site)
    if git_response.status_code != 200:
        print(f'Failed to retrieve the webpage. Page{json_site} Status code:', git_response.status_code)
        return []
    git_list = []
    source_jason = git_response.text

    get_json_pattern = re.compile(r'project_urls[^}]*')
    matches = get_json_pattern.finditer(source_jason)
    for match in matches:   # runs only once or never, not really a for-loop
        start, stop = match.span()
        git_chunk = source_jason[start:stop]

        home_pattern = re.findall(r'Homepage&#34;: &#34;(https://git[-_a-zA-Z/.d]+)', git_chunk)
        rep_pattern = re.findall(r'Repository&#34;: &#34;(https://git[-_a-zA-Z/.d]+)', git_chunk)

        if home_pattern:
            git_list += home_pattern
        if rep_pattern and rep_pattern != home_pattern:
            git_list += rep_pattern

    return git_list


def check_setup_py_in_git(unfiltered_links: list) -> list:
    """
    Checks if projects contain 'setup.py' files, only those links remain in result list of links,
    other links to projects without 'setup.py' are filtered out.
    :param unfiltered_links: list of input links
    :return: filtered links
    """
    filtered_links = []
    for i, link in enumerate(unfiltered_links):
        response = requests.get(link)
        if response.status_code != 200:
            print(f'check_congig_get: '
                  f'Failed to retrieve the webpage {link}. Status code:', response.status_code)
        else:
            print('Analysing presence of setup.py file on github', i)
            web_text = response.text

            pattern = re.compile(r'setup\.py')
            matches = pattern.findall(web_text)
            if matches:
                filtered_links.append(link)

    return filtered_links


def filter_toml_in_git(unfiltered_links: list) -> list:
    """
    Filters out all links to projects which contain 'pyproject.toml' files, since those files 99% have authors coded
    already.
    :param unfiltered_links: list of input links
    :return: filtered links
    """
    filtered_links = []
    for i, link in enumerate(unfiltered_links):
        response = requests.get(link)
        if response.status_code != 200:
            print(f'filter_toml_in_git: '
                  f'Failed to retrieve the webpage {link}. Status code:', response.status_code)
        else:
            print('Analysing presence of pyproject.toml file on github', i)
            web_text = response.text

            pattern = re.compile(r'pyproject\.toml')
            matches = pattern.findall(web_text)
            if not matches:
                filtered_links.append(link)

    return filtered_links


def filterout_logged(current_log_file_name, candidate_list) -> list:
    filtered_list = []
    count = 0
    with open(current_log_file_name, 'r') as f:
        in_str = f.read()
    for candidate in candidate_list:
        if candidate not in in_str.split():
            filtered_list.append(candidate)
        else:
            count += 1
            print('Removing : ', count, candidate)
    print('Filtered as previously logged : ', count)
    return filtered_list


def main():
    NUMBER_OF_ENTRIES = 20    # Number of projects to analyze, counting from the most recent entry
    pydigger_link = f'https://pydigger.com/search/has-vcs-no-author?q=&page=1&limit={NUMBER_OF_ENTRIES}'
    log_file_name = 'git_log.txt'

    print(f"Running for {NUMBER_OF_ENTRIES} projs..")

    # running preparation
    pdig_link_list = get_link_from_pdig(pydigger_link)

    # running 1st scan. Getting github links from json
    git_link_list = []
    for i, link in enumerate(pdig_link_list):
        print('Scanning PyDigger entries: #', i)
        new_link_to_github = get_link_from_json(link)
        if new_link_to_github:
            git_link_list += new_link_to_github

    print(f'Pydigger source: {len(pdig_link_list)}, alive on Github count: {len(git_link_list)}')

    # running 2nd scan. Checking setup.py
    print('Ensuring setup.py on Github now..')
    gits_checked_list = check_setup_py_in_git(git_link_list)
    print('Projs with setup.py count: ', len(gits_checked_list))

    # running 3rd scan. Checking pyproject.toml
    print('Filtering pyproject.toml files on Github now..')
    gits_checked_list = filter_toml_in_git(gits_checked_list)
    print('Projs without pyproject.toml count: ', len(gits_checked_list))

    # filtering out already logged
    gits_checked_list = filterout_logged(log_file_name, gits_checked_list)

    print(' :\n' + '\n'.join(gits_checked_list) + '\n')

    # Appending list of resulted checked links into log file
    utc_now = datetime.datetime.utcnow()
    output_lines = '\n\n\n\nResults ' + str(utc_now) + ' :\n' + '\n'.join(gits_checked_list) + '\n'

    with open(log_file_name, 'a') as log_file:
        log_file.write(output_lines)


if __name__ == '__main__':
    main()

