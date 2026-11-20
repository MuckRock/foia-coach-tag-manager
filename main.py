"""Standardize the `Type` tag on FOIA Coach source documents in DocumentCloud."""

import collections
import csv

from documentcloud.addon import AddOn

from tags import TYPE_KEY, UNRESOLVED, resolve

REPORT = "tag-report.csv"


class TagManager(AddOn):
    def main(self):
        self.client.session.headers.update(
            {"User-Agent": "FOIA Coach Tag Manager (MuckRock DocumentCloud Add-On)"}
        )
        apply = self.data.get("apply", False)
        default = self.data.get("untagged_type") or None

        self.set_message("Checking tags…")
        counts = collections.Counter()
        with open(REPORT, "w+", newline="") as report:
            writer = csv.writer(report)
            writer.writerow(
                ["id", "title", "url", "status", "current Type", "new Type", "note"]
            )
            for doc in self.get_documents():
                result = resolve(doc.data, default)
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
        changed = sum(n for s, n in counts.items() if s not in ("ok", UNRESOLVED))
        verb = "Updated" if apply else "Would update"
        self.set_message(f"{verb} {changed} documents ({summary}). See {REPORT}.")

    def set_type(self, doc_id, value):
        """Replace only the `Type` key, leaving the document's other data untouched."""
        self.client.put(
            f"documents/{doc_id}/data/{TYPE_KEY}/", json={"values": [value]}
        )


if __name__ == "__main__":
    TagManager().main()
