from pathlib import Path

names = dict()

content = Path("./callgraph.dot").read_text("utf-8")

for mapping_line in filter(lambda s: s.startswith("// "), content.splitlines()):
    ident, rest = mapping_line.removeprefix("// ").split(":")
    module, rest = rest.split("(")
    module = module.removesuffix(".py")
    function = rest.split("/")[-1].removeprefix("ideaseed.").removesuffix(")")
    names[ident] = module + "." + function

for ident, name in names.items():
    content = content.replace(f"\t{ident} ->", f'\t"{name}" ->')
    content = content.replace(f" {ident};", f' "{name}";')

for line in content.splitlines():
    if 'cli.run" ->' in line or "utils." in line:
        content = content.replace(line, "")

print(content)
