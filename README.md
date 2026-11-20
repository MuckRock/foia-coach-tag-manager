# FOIA Coach Tag Manager

FOIA Coach is a suite of tools that helps journalists file better public records requests.

[Please see the Add-On documentation](https://github.com/MuckRock/documentcloud-hello-world-addon/wiki/)

## Tag manager

This is a DocumentCloud Add-On that manages tags related to FOIA Coach.

This sets how documents in the "Moss – <State>" DocumentCloud projects are tagged, so an
importer can tell what each document is without guesswork. It's based on the tags already in
use across the Moss projects (listed in `scripts/moss_inventory.py`). Why it's needed is in [`README.md`](README.md#what-foia-coach-has-now).
`python scripts/moss_inventory.py --check` reports documents that don't follow it.

## Rules

1. **Each document has exactly one `Type` value**, taken from the list below. Spelling and
   capitalization must match exactly, in the singular.
2. **`Type` is the only key the importer reads for classification.** Other keys, such as `_tag`,
   `Tags` or `name`, can stay. They're ignored, so there's no need to remove them.
3. **Some keys have an agreed meaning** when they're used. See [Optional keys](#optional-keys).
4. **A project holds one jurisdiction.** The project, not a tag, says which state the documents
   belong to. A document that applies to several states goes in each state's project.
5. **Projects can hold documents that aren't indexed.** The importer picks documents by `Type`,
   so anything else in a project is simply left out. Documents don't need to be removed, and
   shouldn't be. Connecticut's request template, for example, can stay tagged `Other`.

## `Type` values

| `Type`                   | Use for                                                                                                                      | Not for                                                     | Replaces these values in use today                                    |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------- |
| `Retention Schedule`     | Retention and disposition schedules: general schedules, agency-specific schedules, RDAs, email retention policies            | Records management manuals that contain no schedule entries | "Retention Schedules"                                                 |
| `Guide`                  | Explainers about the jurisdiction's records law: NFOIC chapter guides, RCFP, AG or ombudsman handbooks, FAQs, training decks | Court decisions or opinions                                 | "Guides"                                                              |
| `Court Opinion`          | Decisions by a court                                                                                                         | Decisions by an AG, commission or counselor                 | "Court", "Court Opinions", "Court Cases"                              |
| `Administrative Opinion` | Opinions and decisions by an attorney general, FOI commission, public access counselor or similar office                     | Agency responses to a single request                        | "AG Opinion"; Connecticut FOI Commission decisions now tagged "Other" |
| `Records Log`            | An agency's own log of records requests it received                                                                          | A single request and its response                           | "Public Records Logs", "FOIA Logs"; Tennessee's 17 untagged logs      |
| `Request`                | A real request and, if available, the agency's response                                                                      | Templates or sample language                                | "Successful Request", "Agency Response"                               |
| `Other`                  | Anything that fits none of the above. Never indexed.                                                                         |                                                             |                                                                       |

Whether `Court Opinion`, `Administrative Opinion`, `Records Log` and `Request` documents get
indexed is still undecided. Logs and requests may come through the MuckRock MCP instead. Tagging
them now costs little and keeps both options open.

## Optional keys

Any key may be present. These have an agreed meaning when used:

| Key           | Value                                                                                                                                                                   | Why                                                                                  |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `name`        | The source filename, e.g. `RDA_35789_Agency Compliance Documentation.pdf`                                                                                               | Already used in Tennessee and New Jersey. Lets a document be traced to its download. |
| `Source URL`  | The web page the document came from                                                                                                                                     | Lets an update job check for newer versions. Most useful for guides and schedules.   |
| `Entity Type` | For local schedules, the kinds of agency covered, one value each: `County`, `Municipal`, `Law Enforcement`, `School District`, `Court`, `Special District`, `All Local` | Lets search filter "what does a sheriff's office keep?" Value list to be agreed.     |

Keys are case-sensitive. DocumentCloud data values are lists, so `Entity Type` can hold several
values. `Type` must hold one.

## What the importer can rely on

- A document is imported as a schedule if `Type == ["Retention Schedule"]`, and as a guide if
  `Type == ["Guide"]`. No fallbacks for variants.
- A document whose `Type` is `Other`, or is a type not yet indexed, is skipped quietly.
- A document with a missing or unknown `Type`, or more than one value, is skipped and reported,
  never guessed.
- Every other key, and every other document in the project, is ignored.
- The jurisdiction comes from the project.

## Applying it

`moss_inventory.py --check` reports 365 documents whose `Type` needs to change: 311 in the
main projects and 54 in Colorado's older second project (see below). Nothing has to be removed.

| Project           | Docs | Changes                                                                                                                                                                                                                                                                                                                                                                                             |
| ----------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Colorado          | 49   | 25 "Retention Schedules" → `Retention Schedule`; 24 court documents tagged only `_tag: Court` get `Type: Court Opinion`                                                                                                                                                                                                                                                                             |
| Colorado (224857) | 3    | The older "Project Moss – Colorado". Its other 54 documents are byte-for-byte copies (same file hash) of documents in 224931. Three exist only here, untagged: Schedule 45 Governing Body Records, Schedule 55 Information Technology and Communication Systems Records, Schedule No. 9 Historical Records. Tag them `Retention Schedule`, or add them to 224931 when the projects are consolidated |
| Georgia           | 12   | "Court" → `Court Opinion`                                                                                                                                                                                                                                                                                                                                                                           |
| Tennessee         | 95   | 39 "Court" → `Court Opinion`; 33 "AG Opinion" → `Administrative Opinion`; 6 "Agency Response" → `Request`; 17 untagged logs get `Records Log`                                                                                                                                                                                                                                                       |
| Indiana           | 116  | 69 "Retention Schedules" → `Retention Schedule`; 29 "Public Records Logs" → `Records Log`; 15 "Court" → `Court Opinion`; 3 "Guides" → `Guide`                                                                                                                                                                                                                                                       |
| DC                | 9    | "Court" → `Court Opinion`                                                                                                                                                                                                                                                                                                                                                                           |
| Connecticut       | 23   | 12 "Court Opinions" → `Court Opinion`; 10 "Successful Request" → `Request`; 1 "FOIA Logs" → `Records Log`                                                                                                                                                                                                                                                                                           |
| New Jersey        | 7    | 7 court documents tagged only `_tag: Court Cases` get `Type: Court Opinion`                                                                                                                                                                                                                                                                                                                         |

All of these are mechanical renames, so a script can do them. Optionally, Connecticut's two FOI
Commission decisions could move from `Other` to `Administrative Opinion`; as `Other` they're
valid but not indexed. Run `--check` again afterwards to confirm nothing's left.

## Points to settle in review

1. **One `Administrative Opinion` type, or separate ones** for AG opinions, commission decisions
   and counselor opinions? Separate types would let search treat binding decisions differently
   from advisory ones.
2. **Email retention policies** (93 of Colorado's 146 schedule documents, one per legislator or
   office): keep them as `Retention Schedule`, or give them their own type? They answer "how long does this office
   keep email?" but aren't schedules in the formal sense.
3. **Should `Source URL` and `Entity Type` be required** for new documents, even if they're
   optional for the ones already uploaded?
4. **The `Entity Type` value list.** The list above is a starting point taken from the state
   surveys. It should probably line up with MuckRock's agency types.
5. **Guides indexed from HTML.** If a guide is crawled from the web, does a PDF copy still go in
   the project? A PDF snapshot is useful as a fallback, but it can then be confused with the live
   page.
