# AGENTS.md

## Project state

This add-on enforces the FOIA Coach tag standard described in `README.md`: each document gets exactly one `Type` value. `tags.py` holds the standard and the pure resolver (no API calls); `main.py` is the add-on that reports and, with `apply`, writes the `Type` key. Applying types with an LLM, for documents the resolver can't map, is planned but not built. Add-On docs: https://github.com/MuckRock/documentcloud-hello-world-addon/wiki/

## How a DocumentCloud Add-On works

- **`main.py`** defines a subclass of `documentcloud.addon.AddOn` (from `python-documentcloud`) and calls `.main()` on it. The base class handles argument parsing, authentication, and provides:
  - `self.data` — the user's form input, keyed by the property names in `config.yaml`
  - `self.get_documents()` — iterates the documents the add-on was run against (selected docs or a search query)
  - `self.client` — an authenticated DocumentCloud API client (set a custom `User-Agent` on `self.client.session.headers`)
  - `self.set_message()`, `self.upload_file()`, `self.send_mail()` — report progress/results back to the DocumentCloud UI and user
- **`config.yaml`** is a JSON Schema (written as YAML) that DocumentCloud renders as the add-on's activation form. `properties` define form fields; `documents` controls whether the add-on accepts `selected` documents and/or a `query`; `categories` must be from: premium, ai, export, bulk, file, monitor, statistical, extraction. `config.example.yaml` is a fully annotated reference showing all supported options (events/scheduling, enums, defaults, etc.).
- **Execution happens in GitHub Actions**, not on a server:
  - `.github/workflows/run-addon.yml` — triggered by `repository_dispatch` when a user runs the add-on in DocumentCloud; delegates to `MuckRock/documentcloud-addon-workflows` (v2), which installs `requirements.txt` and runs `main.py`.
  - `.github/workflows/update-config.yml` — on push to `main` touching `config.yaml`, syncs the form definition to DocumentCloud. So changes to `config.yaml` on `main` go live immediately.

## Development

Dependencies are managed with `uv` (`pyproject.toml` + `uv.lock`, Python 3.13 to match the shared workflow). The GitHub Actions workflow does **not** use uv — it runs `pip install -r requirements.txt` — so `requirements.txt` is a generated file that must be committed and kept in sync with the lockfile:

```bash
uv sync                                  # install into .venv
uv add <package>                         # add a dependency (updates pyproject.toml + uv.lock)
uv export --format requirements-txt --no-hashes --no-header --no-annotate -o requirements.txt   # regenerate after any dependency change
```

There is no test suite or linter configured. Add-ons can be run locally against real DocumentCloud data; credentials come from `DC_USERNAME`/`DC_PASSWORD` (or `--username`/`--password`):

```bash
uv run python main.py --documents <doc_id> [<doc_id> ...] --data '{"name": "test"}'
uv run python main.py --query "<search query>" --data '{...}'
```

## Code comments

Comments say **why**, not what. If the code already says it, delete the comment.

- **One or two short sentences.** If it needs a paragraph, it belongs in a
  doc comment, the PR description, or a doc under `docs/`.
- **Keep the consequence, drop the lead-in.** The clause naming what the
  code does is the half to cut; the clause saying what breaks otherwise is
  the half worth keeping.
- **Never describe code that is not there.** No "this used to...", no
  narrating the change, no explaining why something was removed. `git log`
  and the PR hold that.
- **No reasoning out loud.** Don't walk through scenarios, anticipate
  objections, or record the thought process behind a choice.
- **Do comment the surprising**: a constraint an external system imposes,
  an ordering requirement, a failure that cannot be seen locally. That is
  what a reader cannot get from the code.

```typescript
// Good - a constraint you cannot see from here
// The API rejects a redaction whose page range crosses a document split.

// Bad - narrates the change
// `currentPage` is now derived from the store instead of a prop, so
// this component no longer needs to read it from context.
```

## Docstrings / doc comments

One line on what it does. Add more only for a contract a caller needs: what it rejects/throws, what it returns in the edge case, ordering it requires, side effects it has, a cost worth avoiding.

Two tests before you keep a second paragraph:

- Does it restate the first line in more words? Delete it.
- Would a caller behave differently for knowing it? Keep it, in one or two sentences.

```typescript
// Good - the whole contract, one line
/** Does the document still have pages pending OCR? */

// Good - a second paragraph a caller acts on
/**
 * The document's current processing status, or "error" if any page failed.
 *
 * Read from the cached store value; the document list renders one row
 * per document and cannot afford an API call each.
 */
```

## Pull request descriptions

Open with one sentence on what changes. Then:

- **Behaviour changes** — name them, or say "none".
- **Migrations** — what they do, whether they reverse.
- **What to check** — the QA steps, as a checklist.

Bullets, not prose. Don't recount how the change came about or what was tried first.

## Tests

Name the behaviour, not the mechanism: `renders the error state when OCR fails`, not `test handle error`. A test whose assertion would pass against the unfixed code is not a test.
