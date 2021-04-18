<center><p align="center">
<img alt="ideaseed" src="https://raw.githubusercontent.com/ewen-lbh/ideaseed/master/visual-identity/ideaseed-logomark-color-transparent.svg" width="550px">
  <br>
<a href="https://pypi.org/project/ideased"><img alt="PyPI Latest version" src="https://img.shields.io/pypi/v/ideaseed"/></a>
<a href="https://pepy.tech/project/ideaseed"><img alt="Downloads count" src="https://pepy.tech/badge/ideaseed"/></a>
</p></center>

Do you have ideas suddenly and just wished you could catch them as fast as possible, as to not loose them, without having to interrupt what you were doing?

As I guy with a lot of more or less stupid ideas, I use Google Keep as a centralized place to put all of my thoughts that I deem worthy of consideration.

I recently started to use GitHub Projects for _coding_ project ideas as a [single project called "incubator" on my GitHub profile directly](https://github.com/ewen-lbh?tab=projects), and as issues or notes when the idea is related to an already-existing project and repo.

But when I don't get to decide _when_ this idea comes, and I often need to interrupt what am I doing to open github, get to the right page, input my idea and get back. And I find it frustrating.

Enough rambling. Here's what you came for.

Note down your ideas and get them to the right place, without switching away from your terminal

<details>
<summary>Table of contents</summary>
<ul>
<li><a href="#installation">Installation</a></li>
<li><a href="#authentication">Authentication</a></li>
<li><a href="#usage">Usage</a>
<ul>
<li><a href="#create-a-google-keep-card">Create a Google Keep card</a></li>
<li><a href="#create-an-issue-andor-a-projects-card-on-a-repository">Create an issue and/or a Projects card on a repository</a></li>
<li><a href="#create-a-card-on-a-project-tied-to-your-user-profile">Create a card on a project tied to your user profile</a></li>
<li><a href="#providing-other-information">Providing other information</a>
<ul>
<li><a href="#labels">Labels</a></li>
<li><a href="#assigneescollaborators">Assignees/Collaborators</a></li>
<li><a href="#milestones">Milestones</a></li>
<li><a href="#pin-status">Pin status</a></li>
<li><a href="#colors">Colors</a></li>
</ul></li>
<li><a href="#other-features">Other features</a>
<ul>
<li><a href="#--open"><code>--open</code></a></li>
<li><a href="#--dry-run"><code>--dry-run</code></a></li>
</ul></li>
</ul></li>
<li><a href="#configuration">Configuration</a>
<ul>
<li><a href="#defaults">Defaults</a></li>
<li><a href="#miscelleanous-options">Miscelleanous options</a>
<ul>
<li><a href="#--self-assign-auto-assigning-yourself"><code>--self-assign</code> Auto-assigning yourself</a></li>
<li><a href="#--create-missing-prompt-for-creation-of-missing-stuff"><code>--create-missing</code>: Prompt for creation of missing stuff</a></li>
<li><a href="#--check-for-updates-get-notified-when-a-new-version-of-ideaseed-is-released"><code>--check-for-updates</code>: Get notified when a new version of ideaseed is released.</a></li>
<li><a href="#--auth-cachefilepath-change-the-auth-cache-location"><code>--auth-cache=FILEPATH</code>: Change the auth cache location</a></li>
</ul></li>
</ul></li>
<li><a href="#updating">Updating</a></li>
<li><a href="#complete-usage-from---help">Complete usage from <code>--help</code></a></li>
</ul>
</details>

## Installation

Ideaseed is available [on PyPI.org](https://pypi.org/project/ideaseed):

```sh
pip install ideaseed
```

### Arch Linux

Arch users can also get _ideaseed_ from the AUR:

- latest stable: [`ideaseed`](https://aur.archlinux.org/packages/ideaseed)
- bleeding edge (latest commit): [`ideaseed-git`](https://aur.archlinux.org/packages/ideaseed-git)

## Authentication

Authentication credentials are asked for when necessary, and are cached in a JSON file referred to as the 'auth cache'.
The location of that auth cache is configurable through the `--auth-cache` flag.

You can manually login to both Google Keep and GitHub with `ideaseed login`, and clear the cache with `ideaseed logout`.

A support for keyrings as an alternative authentication method [is planned](https://github.com/ewen-lbh/ideaseed/issues/153)

## Usage

Ideas are made up of different pieces of data, of which only the _body_ is necessary.

- body: the body of your idea, the main content
- title
- project: the GitHub project to put the card in
- column: the project's column to put the card in
- repo: the repository to create the card (and issue) in (only relevant when adding to a repository)

Thus, ideaseed's usage patterns are varied:

### Create a Google Keep card

Provide only the body, a Google Keep card will be created, with no title:
```
ideaseed [options] BODY
```
Same as above, but provide a title:
```
ideaseed [options] TITLE BODY
```

### Create an issue and/or a Projects card on a repository

Also provide a repository name (and owner if it isn't you):
```
ideaseed [options] REPO TITLE BODY
```
If you have set defaults for the project and column names, they will get used.
Otherwise, no Github Projects card will be created. 

Finally, providing the column and/or the project:
```
ideaseed [options] REPO COLUMN TITLE BODY
ideaseed [options] REPO PROJECT COLUMN TITLE BODY
```

Note that you are not forced to use those combinations, as these arguments also exist in `--flag` forms: `-C/--column` for `COLUMN`, etc.

You can use `-I/--no-issue` to only create a Project card.

### Create a card on a project tied to your user profile

If you want to create a github card on a project that's tied to your user profile instead of to a repository, put `user` in front, and drop `REPO`:

```
ideaseed [options] user BODY
ideaseed [options] user TITLE BODY
ideaseed [options] user PROJECT TITLE BODY
ideaseed [options] user PROJECT COLUMN TITLE BODY
```

### Providing other information

#### Labels

Add labels by using `-#/--label` one or more times.
This works on Google Keep or when creating issues. 

#### Assignees/Collaborators

Add assignees (github issues) or collaborators (Google Keep) by using `-@/--assign` one or more times.
Use usernames for github issues and emails for Google Keep cards.


#### Milestones

Assign an issue to a milestone by specifying its name with `-M/--milestone`.

#### Pin status

Pin your Google Keep card with `--pin`.
Support for github issues [is planned](https://github.com/ewen-lbh/issues/155)

#### Colors

Give your Google Keep card a color with `--color NAME`. `NAME` can be:

- blue
- brown
- darkblue (or indigo)
- gray (or grey)
- green
- orange
- pink
- purple (or magenta)
- red
- teal (or cyan)
- white
- yellow

### Other features

#### `--open`

Open the created issue/card in your favorite browser (uses [`webbrowser.open`](https://docs.python.org/3/library/webbrowser.html#webbrowser.open))

#### `--dry-run`

Do a 'test run'. Does not create issues and cards. Note that missing resources tthat were created with `--create-missing` still do get created.

The following will appear to let you know that you are dry-running:

> You are in **dry-run mode**.
>
> Issues and cards will not be created.
>
> Creation of objects from --create-missing will still occur
>
> _(e.g. missing labels will be created if you answer 'yes')_

## Configuration

Configuration is done through aliasing ideaseed and adding flags to the alias.
This configuration can be done interactively with `ideaseed config`.

It will ask you some questions to configure your alias, then append the alias to your current shell's rc file (supported shells are fish, bash, zsh, csh, ksh and tcsh. Feel free to add more shells through PRs or issues!)

### Defaults

You can specify default values for `COLUMN` and `PROJECT`. You can use {placeholders} in these default values to make them dynamic. The format is the same as python's [`str.format`](https://pyformat.info/), so you can also do things like trimming!

| Flag | Sets default value for | Available placeholders |
|------|------------------------|------------------------|
| `--default-project` | `PROJECT` | {repository}, {username}, {owner} |
| `--default-column` | `COLUMN` | {project}, {repository}, {username}, {owner} |

### Miscelleanous options

#### `--self-assign` Auto-assigning yourself

With this flag, if `-@/--assign` is not used, you are assigned to the created issue automatically. Does not assign yourself as a collaborator in Google Keep.

#### `--create-missing`: Prompt for creation of missing stuff

If a label, milestone, project or column does not exist but is used, you will be asked whether or not you want to create that missing resource. 

If you say no, the command will be cancelled and nothing will happen. 

If you say yes, the missing object will get created (you might enter additional informtion such as a column's description) and the issue and/or card will also get created.

#### `--check-for-updates`: Get notified when a new version of ideaseed is released.

With this flag, if you run ideaseed and that it detects that a newer version is available, a notification will appear.

You can then [update ideaseed](#Updating).

#### `--auth-cache=FILEPATH`: Change the auth cache location

If you want to change where ideaseed caches your authentication credentials, use this flag.

## Updating

You can update ideaseed with the `update` command (or directly from your package manager).

## Complete usage from `--help`

```
Note down your ideas and get them to the right place, without switching away from your terminal
Usage:
    ideaseed [options] config
    ideaseed [options] logout
    ideaseed [options] login
    ideaseed [options] about | --about
    ideaseed [options] version | --version
    ideaseed [options] help | --help
    ideaseed [options] update
    ideaseed [options] [-# LABEL...] [-@ USER...] user BODY
    ideaseed [options] [-# LABEL...] [-@ USER...] user TITLE BODY
    ideaseed [options] [-# LABEL...] [-@ USER...] user PROJECT TITLE BODY
    ideaseed [options] [-# LABEL...] [-@ USER...] user PROJECT COLUMN TITLE BODY
    ideaseed [options] [-# LABEL...] [-@ USER...] BODY
    ideaseed [options] [-# LABEL...] [-@ USER...] TITLE BODY
    ideaseed [options] [-# LABEL...] [-@ USER...] REPO TITLE BODY
    ideaseed [options] [-# LABEL...] [-@ USER...] REPO COLUMN TITLE BODY
    ideaseed [options] [-# LABEL...] [-@ USER...] REPO PROJECT COLUMN TITLE BODY
Commands:
    user                    Creates cards in your user's project. 
                            (see https://github.com/users/YOURUSERNAME/projects)
                            Flags --no-issue and --repo has no effects.
                            Flag --default-column still applies.
                            REPO is _not_ set to 'user'.
    config                  Configures an alias with Configuration flags through a series of questions.
    log(in/out)             Fills/Clears the auth cache (see --auth-cache).
    about                   Show information about ideaseed.
    version                 Outputs the version number
    update                  Check for updates. If any is available, shows the changelog. 
                            You can then decide to install the new version.
Arguments:
    BODY      Sets the note's body. Required.
    TITLE     Sets the title.
    REPO      The repository to put the issue/card into. Uses the format [USER/]REPO. 
              If USER/ is omitted, the currently-logged-in user's username is assumed.
              Omitting this argument entirely has the effect of creating a Google Keep card instead.
              When used without PROJECT, the card is added to the Default Project (see --default-project)
              If the Default Project is '<None>', it creates an issue without a project card.
    PROJECT   Specify which GitHub project to add the card to.
              When used without COLUMN, the card is added to the Default Column (see --default-column)
              Can use Placeholders
    COLUMN    Specify which column to use.
              Can use Placeholders.
Options:
    -I --no-issue           Only creates a project card, no issue is created.
                            Has no effect when used without a REPO
    -T --title=TITLE        Specifies TITLE
    -R --repo=REPO          Specifies REPOSITORY
    -P --project=PROJECT    Specifies PROJECT
    -C --column=COLUMN      Specifies COLUMN
    -# --label=LABEL...     Add labels
                            Can be specified multiple times.
                            Cannot be used in the 'user' command.
                            Cannot be used with --no-issue
    -o --open               Open the created card (or issue) in your $BROWSER.
       --dry-run            Tell what will happen but does not do it. Still logs you in.
                            Beware, objects created with --create-missing will
                            still be created.
    -m --create-missing     Creates missing objects (projects, columns, and labels/labels)
    -@ --assign=USER...     Assign USER to the created issue. 
                            Can be specified multiple times.
                            Cannot be used in the 'user' command.
                            Cannot be used with --no-issue
    REPO only: 
       --self-assign        Assign the created issue to yourself. 
                            Has no effect when --assign is used.
    -M --milestone=NAME     Adds the issue to the milestone NAME.
    Google Keep only:
       --pin                Pins the card. 
       --color=COLOR        Sets the card's color. [default: white]
                            Available values: blue, brown, darkblue (or indigo), 
                            gray (or grey), green, orange, pink, purple (or magenta), 
                            red, teal (or cyan), white, yellow. 
Configuration:
   --default-column=COLUMN    Specifies the Default Column. 
                              Used when PROJECT is set but not COLUMN
                              Can use Placeholders.
   --default-project=PROJECT  Specifies the Default Project. 
                              Used when REPO is set but not PROJECT
                              Can use Placeholders.
                              If not set, or set to '<None>',
                              using REPO without PROJECT creates an issue
                              without its project card.
   --auth-cache=FILEPATH      Set the filepath for the auth. cache [default: ~/.cache/ideaseed/auth.json]
                              If set to '<None>', disables caching of credentials.
                              Has no effect when used with --keyring.
   --check-for-updates        Check for new versions and show a notification if a new one is found.
Placeholders:
    {repository}      Replaced with the repository's name
    {owner}           Replaced with the repository's owner
    {username}        Replaced with the currently-logged-in GitHub user's username
    {project}         Replaced with the project the card will be added to.
                      Not available to --default-project or PROJECT.
```

[v1.0.0]: https://github.com/ewen-lbh/ideaseed/milestone/2
[v0.4.0]: https://github.com/ewen-lbh/ideaseed/tree/master/CHANGELOG.md#040---2020-06-18
[v0.9.0]: https://github.com/ewen-lbh/ideaseed/blob/master/CHANGELOG.md#090---2020-06-22

* * *

<center><p align="center">
  <img src="https://raw.githubusercontent.com/ewen-lbh/ideaseed/master/visual-identity/ideaseed-logo-black-transparent.png" width="40px">
  <br>
  ideaseed by <a href="https://ewen.works">Ewen Le Bihan</a>
</p></center>
