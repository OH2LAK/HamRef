# Repo cleanup notes (decisions for Erik)

## License proposal
- Hardware (`hardware/`): CERN-OHL-S-2.0 (strongly reciprocal) or CERN-OHL-W-2.0 (weakly reciprocal).
- Firmware (`firmware/`): MIT (permissive) or GPL-3.0-or-later (keeps derivatives open).
- Docs/images: CC BY-SA 4.0.
No LICENSE files were added because this choice is yours.

## Datasheets in `docs/datasheets/`
Vendor datasheets (u-blox, Raspberry Pi, Fischer, Waveshare) are copyrighted. Redistribution in a public repo is usually not allowed. Suggested: remove them from git (`git rm --cached`), add `docs/datasheets/` to `.gitignore`, and list download links in `docs/datasheets/README.md`.
Also check the STEP/schematic files from Waveshare and the enclosure PDF.

## Other
- Author field is "Erik, OH2LAK" only. Git log shows your personal gmail address as commit author; check `git config user.email` if you do not want that public.
- `docs/architecture-and-plan.md` is in Finnish; the README links to it with a TODO.
