# Comments and tracked changes

## Tracked replacement

Run `scripts/edit.py replace input.docx tracked.docx "old phrase" "new phrase" --author "Name"`. The phrase must occur exactly once in body/table paragraphs. Existing unaffected runs keep their formatting; the inserted phrase inherits the first matched run's formatting. An empty replacement performs a tracked deletion. Author and timestamp are recorded on the insertion/deletion.

The helper deliberately fails rather than guessing when the target contains bookmarks, hyperlinks, fields, images, tabs, existing revisions or other complex markup. A rejection leaves the requested output unpublished. For several edits, chain separate new output files; check each phrase is still unique. Do not use a global string replacement on ZIP/XML bytes.

Verify that Word's **All Markup** view shows the intended deletion and insertion under the requested author. The structural validator cannot establish that every intended change is tracked; compare the original and accepted result, and inspect the actual `w:ins`/`w:del` entries if necessary.

## Comments

Run `scripts/edit.py comment input.docx annotated.docx "target phrase" "comment text" --author "Name"`. It splits only boundary runs and uses python-docx's comment API so the comment is anchored to the exact phrase. This supports ordinary comments, not threaded replies/resolution state. Verify the selected phrase and comment in Word; comments may not be included in a PDF export.

For programmatically selected runs in more complex paragraphs, use `Document.add_comment(runs, text=..., author=...)` directly and inspect the anchor range. Do not hand-create the cross-linked comment parts when the library already does it.

## Accept revisions

Run `scripts/edit.py accept tracked.docx clean.docx`. It accepts body/table inline insertions/deletions and property revisions. Deletion of a paragraph mark joins its adjacent paragraph rather than leaving a blank bullet. The helper refuses tracked row/cell changes, move revisions, paragraph-insertion marks and revisions in headers/footers; use Word's **Accept All Changes** for these cases after approval.

This is a bounded revision processor, not a universal Word revision engine. Keep both tracked and clean versions. Compare accepted text against the intended result, verify styles around joined paragraphs, and render the clean copy. For contracts, never infer that removing markup is legal approval or that a clean PDF proves no untracked edits occurred.
