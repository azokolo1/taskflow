## Lesson 1 — Linux filesystem fundamentals (on WSL)

**Date:** 13–15 November 2026
**Status:** ✅ Complete

### What I set out to do
Get comfortable moving around a Linux filesystem and inspecting it (paths, inodes, links, disk usage, `find`), using my own TaskFlow repo on WSL as the practice ground, so I can work in it without guessing.

### What I did myself
- Moved the architecture diagram files (`.png`, `.svg`) and `generate_architecture_diagram.py` from my home folder into `docs/architecture/` and `scripts/` after three failed `cp` attempts, using `find` to locate them first.
- Found the `:Zone.Identifier` files Windows attached to downloads and dealt with them so they stay out of the repo.
- Explored the root filesystem with `ls /` and `ls -l /etc | head -15`.
- Compared disks with `df -h`, `df -h ~ /mnt/c` and `df -hT`. My Linux home is `ext4` (1007G, 4% used). `/mnt/c` is the Windows drive mounted over `9p` (476G, ~70% used).
- Inspected `README.md` with `stat` and `ls -i`: inode 2104, mode `0644`, with Access/Modify/Change/Birth times.
- Built a hard link vs symlink lab in `~/lab/l1`. I created `original.txt`, a hard link and a symlink, compared them with `ls -li`, deleted the original, and checked what survived.
- Proved the difference between mtime and ctime: `chmod 600` on a file changed its **Change** time but left **Modify** untouched.
- Measured the repo with `du -sh`: 2.4M in total, of which `.git` is 1.3M and `docs/` (mostly the PNG) is 1000K.
- Searched the repo with `find`:
  - `-name ".gitkeep"` found 11 placeholder files.
  - `-size +100k` found only `taskflow-architecture.png`.
  - `-mmin -60` found nothing changed in the last hour.
  - `-type f -empty` found the empty scaffold files: `Dockerfile`, `compose.yaml`, `.dockerignore`, `app/main.py` and the `__init__.py` files.
- Counted entries in `/etc` by type with `ls -l /etc | grep -c '^d'`, `'^-'` and `'^l'`: 102 directories, 78 files, 7 symlinks. Cross-checked against `ls /etc | wc -l` = 187 (102 + 78 + 7, so the counts add up).
- Listed the 7 symlinks in `/etc`. `resolv.conf` points to `/mnt/wsl/resolv.conf`, which is WSL managing DNS for me. `localtime` points to `Europe/London`.

### Problems I hit and how I diagnosed them
| Symptom | Cause | How I found it | Fix |
|---|---|---|---|
| `cp: cannot stat '/home/swift-tech/swift-tech/taskflow-architecture.png': No such file or directory` | `~` already expands to `/home/swift-tech`, so `~/swift-tech/` pointed to a folder that doesn't exist | The error message showed the expanded path with `swift-tech` twice | Used the real location: `cp ~/taskflow-architecture.* docs/architecture/` |
| `cp: cannot stat '/home/swift-tech/Downloads/...'` | Files downloaded in Windows don't land in the Linux `~/Downloads` | `find ~ /mnt/c/Users/*/Downloads -maxdepth 3 -name 'taskflow-architecture.*'` showed the files were in `~` | Copied from `~` |
| `*:Zone.Identifier` files next to my downloads | Windows tags files downloaded from the internet. Dragging them into WSL brings the tag along as a separate file | The same `find` output | `rm ~/*:Zone.Identifier` and added `*:Zone.Identifier` to `.gitignore` |
| `du: cannot access '~taskflow': No such file or directory` | `~name` means "the home folder of user *name*". There is no user `taskflow`, so the shell left it as literal text | Compared it with `du -sh ~/taskflow`, which worked | Always write `~/` with the slash |
| `du -sh ~/taskflow/* ~/taskflow/ .[!.]*` reported `~/taskflow/` as 1.3M, but `du -sh ~/taskflow` said 2.4M | (1) `du` counts each directory once per run, so `~/taskflow/` only showed what the `*` glob hadn't already counted, mostly `.git`. (2) `.[!.]*` was expanded in my current folder (`~/lab/l1`), not in the repo, and `2>/dev/null` hid the error | `du -sh ~/taskflow/.git` came to exactly 1.3M | `cd ~/taskflow && du -sh * .[!.]* \| sort -h`, without hiding errors while learning |
| `find: unknown predicate '-not-path'` | `-not` and `-path` are two separate tests and need a space between them | The error message named the bad predicate | `-not -path "./.git/*"` |
| `find . -name ".py"` found nothing | With no wildcard, it only matches a file named exactly `.py` | Spotted while fixing the line above | `-name "*.py"` |
| `find . -name *.py` (unquoted) worked | The shell expands `*.py` against the current folder before `find` runs. The repo root has no `.py` files, so bash passed the pattern through unchanged. It worked by luck | Tested it from the repo root and compared with the quoted version | Always quote patterns: `-name "*.py"` |
| `catsymlink.txt: command not found` | Typo, missing space | Read the error | `cat symlink.txt` |
| `cat symlink.txt` → `No such file or directory` after `rm original.txt` | A symlink stores a path, not the data. Its target was gone, so it was left pointing at nothing | `ls -li` still showed `symlink.txt -> original.txt` | Expected result; this was the point of the lab |

### Key lessons
1. Read the expanded path in an error message before retrying. The shell tells me what it actually tried.
2. Write `~/` with the slash, and use `"$HOME/..."` in scripts. Never put `~` inside quotes.
3. Quote every pattern meant for a command (`find -name '*.py'`, `git ls-files '*.py'`). Unquoted patterns depend on whatever folder I happen to be in.
4. Keep work on the Linux side (`~/taskflow`). Use `/mnt/c` only to bring files in or out, then check their permissions.
5. Don't hide errors with `2>/dev/null` while learning or debugging. It hid the clue twice in this lesson.
6. When two numbers disagree (`du` vs `du`, `df` vs `du`), work out why before trusting either.
7. Rotate a leaked secret first, clean Git history second.

### What I can now explain (interview-ready)
- **Inode:** The filename is just a label in a folder. The inode holds the file's details (permissions, owner, times, where the data is), and the data blocks hold the contents. `README.md` is inode 2104, and `ls -i` and `stat` show it.
- **Hard link vs symlink:** A hard link is a second name for the same inode. My `original.txt` and `hardlink.txt` both showed inode 14776 with link count 2. Deleting the original dropped the count to 1 and the data survived. A symlink is a separate small file holding a path (its own inode, 14778). When I deleted the target, it broke.
- **mtime vs ctime:** mtime changes when the contents change. ctime changes when the inode changes, which includes `chmod`, `chown` and renames. I proved it: `chmod 600` moved Change by 2 seconds and left Modify alone. ctime is *change* time, not creation time. Creation is `Birth`.
- **`df` vs `du`:** `df` asks the filesystem how many blocks are in use. `du` walks the folders and adds up the files it finds. They can disagree when a deleted file is still held open by a process: `df` counts it but `du` can't see it. Find it with `sudo lsof +L1` and fix it by restarting the process or truncating the file through `/proc/<PID>/fd/<FD>`.
- **Absolute vs relative paths:** `~/taskflow/scripts` always means the same place. `scripts` means "inside wherever I am now". Scripts should build paths from their own location (`Path(__file__).resolve()`) so they work in CI too.
- **Shell globbing:** Bash expands `*` before the command runs. That's why `find -name *.py` can work, silently give wrong results, or error out, depending on the current folder.
- **`.gitignore` order:** The last matching rule wins, so `!.env.example` has to come after `.env.*`. `git check-ignore -v <file>` shows which rule matched.
- **`.env` vs `.env.example`:** The example documents which variables exist and belongs in Git. The real `.env` holds secrets and never does, because Git history is permanent. `git rm --cached` stops future commits including the file but doesn't remove it from past commits.
- **Terraform lock file vs state:** `.terraform.lock.hcl` pins provider versions and checksums and is committed with the code. `terraform.tfstate` records live infrastructure, holds secrets in plain text and needs locking, so it lives in an encrypted S3 backend with versioning and `use_lockfile = true`.
- **WSL and `/mnt/c`:** `/mnt/c` is NTFS mounted over `9p`, and Linux permissions there are made up (777). `mv` keeps those permissions when moving onto ext4, so files arrive world-writable. The fix is `chmod`, plus mounting with `metadata` in `/etc/wsl.conf`.

### Unresolved questions
- [ ] Why do the snap mounts, `/dev/loop0` and `/usr/src/linux-headers-...` show 100% used in `df -h`? Is that a problem?
- [ ] Have I checked and fixed the permissions on every file that came in through `/mnt/c` (diagram files and generator script)?
- [ ] Should I add `[automount] options = "metadata,umask=022,fmask=133"` to `/etc/wsl.conf`, and what else does it change?
- [ ] Should `scripts/generate_architecture_diagram.py` be `644` (run with `python3`) or `755` with a shebang?

### Evidence
- Terminal log of this lesson (`~/lab/l1` link lab, `stat`, `df -hT`, `du`, `find` runs)
- `ls -li` output: `14776 … 2 … hardlink.txt` / `14776 … 2 … original.txt` / `14778 … symlink.txt -> original.txt`
- mtime/ctime proof: `Modify: 00:10:45.096 | Change: 00:10:47.118` after `chmod 600`
- Commit adding the diagram and generator script: `<commit hash>`
- Commit adding the diagram to the README: `<commit hash>`

### Next milestone
Lesson 2: fill in the empty scaffolding that `find -empty` turned up. That means a minimal FastAPI app in `app/main.py` with a `/health` endpoint, a `Dockerfile`, `.dockerignore` and `compose.yaml`, running locally in Docker.
