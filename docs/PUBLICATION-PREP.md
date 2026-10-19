# Publication preparation - 2026-10-19

## Scope and baseline

Starting commit: `c88b3e4`, branch `master`. Work prepared on `feat/publication-prep`. No visibility change, branch rename, Pages enablement, deployment, or history rewrite is part of this preparation.

Python environment: Python 3.14.7 via the Windows Python launcher; no repository virtual environment, dependency manifest, or third-party packages required.

Command: `py -3 -X utf8 -m unittest discover -s tests -v`

Baseline: **22 tests passed**. The initial restricted run discovered 22 tests but hit four temp-directory permission errors; rerunning with normal filesystem access passed all 22 without code changes.

## Secret and personal-data review

Gitleaks was unavailable. A fallback full-blob scan enumerated `git rev-list --objects --all`, selected every blob with `git cat-file -t`, and read every selected blob with `git cat-file blob`. Baseline: **3 reachable commits, 22 distinct blobs**. No secret candidates or historical `.env` files found. Rules covered provider token/key prefixes, private-key headers, credential assignments (secret/token/password/API/access keys), and credentials embedded in HTTP URLs. No matched secret values are printed. This is a heuristic scan, not proof that no secret exists; unreferenced/unreachable objects and provider-side revoked credentials are outside its scope.

Current tracked-file scan used `git ls-files -z` and inspected file contents for drive-root/user-profile paths, emails (allowlisting the owner's Hotmail address), and phone-like numbers. One real path was found in `docs/DEVELOPMENT-CHECKPOINT.md` and replaced with `./`, referring to this repository. No disallowed email addresses or phone numbers found; date strings were false-positive phone candidates. History is unchanged and still contains the old documentation path.

## Path regression

Added `test_tracked_files_have_no_absolute_local_paths`. It reads every Git-tracked file's working-tree bytes, including staged additions, and rejects absolute Windows drive paths and the local user-profile marker without printing matching content. First run failed at `docs/DEVELOPMENT-CHECKPOINT.md:7` before the path replacement. Post-fix suite: **23 tests passed**. Keep Git installed when running this guard, and stage new files before the final local check; CI checks the committed tree.

## Serving and Pages decision

No frontend framework or build tool: `atlas/static/index.html`, `app.js`, and `styles.css` are served by the standard-library `ThreadingHTTPServer` in `atlas/server.py`, started by `run.py`. `app.js` posts to `/api/run`; Python executes the SQLite simulation. The HTML also uses root-relative asset URLs.

The complete current case page cannot run on GitHub Pages without a server. A future dependency-free static export could precompute reports and change the UI to consume relative JSON, but that is a feature change beyond publication preparation. Therefore the conditional Pages workflow was not added. Any future Pages workflow must be marked **unverified until first Pages deploy**. Nothing was deployed.

## Prepared files and verification limits

MIT license, public-reader README with honest limits and related-project link, offline push/PR CI, tracked-file path guard, and evidence-mapped portfolio card draft. CI installs Python, checks out the repository, and runs standard-library unittest on Linux (Python 3.10 and 3.14) and Windows (3.14); it uses no configured secrets. The test execution is offline; Actions checkout and Python setup require network access.

Local results do not establish hosted CI success. Browser/visual QA, other Python/OS matrix combinations, Pages, and production behavior remain unverified. Prior validation documents retain their historical results.
