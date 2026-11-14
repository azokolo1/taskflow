# Learning Progress — TaskFlow

A running record of what I built, what broke, how I diagnosed it, and what I can now explain.
Newest phase at the top. Each entry follows the same template (see the bottom of this file).

---

## Current status

| Item | Status |
|---|---|
| Current phase | Phase 1 — Linux fundamentals (not started) |
| Last completed | Phase 0 — Repository foundation |
| Lab environment | WSL Ubuntu (systemd status: to be checked with `ps -p 1 -o comm=`) |
| AWS spend so far | £0 — nothing provisioned yet |

---

## Phase 0 — Repository foundation

**Date:** 13–14 Nov 2026
**Status:** ✅ Complete

### What I set out to do
Create a clean, professional repository structure for TaskFlow, with safety rails in place
*before* the first commit, so secrets can never reach Git.

### What I did myself
- Created the folder structure with `mkdir -p` and brace expansion.
- Wrote `.gitignore` covering secrets (`.env`, `*.pem`), Terraform state, Python caches and editor files.
- Wrote `.env.example` with placeholder values only.
- Added `.gitkeep` files so Git tracks empty folders.
- Added the architecture diagram to `docs/architecture/` and its generator to `scripts/`.
- Ran `git init -b main`, reviewed `git status`, made the first commit and pushed to GitHub.
- Verified `.env` is ignored and `.env.example` is tracked (`git check-ignore`, `git ls-files`).

### Problems I hit and how I diagnosed them

| Symptom | Cause | How I found it | Fix |
|---|---|---|---|
| Workflow files ended up as `.github/workflows/ci/yml`, with `cd.yml` in the root | A multi-path command where only the first path had the full prefix | Read the `tree` output carefully | Rebuilt the structure with every path written in full |
| `cp: cannot stat '/home/swift-tech/swift-tech/...'` | Wrote `~/swift-tech/...`, but `~` already means `/home/swift-tech` | Read the **expanded path in the error message**, not the one I typed | Used `~/file` instead |
| `mv: target 'docs/architecture/': No such file or directory` | Pasted a block of commands while in `~`, not `~/taskflow` | `pwd` printed `/home/swift-tech`, but the pasted commands kept running | `cd ~/taskflow` first, then re-ran |
| `.gitignore` test "passed" but tested nothing | Typo: tested `.env.exaple`, not `.env.example` | Reviewed the output: it was matching a file that doesn't exist | Re-ran with the correct name: exit code `1`, so not ignored ✔ |
| Extra `*:Zone.Identifier` files appeared | Windows adds a "downloaded from internet" marker; WSL shows it as a separate file | Spotted them in `ls` | Deleted them and added `*:Zone.Identifier` to `.gitignore` |

### Key lessons
1. **Check `pwd` before running relative paths.** Run it on its own and read the result, rather than pasting it inside a block.
2. **Read the path in the error message.** It shows exactly what the shell expanded.
3. **End a `mv`/`cp` destination with `/`.** It fails loudly if the folder doesn't exist, rather than silently renaming the file.
4. **A test with a typo can pass while proving nothing.** Check that the test targets the real thing.
5. **Safety rails go in before the first commit.** `.gitignore` before `git add`, and always read `git status` before committing.
6. GitHub Actions only runs `.yml`/`.yaml` files placed **directly** in `.github/workflows/`.
7. Git tracks files, not folders. Empty folders need a `.gitkeep`.

### What I can now explain (interview-ready)
- **Absolute vs relative paths:** `~/taskflow/scripts` is absolute, because the shell expands `~` to `/home/swift-tech`, so it works from anywhere. `scripts` is relative to the current folder, which is why my `mv` failed from `~`.
- **Why `.env.example` is committed but `.env` isn't:** the example documents which settings the app needs. The real file holds secrets that would be exposed to everyone with repo access and stay in Git history forever.
- **If a secret is pushed:** rotate it first, check CloudTrail/access logs for misuse, clean the history (`git filter-repo`), and prevent a repeat (GitHub push protection, a `gitleaks` pre-commit hook). Rotation is the real fix, because clones and forks may already have the secret.
- **`git rm --cached`:** removes a file from the next commit but keeps it on disk. Earlier commits still contain it.
- **`.terraform.lock.hcl` vs `terraform.tfstate`:** the lock file is code (it pins provider versions, so commit it). State is live data that contains secrets in plain text and needs locking, so it goes in S3 and never in Git.

### Unresolved questions
- [ ] NAT gateway vs VPC endpoints: which is cheaper for the TaskFlow lab, with real numbers?
- [ ] Does my WSL run systemd, or do I need EC2 for the service lessons?

### Evidence
- First commit: `cb7d627 chore: initialise repository structure and safety rails`
- `tree -aF -I .git` output and the `git check-ignore` result (screenshots to be added in `docs/architecture/`)
- Architecture diagram: [`docs/architecture/taskflow-architecture.png`](architecture/taskflow-architecture.png)

### Next milestone
Phase 1: Linux fundamentals — filesystem, permissions, processes and services on a lab machine.

---

## Template — copy this for each new lesson or phase

```markdown
## Phase N — <name>

**Date:**
**Status:** 🟡 In progress / ✅ Complete

### What I set out to do
<One or two sentences: the problem this phase solves.>

### What I did myself
- <Action, in past tense. Only list what you actually typed or decided.>

### Problems I hit and how I diagnosed them
| Symptom | Cause | How I found it | Fix |
|---|---|---|---|
| <exact error text> | <root cause> | <command or log that showed it> | <what fixed it> |

### Key lessons
1. <A rule you'll follow from now on, written as an instruction to yourself.>

### What I can now explain (interview-ready)
- **<Concept>:** <two or three sentences in your own words, ideally linked to something that happened to you.>

### Unresolved questions
- [ ] <Anything you're unsure about. Tick it off when answered.>

### Evidence
- <commit hash, command output, screenshot path>

### Next milestone
<What comes next.>
```
