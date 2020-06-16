# ideaseed

---

_Disclaimer_ This project is at a "I'm figuring out the interface" state, so nothing is working yet.

---

Do you have ideas suddenly and just wished you could catch them as fast as possible, as to not loose them, without having to interrupt what you were doing?

As I guy without a lot of more or less stupid ideas, I use Google Keep as a centralized place to put all of my thoughts that I deem worthy of consideration.

I recently started to use GitHub Projects for _coding_ project ideas as a [single project called "incubator" on my GitHub profile directly](https://github.com/ewen-lbh?tab=projects), and as issues or notes when the idea is related to an already-existing project and repo.

But when I don't get to decide _when_ this idea comes, and I often need to interrupt what am I doing to open github, get to the right page, input my idea and get back. And I find it frustrating.

So I started this CLI, as my first Go project, and my first project consuming a GraphQL API (GitHub's)

I'm also using an unofficial, reverse-engineered REST API—turns out Google Keep doesn't have an official one.

Enough rambling. Here's what you came for.

## Usage

The interface itself is pretty simple and POSIX-compliant

```bash
ideaseed [options] [[OWNER/]REPO [PROJECT [COLUMN]]] IDEA
```

`[OWNER/]REPO` allows you to select a repository. If not given, the idea will be added to Google Keep
If the `OWNER/` part is omitted, your GitHub username is assumed.

`PROJECT` allows you to select a project by name to put your card to. If omitted, `REPO` is assumed (eg `ideaseed myrepo "do this thing"` is the same as `ideaseed myrepo myrepo "do this thing"`)

`COLUMN`, much like `PROJECTS`, allows you to select a project's column by name, and defaults to `To-Do`

### Options

| Shorthand | Full-length      | Description                                                                                          |
| --------- | ---------------- | ---------------------------------------------------------------------------------------------------- |
| -p        | --project        | Creates a GitHub project on your user profile instead of a Google Keep card if REPO is not given     |
| -c        | --color COLOR    | Chooses which color to use for Google Keep cards. See [Color names](#color-names) for allowed values |
| -t        | --tag TAG        | Adds tags to the Google Keep card.                                                                   |
| -i        | --issue TITLE    | Creates an issue with title TITLE.                                                                   |
| -I        | --interactive    | Prompts you for the above options when they are not provided.                                        |
|           | --create-missing | Create non-existant tags, projects or columns specified (needs confirmation if -I is used)           |
|           | --about          | Details about ideaseed like currently-installed version                                              |
|           | --version        | Like --about, without dumb and useless stuff                                                         |

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

#### Relax. You don't need to remember those options

You can also use `ideaseed -?` to prompt you for some information:

- Where do you want to upload this idea? (github, google keep)
- If you decide to use github,
  - On your profile?
  - If not:
    - Which repo? (using REPO or OWNER/REPO) (autocompletes with repositories you contribute to)
    - Which column? (choices are the column names, and you can type the column's index to be quicker)
- If you decide to use google keep,
  - Which color? (defaults to white)
  - Some tags?
