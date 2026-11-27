---
name: merge
description: >-
  Merge the user's requested changes in the nauta-monitor project. Invoke only
  when the user has explicitly requested merging, such as choosing Merge
  Change, invoking /merge, or asking to land the changes. Do not invoke for
  review, preparation, passing checks, or skill installation alone.
disable-model-invocation: true
metadata:
  delta-action: land
---

# Merge changes in nauta-monitor

Use this workflow only for an explicit merge request. The request that invoked
this skill is authorization to carry out the merge; do not ask whether the user
wants to merge or wait for another confirmation of that same request.

## Prepare safely

1. Confirm the repository is nauta-monitor and inspect the current branch,
   remotes, status, and the requested change's scope. The normal destination is
   `master` on `origin`, but check the current remote and repository settings
   rather than relying on stale local configuration.
2. Review the contribution guidance in `docs/contributing.md`. It calls for
   a feature branch, applicable tests, descriptive commit messages, and a pull
   request. No signing, contributor agreement, mandatory changelog entry, or
   human-authored submission text requirement is specified there; do not invent
   one. Update documentation or changelog when appropriate to the change.
3. Preserve unrelated work. Inspect all uncommitted changes before staging;
   include only changes in the requested scope. Never discard, overwrite, or
   silently commit unrelated changes. If the requested changes cannot be
   isolated safely, stop and explain the blocker.
4. If needed, create a feature branch from the appropriate current base and
   prepare descriptive, non-interactive commits. Do not start an interactive
   editor or interactive rebase. Publish the branch to `origin` only as needed
   to create/update the pull request.

## Verify and merge

1. For code changes, install the project's development dependencies if needed
   and run `python -m pytest -v` from the repository root. The project declares
   pytest in its `dev` extra and this invocation is documented in
   `docs/contributing.md`.
2. If documentation changes affect the MkDocs site, run `mkdocs build`. The
   documentation workflow in `.github/workflows/docs.yml` installs MkDocs and
   MkDocs Material and invokes this exact build command. Do not claim it passed
   if the required tool/dependencies are unavailable.
3. Create or update a pull request targeting the verified destination branch.
   Check the repository's current rules, required reviews, and required status
   checks. Wait for applicable reviews and every required check to pass for the
   exact PR changes being merged. Pending, failing, missing, or unverifiable
   required checks are blockers; never bypass them.
4. If conflicts arise, resolve them automatically only when the intended result
   is clear and unrelated work remains safe. Otherwise stop and ask the user to
   decide. Re-run applicable local verification and ensure remote required
   checks pass on the updated PR changes.
5. Merge the PR using the repository's currently allowed and configured
   strategy through the authenticated GitHub CLI when available. Do not assume
   a merge, squash, or rebase strategy; do not force-push or bypass rules. If
   the CLI is unavailable or the required operation cannot be performed safely,
   stop and report the blocker rather than claiming completion.
6. Verify that the PR is merged and its resulting change is present on the
   intended destination branch. If this cannot be verified, report that the
   changes have not been confirmed merged.
