# Ideasprout

---

_Disclaimer_ This project is at a "I'm figuring out the interface" state, so nothing is working yet.

---

Do you have ideas suddenly and just wished you could catch them as fast as possible, as to not loose them, without having to interrupt what you were doing?

As I guy without a lot of more or less stupid ideas, I use Google Keep as a centralized place to put all of my thoughts that I deem worthy of consideration.

I recently started to use GitHub Projects for _coding_ project ideas as a [single project called "incubator" on my GitHub profile directly](https://github.com/ewen-lbh?tab=projects), and as issues or notes when the idea is related to an already-existing project and repo.

But when I don't get to decide _when_ this idea comes, and I often need to interrupt what am I doing to open github, get to the right page, input my idea and get back. And I find it frustrating.

So I started this CLI, as my first Go project, and my first project consuming a GraphQL API (GitHub's)

I'm also using an unofficial, reverse-engineered REST API—turns out Google Keep doesn't have an official one.

Enough rambing. Here's what you came for.

## Usage

The interface itself is pretty simple and POSIX-compliant

```bash
ideasprout your idea and no you dont need quotes because that takes too much time
```

Obviously, depending on your shell, you might want to escape special characters or use quotes

### Options

[[Jump straight to the options table](#options-table)]

By default, the latter example will add a new card to your Google Keep account. To save it to GitHub, you can add the `--gh` flag. `--gh` optionally takes an argument, which is either `REPO` (resolves to `your-user-name/REPO`) or `OWNER/REPO`. You can also pass `-p` or `--project` and type the name of the project to add the card to. 

In all cases, the card will get added to the leftmost column, except with `-c` or `--column`, which can be given a column name or an index, starting from one. If the column name does not exist, it'll choose the closest column that exists by fuzzy matching. You can also use `--create-columns` and it'll create them for you, after you confirm (you don't want to create columns accidently by making a typo, don't you?).

With Google Keep, you can use `--color` or `-d` (d for **d**ye) to specify one of these colors:

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

Also with Google Keep, you can add tags to your card with `--tag` or `-t`. If your tag contains spaces, you must quote the option's argument. Of course you can add multiple tags by using the argument multiple times: `ideasprout -t web -t app a webapp to permanently solve all conflicts in the world` will add both tags `web` and `app`. Same as with `--column`, non-existant tags will resolve to the closes ones by fuzzy matching, and you can also use `--create-tags` to create them, after being prompted.

#### Relax. You don't need to remember those options

You can also use `ideasprout -?` to prompt you some information:

- Where do you want to upload this idea? (github, google keep)
- Which repo? (using REPO or OWNER/REPO) (autocompletes with repositories you contribute to)
- Which column? (choices are the column names, and you can type the column's index to be quicker)

#### Type even less not-your-idea stuff

If you always want to be prompted, or always post to github, or just to type faster, you can make your alias to "configure" ideasprout (no config files are planned for now, I'm trying to follow [n³'s way of configuring things](https://github.com/jarun/nnn#quickstart)).

This works well because, as you don't need quotes to type your idea, dashes are of course allowed in your idea, and so flags need to be added before the idea text. Thus, aliases work well in this case because you only have to _append_ input.

As an example, if you want to only have to type `idea` to use `ideasprout --gh -c To-Do`, do

```bash
alias idea="ideasprout --gh --column To-Do"
```

And you're all set!

#### Options table

| Shorthand            | Flag               | Arguments        | Repeatable | Description                                                                                                                                                                                                                              |
| -------------------- | ------------------ | ---------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-g`                 | `--gh`             | `[[OWNER/]REPO]` |            | Put the idea to github. If no argument is given, the card is added to one of the user's projects.                                                                                                                                        |
| `-p`                 | `--project`        | `PROJECT NAME`   |            | Select which project to put the project too. Can only be used with `--gh`.                                                                                                                                                               |
| `-c`                 | `--column`         | `COLUMN NAME`    |            | Select which column of the project to use. Can only be used with `--gh`.                                                                                                                                                                 |
|                      | `--create-columns` |                  |            | Prompt to create non-existant columns specified with `--columns`.                                                                                                                                                                        |
| `-d` (as in **d**ye) | `--color`          | `COLOR`          |            | Chooses which color to use for Google Keep cards. Cannot be used with `--gh`. `COLOR` can be one of: `bl[ue]`, `br[own]`, `d[arkblue]`, `gra[y]`, `gre[en]`, `o[range]`, `pi[nk]`, `pu[rple]`, `r[ed]`, `t[eal]`, `w[hite]`, `y[ellow]`, |
| `-t`                 | `--tag`            | `TAG NAME`       | yes        | Adds tags to the Google Keep card. Cannot be used with `--gh`.                                                                                                                                                                           |
|                      | `--create-tags`    |                  |            | Prompt to create non-existant tags specified with `--tag`.                                                                                                                                                                               |
| `-?`                 | `--prompt-mode`    |                  |            | Prompts you for the above options when they are not provided.                                                                                                                                                                            |
