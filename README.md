# FOIA Coach Tag Manager

FOIA Coach is a suite of tools that helps journalists file better public records requests.

This DocumentCloud Add-On standardizes how documents in the "Moss – <State>" projects are
tagged, so the FOIA Coach importer can tell what each document is without guesswork. Later it
will also suggest tags for documents it can't classify, using an LLM.

## Using the Add-On

Run it on selected documents or a search, e.g. `+project:225303` for a whole project.

1. Run it with **Apply changes** unchecked. Nothing changes; you get `tag-report.csv`
   with each document's current and new `Type`.
2. Check the report, then run it again with **Apply changes** checked.

For each document it does one of:

| Status       | Meaning                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------- |
| `ok`         | `Type` already follows the standard.                                                        |
| `rename`     | `Type` uses an old spelling, e.g. "Retention Schedules", and is renamed.                     |
| `from hint`  | No `Type`, but `_tag` or `Tags` values all map to one standard value.                        |
| `defaulted`  | No `Type`, `_tag` or `Tags`, and you set **Type for untagged documents**.                   |
| `email policy` | A retention schedule whose text reads as an email retention policy. Needs **Find email retention policies**. |
| `unresolved` | An unknown value, or values that disagree. Reported, never guessed. Fix these by hand.      |

Only the `Type` key is written. Other keys are left alone.

**Find email retention policies** reads each schedule's text and retags it
`Email Retention Policy` if it reads as one: no "Retention Schedule" or "Records Management
Manual" heading near the start, and a mention of email or Colorado's email statute
(24-72-204.5, SB 23-286) in the opening. It's the same test the FOIA Coach importers use, and
it's slower because it fetches every schedule's text. A schedule with no text yet comes back
`unresolved`.

**Type for untagged documents** applies to every untagged document in the run, so select only
documents you know are that type, such as a batch of untagged records logs.

### Running locally

```bash
uv sync
uv run python main.py --query "+project:225303" --data '{}'
uv run python main.py --query "+project:225303" --data '{"apply": true}'
```

Credentials come from `DC_USERNAME` and `DC_PASSWORD`. Locally the report is written to
`tag-report.csv` instead of being uploaded.

## The tag standard

### Rules

1. **Each document has exactly one `Type` value**, taken from the list below. Spelling and
   capitalization must match exactly, in the singular.
2. **`Type` is the only key the importer reads for classification.** Other keys, such as `_tag`,
   `Tags` or `name`, can stay. They're ignored, so there's no need to remove them.
3. **Some keys have an agreed meaning** when they're used. See [Optional keys](#optional-keys).
4. **A project holds one jurisdiction.** The project, not a tag, says which state the documents
   belong to. A document that applies to several states goes in each state's project.
5. **Projects can hold documents that aren't indexed.** The importer picks documents by `Type`,
   so anything else in a project is simply left out. Documents don't need to be removed, and
   shouldn't be.

### `Type` values

| `Type`                   | Use for                                                                                                                      | Not for                                                     | Replaces                                       |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------- |
| `Retention Schedule`     | Retention and disposition schedules: general schedules, agency-specific schedules, RDAs                                      | Records management manuals that contain no schedule entries | "Retention Schedules"                          |
| `Email Retention Policy` | An office's policy on how long it keeps email, e.g. one per legislator or legislative office                                  | Schedules that cover email among other records              |                                                |
| `Guide`                  | Explainers about the jurisdiction's records law: NFOIC chapter guides, RCFP, AG or ombudsman handbooks, FAQs, training decks | Court decisions or opinions                                 | "Guides"                                       |
| `Court Opinion`          | Decisions by a court                                                                                                         | Decisions by an AG, commission or counselor                 | "Court", "Court Opinions", "Court Cases"       |
| `Administrative Opinion` | Opinions and decisions by an attorney general, FOI commission, public access counselor or similar office                     | Agency responses to a single request                        | "AG Opinion"                                   |
| `Records Log`            | An agency's own log of records requests it received                                                                          | A single request and its response                           | "Public Records Logs", "FOIA Logs"             |
| `Request`                | A real request and, if available, the agency's response                                                                      | Templates or sample language                                | "Successful Request", "Agency Response"        |
| `Other`                  | Anything that fits none of the above. Never indexed.                                                                         |                                                             |                                                |

The values in "Replaces" are renamed automatically. Email retention policies are currently
tagged as schedules; run with **Find email retention policies** to retag them.

`Administrative Opinion` covers binding and advisory opinions alike.

Whether `Court Opinion`, `Administrative Opinion`, `Records Log` and `Request` documents get
indexed is still undecided. Logs and requests may come through the MuckRock MCP instead.

### Optional keys

Any key may be present. These have an agreed meaning when used. None are required, including
for new documents.

| Key           | Value                                                                                                                                                                   | Why                                                                              |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `name`        | The source filename, e.g. `RDA_35789_Agency Compliance Documentation.pdf`                                                                                               | Lets a document be traced to its download.                                       |
| `Source URL`  | The web page the document came from                                                                                                                                     | Lets an update job check for newer versions. Most useful for guides and schedules. |
| `Entity Type` | For local schedules, the kinds of agency covered, one value each: `County`, `Municipal`, `Law Enforcement`, `School District`, `Court`, `Special District`, `All Local` | Lets search filter "what does a sheriff's office keep?"                          |

Keys are case-sensitive. DocumentCloud data values are lists, so `Entity Type` can hold several
values. `Type` must hold one.

The `Entity Type` value list is a starting point taken from the state surveys and isn't settled.
It should probably line up with MuckRock's agency types.

### What the importer can rely on

- A document is imported as a schedule if `Type == ["Retention Schedule"]`, and as a guide if
  `Type == ["Guide"]`. No fallbacks for variants.
- A document whose `Type` is `Other`, or is a type not yet indexed, is skipped quietly.
- A document with a missing or unknown `Type`, or more than one value, is skipped and reported,
  never guessed.
- Every other key, and every other document in the project, is ignored.
- The jurisdiction comes from the project.

## Add-On documentation

See the [DocumentCloud Add-On wiki](https://github.com/MuckRock/documentcloud-hello-world-addon/wiki/).
