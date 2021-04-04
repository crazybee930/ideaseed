from typing import Iterable, NamedTuple, Optional

from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import CodeBlock, Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from ideaseed.utils import readable_on

ABOUT_SCREEN = """


                ██████████  ██  ██
                ██      ██  ██  ██
                ██████████  ██  ██
                ██      ██  ██  ██
                ██████████████████
                ██      ██      ██
                ██████████      ██
                ██      ██      ██
                ██████████      ██
      
            ideaseed v{version}
            by Ewen Le Bihan
            more at https://ewen.works
      
                ~ thx to these ppl ~

https://github.com/kiwiz
    This madman reverse-engineered Google Keep's
    internal REST API so that anyone could 
    use it with ease.
                    
https://github.com/PyGithub
    This one of the cleanest libs I've ever used.
    Like `requests`-level cleanliness.
                    
https://github.com/docopt
    Designing CLIs with this is a fucking breeze.
    I can almost copy-paste documentation into
    a docstring and call it a day, it's crazy.
"""


# Remove ugly frames around markdown code blocks
# see https://github.com/willmcgugan/rich/issues/264
class FramelessCodeBlock(CodeBlock):
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        code = str(self.text).rstrip()
        syntax = Padding(Syntax(code, self.lexer_name, theme=self.theme), pad=(1, 4))
        yield syntax

Markdown.elements["code_block"] = FramelessCodeBlock


class Label(NamedTuple):
    name: str
    color: str = "default"
    url: Optional[str] = None

    def __str__(self) -> str:
        s = f"[#{readable_on(self.color)} on #{self.color}]{self.name}[/]"
        if self.url:
            s = href(s, self.url)
        return s


def href(s: str, url: str) -> str:
    return f"[link {url}]{s}[/link {url}]"


def make_card(
    title: str,
    right_of_title: str,
    description: str,
    labels: list[Label],
    card_title: str,
    card_style: str = "default",
) -> Panel:
    header = Table.grid(expand=True)
    header.add_column()
    header.add_column(justify="right")
    header.add_row(f"[bold]{title}", f"[bold blue]{right_of_title}")

    card = Table.grid(padding=1, expand=True)
    card.add_column()
    card.add_row(header)
    card.add_row(Markdown(description))

    if labels:
        label_row = Table.grid(expand=True)
        label_row.add_column(justify="right")
        label_row.add_row(", ".join(map(str, labels)))
        card.add_row(label_row)

    return Panel(card, title=card_title, style=card_style)


def make_listing(
    milestone: Optional[str] = None,
    assignees: Optional[Iterable[str]] = None,
    project: Optional[str] = None,
    project_column: Optional[str] = None,
    url: Optional[str] = None,
) -> Table:
    listing = Table.grid(expand=True, padding=0)
    listing.add_column()
    listing.add_column(justify="right")
    if project:
        listing.add_row(
            "Card in", f"[bold blue]{project}[/] [bold dim]>[/] [blue]{project_column}"
        )
    if milestone:
        listing.add_row("Milestone'd to", f"[bold blue]{milestone}[/]")
    if assignees:
        listing.add_row(
            "Assigned to",
            ", ".join(
                f"[bold dim]@[/][bold blue]{name}[/]" for name in assignees
            ),
        )

    if url:
        listing.add_row("Available at", f"[blue link {url}]{url}")

    return listing


def show(
    title: str,
    right_of_title: str,
    description: str,
    labels: list[Label],
    card_title: str,
    card_style: str = "default",
    milestone: Optional[str] = None,
    assignees: Optional[Iterable[str]] = None,
    project: Optional[str] = None,
    project_column: Optional[str] = None,
    url: Optional[str] = None,
):
    c = Console()
    c.print(
        make_card(
            title=title,
            right_of_title=right_of_title,
            description=description,
            labels=labels,
            card_title=card_title,
            card_style=card_style,
        )
    )
    c.print()
    c.print(
        make_listing(
            milestone=milestone,
            assignees=assignees,
            project=project,
            project_column=project_column,
            url=url,
        )
    )


if __name__ == "__main__":
    show(
        title="lsd cannot follow windows symlinks",
        right_of_title="#499",
        description=r"""
I've tried a few and stumbled upon a more general solution that supports multiple languages and multiple types of graphs, called [depends](https://github.com/multilang-depends/depends).

It does something weird with its DOT format generation, it puts node names (so actual functions) in some weird format in _comments_ atop the `digraph` and only uses numbers in the actually shown content. I patched together a small python script that fixes the DOT file to actually show the functions' names, and it works well.

```python
from pathlib import Path
names = dict()

content = Path('PUT YOUR FILE'S PATH HERE').read_text('utf-8')

for mapping_line in filter(lambda s: s.startswith('// '), content.splitlines()):
    ident, rest = mapping_line.removeprefix('// ').split(':')
    module, rest = rest.split('(')
    module = module.removesuffix('.py')
    function = rest.split('/')[-1].removeprefix('ideaseed.').removesuffix(')')
    names[ident] = module + "." + function

for ident, name in names.items():
    content = content.replace(f"\t{ident} ->", f"\t\"{name}\" ->")
    content = content.replace(f" {ident};", f" \"{name}\";")

for line in content.splitlines():
    if 'cli.run" ->' in line or 'utils.' in line:
        content = content.replace(line, "")

print(content)
```

just putting this out here in case an internet stranger stumbles upon this issue.""",
        labels=[
            Label(name="help wanted", color="00E6C4"),
            Label(name="kind/enhancement", color="A0EEEE"),
            Label(
                name="os/windows",
                color="CE8D4C",
                url="https://github.com/anishathalye/dotbot/labels/enhancement",
            ),
        ],
        card_title=href("Peltoche/lsd", "https://github.com/Peltoche/lsd"),
        milestone="1.6.3",
        assignees=(href("meain", "https://github.com/meain"), "Peltoche"),
        project="Backlog",
        project_column="work in progress",
        url="https://github.com/Peltoche/lsd/issues/499",
    )
