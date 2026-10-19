# Coureur packages

Skills, tools and blueprints for [WildSon Coureur](https://github.com/cjvigue-cmd/Coureur), each a folder with a manifest and a check. Nothing here is taken on its say-so: Coureur imports a package only after its check has run.

```sh
coureur --skills    import https://github.com/cjvigue-cmd/coureur-packages.git
coureur --tools     import https://github.com/cjvigue-cmd/coureur-packages.git
coureur --blueprint import https://github.com/cjvigue-cmd/coureur-packages.git
```

Each command finds the packages of its kind anywhere in the repo (a shallow clone, removed after), checks every one, and stores the ones that pass. The console has the same under System → Settings → Packages, where a stored package is switched on, tried, trained or removed.

## The three kinds

| Kind | Folder | Manifest | What's beside it | The check that decides |
|---|---|---|---|---|
| **Skill** | `skills/<name>/` | `SKILL.md`: front matter `name` + `description`, then the instructions | `scripts/`, `references/`, `assets/`; optional `cases/*.json` | The manifest's rules (a name of lowercase letters, digits and single hyphens that matches the folder; a description; instructions; a body under 500 lines). On = Claude Code loads it from its own skills folder; another Conductor gets the text in its system prompt. |
| **Tool** | `tools/<name>/` | `TOOL.md`: front matter (`name`, `description`, `requires:` modules, `network: no`), then notes on when to use it | `tool.py` or `tool.mjs` (reads `input.json`, prints the result), optional `schema.json`, `examples/*.json` | Every example runs in Coureur's sandbox; the printed output must match. A tool with no examples is a draft. Served = on the Conductor's MCP tool list, every call run the same way. |
| **Blueprint** | `blueprints/<name>/` | `BLUEPRINT.md`: front matter, then notes | `blueprint.json` (the gate recipe), `cases.json` (`inputs`, `good`, `bad`) | The real gate on the empty answer, every good one and every bad one: stored only when the empty and bad answers fail and the good ones pass. Enabled = usable by name like a built-in. |

### Training a skill

A skill's `cases/*.json` are tasks it should make a seat good at, each with the gate that decides it — the same fields `execute_task` takes:

```json
{ "prompt": "Write add(a, b) returning the sum.", "task_type": "python", "tests": "import unittest\n..." }
```

`coureur --skills train NAME` runs every case through the Local seat with the skill's instructions and gates each answer. The pass rate is the skill's scorecard. Change the skill, train again, and the scorecard says whether it helped.

### What you trust when you import

Passing a check is not a review. A tool that passes its examples is still code you imported, and a skill is text a model will follow. What bounds a tool: Coureur runs it in the gates' sandbox — no network, reads only its own folder and the system folders, writes only its own folder, a memory limit, a process cap and a timeout — with a scrubbed environment (no API keys reach it), and only when a Conductor calls it. What a tool must say in `TOOL.md`: `requires:` the interpreter modules it imports (each is imported once in the sandbox before the examples run; a missing one fails the import) and `network: no` (the only value a tool can keep; a tool that says `yes` is refused). Read a package before you enable it. A package from a stranger is a stranger's code, and this repo's maintainers review what they merge, not what you import from elsewhere.

### A tool's contract

The script reads `input.json` from the folder it runs in, prints its result to stdout (JSON when it can) and exits 0. Each example is `{"input": {...}, "expect": {...}}` (the printed JSON must equal it) or `{"input": {...}, "expect_contains": "text"}`.

### A blueprint's cases

```json
{ "inputs": { "word": "HELLO" }, "good": ["HELLO WORLD\n"], "bad": ["hello world\n", "WORLD\n"] }
```

Any string may be `{"file": "path"}`, read relative to the package folder. A gate is only as good as what it rejects, so a package needs at least one bad answer.

## Contributing

Open a pull request with a package folder of one of the three kinds. It is taken when its check passes on import, which you can run yourself:

```sh
coureur --skills    check skills/<name>
coureur --tools     check tools/<name>
coureur --blueprint test blueprints/<name>/blueprint.json blueprints/<name>/cases.json
```

## License

MIT OR Apache-2.0, at your option.
