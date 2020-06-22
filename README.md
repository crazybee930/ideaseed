# ![ideaseed](visual-identity/ideaseed-logomark-color-transparent.svg)

Do you have ideas suddenly and just wished you could catch them as fast as possible, as to not loose them, without having to interrupt what you were doing?

As I guy without a lot of more or less stupid ideas, I use Google Keep as a centralized place to put all of my thoughts that I deem worthy of consideration.

I recently started to use GitHub Projects for _coding_ project ideas as a [single project called "incubator" on my GitHub profile directly](https://github.com/ewen-lbh?tab=projects), and as issues or notes when the idea is related to an already-existing project and repo.

But when I don't get to decide _when_ this idea comes, and I often need to interrupt what am I doing to open github, get to the right page, input my idea and get back. And I find it frustrating.

Enough rambling. Here's what you came for.

Note down your ideas and get them to the right place, without switching away from your terminal

## Installation

Ideaseed is available [on PyPI.org](https://pypi.org/project/ideaseed):

```sh-session
pip install ideaseed
```

See [Installation troubleshooting](#installation-troubleshooting) if you can't install it like this.

## Usage

```bash
ideaseed (--help | --about | --version)
ideaseed [options] ARGUMENTS...
```

### Examples

```sh-session
# Save a card "test" in schoolsyst/webapp > project "UX" > column "To-Do"
$ ideaseed schoolsyst/webapp UX "test"
# Save a card "lorem" in your-username/ipsum > project "ipsum" > column "To-Do"
$ ideaseed ipsum "lorem"
# Save a card "a CLI to note down ideas named ideaseed" in your user profile > project "incubator" > column "willmake"
$ ideaseed --user-keyword=project --user-project=incubator project "a CLI to note down ideas named ideaseed"
```

### Arguments

| Argument | Meaning                                                                                                              | Default value  |
| -------- | -------------------------------------------------------------------------------------------------------------------- | -------------- |
| REPO     | Select a repository by name                                                                                          |
|          | If not given, uses Google Keep instead of GitHub (or uses your user profile's projects if --project is used)         |
|          | If --user-keyword's value is given, creates a card on your user's project (select which project with --user-project) |
|          | If given in the form OWNER/REPO, uses the repository OWNER/REPO                                                      |
|          | If given in the form REPO, uses the repository "your username/REPO"                                                  |
| PROJECT  | Select a project by name to put your card to [default: REPO's value]                                                 | `REPO`'s value |
|          | If creating a card on your user's project, this becomes the COLUMN                                                   |
| COLUMN   | Select a project's column by name [default: To-Do]                                                                   | To-Do          |
|          | If creating a card on your user's project, this is ignored                                                           |

### Options

| Shorthand | Full-length            | Description                                                                                                     |
| --------- | ---------------------- | --------------------------------------------------------------------------------------------------------------- |
| -c        | --color COLOR          | Chooses which color to use for Google Keep cards. See [Color names](#color-names) for a list of valid values    |
| -t        | --tag TAG              | Adds tags to the Google Keep card. Can also be used on GitHub together with --issue to add labels to the issue. |
| -i        | --issue TITLE          | Creates an issue with title TITLE.                                                                              |
| -I        | --interactive          | Prompts you for the above options when they are not provided.                                                   |
| -L        | --logout               | Clears the authentification cache                                                                               |
| -m        | --create-missing       | Create non-existant tags, projects or columns specified (needs confirmation if -I is used)                      |
| -o        | --open                 | Open the relevant URL in your web browser.                                                                      |
| -l        | --label LABEL          | Alias for --tag. See --tag's description.                                                                       |
| -@        | --assign-to USERNAME   | Assigns users to the created issue. Only works when --issue is used.                                            |
| -M        | --milestone TITLE      | Assign the issue to a milestone with title TITLE.                                                               |
|           | --pin                  | Pin the Google Keep card                                                                                        |
|           | --about                | Details about ideaseed like currently-installed version                                                         |
|           | --version              | Like --about, without dumb and useless stuff                                                                    |
|           | --user-project NAME    | Name of the project to use as your user project                                                                 |
|           | --user-keyword NAME    | When REPO is NAME, creates a GitHub card on your user profile instead of putting it on REPO                     |
|           | --no-auth-cache        | Don't save credentials in a temporary file                                                                      |
|           | --no-check-for-updates | Don't check for updates, don't prompt to update when current version is outdated                                |
|           | --no-self-assign       | Don't assign the issue to yourself                                                                              |

#### Color names

- blue
- brown
- darkblue
- gray
- green
- orange
- pink
- purple
- red
- teal
- white
- yellow

You don't have to specify the whole color name, just enough to be non-ambiguous:

- bl
- br
- d
- gra
- gre
- o
- pi
- pu
- r
- t
- w
- y

Some color have aliases:

- cyan is the same as teal
- indigo is the same as darkblue
- grey is the same as gray
- magenta is the same as purple

#### Relax. You don't need to remember those options

You can also use `ideaseed -I` to prompt you for some information:

- Where do you want to upload this idea? (github, google keep)
- If you decide to use github,
  - On your profile?
  - If not:
    - Which repo? (using REPO or OWNER/REPO) (autocompletes with repositories you contribute to)
    - Which column? (choices are the column names, and you can type the column's index to be quicker)
- If you decide to use google keep,
  - Which color? (defaults to white)
  - Some tags?

## Installation troubleshooting

If you get an error message saying "No matching distribution found":

```sh-session
$ pip install ideaseed
Collecting ideaseed
  Could not find a version that satisfies the requirement ideaseed (from versions: )
No matching distribution found for ideaseed
```

See if the python version `pip` uses is at least 3.6:

```sh-session
$ pip --version
pip 9.0.1 from /usr/lib/python2.7/dist-packages (python 2.7) # Should be at least "(python 3.6)"
```

You can then try with `pip3` (`pip3 --version` should report a python version of at least 3.6):

```sh-session
$ pip3 --version
pip 20.0.2 from /home/ewen/.local/lib/python3.7/site-packages/pip (python 3.7)
$ pip3 install ideaseed
```
