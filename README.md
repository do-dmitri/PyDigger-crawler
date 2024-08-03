The purpose of this module is to run through pydigger.com/stats -> "Has VCS but no author" page.
The page shows list of projects with no "authors=<name>" line in setup.py file. This program is used to
narrow all projects down to whose where "authors=<name>" line would be recommended to add (setup.py is present,
pyproject.toml, which contains authors normally, is not used).

1. goes to https://pydigger.com/search/has-vcs-no-author and reads all entries there
2. checks individual json file on each entry and extracts links to /github projects if available
3. checks each /github link and keeps those which have setup.py file
4. filters out all projects with pyproject.toml files
5. makes final list and writes to logfile
