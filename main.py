"""Standardize the `Type` tag on FOIA Coach source documents in DocumentCloud."""

import collections
import csv

from documentcloud.addon import AddOn
from documentcloud.exceptions import DoesNotExistError

from tags import TYPE_KEY, DocType, Status, as_email_policy, resolve

REPORT = "tag-report.csv"


class TagManager(AddOn):
    def main(self):
        self.client.session.headers.update(
            {"User-Agent": "FOIA Coach Tag Manager (MuckRock DocumentCloud Add-On)"}
        )
        apply = self.data.get("apply", False)
        default = self.data.get("untagged_type")
        default = DocType(default) if default else None
        find_email = self.data.get("find_email_policies", False)

        self.set_message("Checking tags…")
        counts = collections.Counter()
        with open(REPORT, "w+", newline="") as report:
            writer = csv.writer(report)
            writer.writerow(
                ["id", "title", "url", "status", "current Type", "new Type", "note"]
            )
            for doc in self.get_documents():
                result = resolve(doc.data, default)
                if find_email and result.new == DocType.SCHEDULE:
                    result = as_email_policy(result, page_text(doc))
                counts[result.status] += 1
                if result.changes and apply:
                    self.set_type(doc.id, result.new)
                writer.writerow(
                    [
                        doc.id,
                        doc.title,
                        doc.canonical_url,
                        result.status,
                        "; ".join(result.current),
                        result.new or "",
                        result.reason,
                    ]
                )
            self.upload_file(report)

        summary = ", ".join(f"{n} {status}" for status, n in sorted(counts.items()))
        changed = sum(
            n for s, n in counts.items() if s not in (Status.OK, Status.UNRESOLVED)
        )
        verb = "Updated" if apply else "Would update"
        self.set_message(f"{verb} {changed} documents ({summary}). See {REPORT}.")

    def set_type(self, doc_id, value):
        """Replace only the `Type` key, leaving the document's other data untouched."""
        self.client.put(
            f"documents/{doc_id}/data/{TYPE_KEY}/", json={"values": [value]}
        )


def page_text(doc):
    """All of a document's page text, joined as the services importers join it; None if it has none."""
    try:
        pages = doc.get_json_text().get("pages", [])
    except DoesNotExistError:
        return None
    return "\n".join(p["contents"] for p in pages)


if __name__ == "__main__":
    TagManager().main()
