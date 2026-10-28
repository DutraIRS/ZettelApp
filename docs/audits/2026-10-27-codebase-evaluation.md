# ZettelApp codebase evaluation

> **Status on 2026-10-28.** This is the audit as written on 2026-10-27, before the remediation commits; its findings, line numbers and counts describe that snapshot. All three release blockers have since been resolved:
>
> 1. **Test command: resolved.** `python -m pytest -q` runs and passes, and CI and the release workflow run it with coverage as a step of its own, so failing tests fail the build (`489daa4`). No committed `pyproject.toml` has ever contained the `--timeout=30` option described in H1, so that failure could not be reproduced from the repository.
> 2. **Atomic imports: fixed.** Every kind of import runs in one vault transaction; on any error it is rolled back and the image files the import added are deleted. This covers ZettelApp archives and JSON, which are also validated before the first write (`ef916b6`), and Markdown folders, zips of Markdown files and single `.md` files.
> 3. **Mind-map truncation: fixed.** The mind-map editor no longer adds ideas beyond the depth or node limit, and saving rejects an oversized map with an error instead of trimming it (`01cb1c0`). Mind maps built *From links* stop at the node limit and say how many links were left out.

**Audit date:** 2026-10-27  
**Repository:** the repository root  
**Snapshot:** branch `feature/zettelapp-1.0`, commit `f977dcedd3df608694028604e60d0fb870d92265`, plus the existing working-tree changes listed near the end of this report  
**Application:** Python 3.12+ / PySide6 Windows desktop application, version 1.0.0

## Executive assessment

ZettelApp is a substantial, coherent Windows application rather than a prototype. Its strongest areas are security-conscious boundary handling, Windows integration, pinned release dependencies, broad end-user documentation, a Qt-free core, atomic exports, a tested packaged executable, and generally clear algorithms. The application and MCP executables build and pass their packaged self-tests on Windows.

The repository is not ready for a low-risk 1.0 release without corrections. The standard test command and the current CI workflow fail before collecting tests because `pyproject.toml` requires the absent `pytest-timeout` plugin. Import is not transactional: a malformed import can report failure after records have already been committed. The mind-map UI can create a tree deeper than the model accepts, after which saving silently truncates the tree. The architecture also has concentrated maintenance risk in `MainWindow`, `Vault`, `Editor`, `OptionsDialog`, and the import/export modules.

### Overall ratings

| Area | Rating | Summary |
|---|---:|---|
| Correctness | **C+** | The corrected suite passes, but the default suite/CI is broken and two reproducible data-integrity defects exist. |
| Windows conventions | **A-** | Strong per-user installation, paths, registry, credential, IPC, shell, theme, DPI, and packaging choices. Signing is optional and the installer was not executable in this environment. |
| PEP/style | **C** | Naming and structure are mostly readable, but no enforced style configuration exists; Ruff reports 46 violations and formatting drift in 44 files. |
| Documentation | **A-** end-user / **C** developer API | End-user, security, contribution, and release documentation is unusually complete; strict public API docstring coverage is poor and one security claim exceeds actual validation. |
| SOLID | **C+** | The Qt-free core and registries are good; SRP, ISP, and DIP weaken around central UI and persistence classes. |
| DRY | **B-** | Shared security, rendering, widget, and graph helpers are good; refresh/invalidation, renderer construction, and page-to-window coordination are duplicated. |
| KISS | **B-** | Most core algorithms are direct and standard-library-oriented; several very large coordinators and nested callbacks make change paths difficult. |
| Testing/tooling | **C+** | 104 corrected tests pass with 71% branch coverage and the portable build self-tests, but the canonical command/CI fail and no lint/type/coverage gate exists. |
| Security | **B+** | No known dependency vulnerabilities; strong trust-boundary design. Import validation/atomicity and image validation claims need correction. |

### Release blockers

1. Fix the `pytest-timeout` configuration/dependency mismatch so the documented command and CI actually run.
2. Make imports validate fully before mutation and commit atomically, or provide explicit rollback.
3. Prevent the mind-map editor from creating unsupported depth, or reject the save visibly instead of silently dropping nodes.

No critical remote-code-execution or credential-disclosure issue was found in this review.

---

## Scope and method

The review covered:

- all Python modules under `zettelapp/`;
- all tests under `tests/`;
- package metadata and pinned dependencies;
- PyInstaller, PowerShell, Inno Setup, and GitHub Actions files;
- README, contribution, security, changelog, roadmap, and `docs/` content;
- Windows filesystem, registry, shell, URL protocol, IPC, theme, DPI, logging, installer, signing, and secret-storage conventions;
- correctness, security, PEP 8/257/484, SOLID, DRY, KISS, complexity, dead code, test coverage, and packaging behavior.

This was a read-only source audit except for this report and ignored build/coverage outputs. No application source file was changed.

## Objective tool results

| Check | Result |
|---|---|
| `python -m compileall -q zettelapp tests tools packaging` | **Pass**; no syntax failures. |
| Canonical `python -m pytest -q` | **Fail**, exit 2: `unrecognized arguments: --timeout=30`; `pyproject.toml:56-59` configures an option from a plugin absent from `requirements-dev.txt`. |
| Isolated pinned environment, `pytest -q -o addopts=` | **Pass: 104 tests** in 11.69 seconds. |
| Branch coverage, same corrected run | **71% total**; 8,659 statements, 2,257 missed, 1,966 branches, 268 partial branches. |
| `uvx ruff check .` | **Fail: 46 findings**: 45 `E501` line-length violations and one `F841` unused local at `zettelapp/core/storage.py:619`. |
| `uvx ruff format --check .` | **Fail**: 44 files would be reformatted. |
| Pyright, isolated pinned runtime | **Fail: 247 errors**. Many are Qt typing limitations, but several expose real optionality, model-shape, and framework-method-shadowing issues. |
| Pydocstyle | **486 findings in 45 files**: 277 `D102`, 86 `D103`, 56 `D101`, 45 `D107`, plus 22 other findings. |
| Radon cyclomatic complexity | 783 blocks, average **3.69**; 644 A, 98 B, 31 C, 7 D, 2 E, 1 F. |
| Highest cyclomatic complexity | `import_data` **43/F**; `Graph3DView.paintEvent` **31/E**; `parse_item` **31/E**; `_import_markdown_files` **29/D**; `force_layout` **28/D**. |
| Radon maintainability index | `ui/main_window.py` **0/C**; `core/storage.py` **1.64/C**; `ui/editor.py` **12.76/B**; `ui/settings_dialog.py` **14.68/B**; `core/export.py` **17.42/B**. |
| Vulture, confidence >=80% | Only `MindMapView.focusNextPrevChild(forward)`; this is a required Qt override parameter, not actionable dead code. |
| Dependency audit in an isolated pinned environment | **No known vulnerabilities found**. The local `zettelapp` package itself is not on PyPI and was correctly skipped. |
| Markdown local-link scan | 54 Markdown files, 77 local links, **0 broken local targets**. |
| Windows portable build | **Pass**: PyInstaller produced both executables; `ZettelApp.exe --self-test` and `zettelapp-mcp.exe --version` passed. |
| Built size | App folder **156 MB**; portable zip **70 MB**. |
| Installer build | Not run: Inno Setup 6 is absent. The `.iss` file was reviewed statically. |

The portable build emitted one PyInstaller warning: hidden import `tzdata` was not found. The self-tests still passed. Determine whether packaged timezone behavior needs `tzdata`; if not, explicitly suppress or document the warning.

---

## Prioritized findings

## High severity

### H1. The documented test command and CI cannot run

**Evidence**

- `pyproject.toml:56-59` defines `addopts = "--timeout=30"`.
- `requirements-dev.txt:1-3` contains runtime requirements, pytest, and PyInstaller, but not `pytest-timeout`.
- `README.md:63-65`, `docs/development.md:18-22`, `.github/workflows/ci.yml:21-26`, and `.github/workflows/release.yml:27-37` all invoke pytest without overriding this option.
- Actual result: pytest exits 2 before test collection with `unrecognized arguments: --timeout=30`.
- Removing only the invalid option produced 104 passing tests in the pinned dependency environment.

**Impact**

The main CI test job, dependent build job, and tagged release workflow are expected to fail. Contributors following the documentation also fail before running any test. This defeats the primary correctness gate.

**Recommendation**

Add a pinned compatible `pytest-timeout` to `requirements-dev.txt`, or remove the timeout option. Then run the exact documented and CI commands. Add a CI lint step that parses configuration early. Do not rely on a developer machine having undeclared plugins.

### H2. A failed import can leave partially committed data

**Evidence**

- `zettelapp/core/importer.py:142-175` creates and commits all imported notes before complete field validation.
- `importer.py:187-195` sanitizes mind maps and saves note details only in a later pass.
- Every `Vault.create_note`/`save_note` operation manages its own committed transaction; `import_data` has no enclosing transaction.
- Reproduction with two notes and a malformed second mind map (`"children": 1`) raised `TypeError: 'int' object is not iterable` while `vault.count_notes()` returned **2** after the reported failure.
- `MainWindow._import`, `ui/main_window.py:770-793`, reports the import as failed and does not disclose that data may already have changed.

**Impact**

Users can receive a failure message while blank or partially populated notes, link types, or other records remain in the vault. A retry can then create duplicates or remap IDs differently. This violates transactional expectations and complicates recovery.

**Recommendation**

1. Parse and validate the complete payload into typed in-memory structures first.
2. Reject malformed collection shapes explicitly; `children` must be a list.
3. Perform the complete import in one database transaction using non-committing internal repository methods.
4. Roll back assets created before a database failure, or stage assets and publish them only after commit.
5. Add tests asserting zero vault changes after failures in each import phase.

### H3. The mind-map UI can silently create data that persistence truncates

**Evidence**

- `zettelapp/ui/mindmap.py:221-246` limits only the total node count; it does not limit depth.
- `zettelapp/core/models.py:102-131` sanitizes recursively and stops after `MAX_MINDMAP_DEPTH = 40`.
- The save path sanitizes without presenting an error.
- Reproduction: a valid 46-node single-child chain became **41 nodes** after `sanitize_mindmap`.

**Impact**

A user can create a deep map through normal UI operations and lose the deepest nodes on save/reload without warning. This is direct silent data loss, even if the interaction is uncommon.

**Recommendation**

Enforce the same maximum depth in `add_child` and `add_sibling`, show a clear limit message, and make persistence reject over-depth in-memory trees rather than silently truncate them. Reserve truncating sanitization for untrusted imports, with a recorded warning.

---

## Medium severity

### M1. Core coordinator classes have excessive responsibility

The following concentration is the main SOLID/KISS maintenance risk:

- `ui/main_window.py`: 868 lines, 702 statements, maintainability index 0. It builds navigation and menus; owns vault lifecycle, backups, notes, links, suggestions, imports, exports, Zotero, settings, protocol messages, and window state.
- `core/storage.py`: 737 lines, 432 statements, maintainability index 1.64. `Vault` owns schema/migrations, search, notes, links, types, feedback, cards, review state, assets, backups, and lifecycle.
- `ui/editor.py`: 551 lines and maintainability index 12.76.
- `ui/settings_dialog.py`: 541 lines and maintainability index 14.68; one class owns nine settings pages and external configuration mutation.
- `core/export.py`: 503 lines and maintainability index 17.42.
- `core/importer.py`: `import_data` complexity 43/F and `_import_markdown_files` 29/D.

**Impact:** changes to a feature require touching central objects and reproducing refresh/invalidation sequences. This increases regression probability and makes isolated tests harder.

**Recommendation:** extract application services around vault lifecycle, note commands, import transactions, export jobs, and integration configuration. Split settings pages into independent widgets/controllers. Keep `MainWindow` as composition and routing, not business workflow. Split persistence into repositories behind a shared transaction boundary without creating an abstract framework.

### M2. Style and formatting are neither clean nor enforced

Ruff found 46 errors, including the real unused local `card_ids` at `core/storage.py:619`; 44 files fail Ruff formatting. There is no `[tool.ruff]` configuration, Ruff is not in `requirements-dev.txt`, and CI does not run it.

Most line-length findings come from dense UI construction and long expressions. These reduce diff readability and contribute to KISS problems. The repository otherwise uses good names, modern union types, `pathlib`, f-strings, context managers, and explicit encodings.

**Recommendation:** pin Ruff, define a deliberate target version and line length, format once in a dedicated mechanical commit, remove `F841`, and gate `ruff check` plus `ruff format --check` in CI. Avoid enabling hundreds of optional rules without triage.

### M3. Type hints exist but do not form a verified contract

Pyright reports 247 errors. A large subset comes from PySide stubs and untyped `window` parameters, but the output exposes actionable issues:

- optional values passed where non-optional values are required in import, export, clustering, storage, graph, and UI paths;
- weak `dict`/`list` annotations at untrusted JSON boundaries;
- no declared type for page dependencies, causing `window` to be inferred incorrectly;
- instance attributes shadow Qt methods: `AskPage.thread`, `GraphPage.depth`, `ScopePicker.depth`, and `MindMapView.items`;
- concrete examples in core code include possible `None` values in `cluster.py`, `export.py`, `importer.py`, `zotero.py`, and `storage.py`.

**Recommendation:** add a scoped Pyright configuration. First type-check `zettelapp/core`, `mcp_server.py`, and integration clients; then add UI gradually. Use `TypedDict` or dataclasses for imported JSON and narrow page host protocols instead of untyped `window`. Rename attributes that shadow Qt methods.

### M4. Async result freshness is inconsistent

Good patterns exist in `SuggestionService`, `GraphPage`, and `ZoteroDialog`, where request IDs suppress stale results. The same discipline is not universal:

- `ui/insights.py:363-373` starts a clustering task on every refresh without a generation/request token. An older, slower completion can overwrite newer vault results.
- `ui/graph_page.py:285-314` mutates `self._clusters` inside the worker closure (`line 308`) rather than returning all state for GUI-thread publication.
- Graph layout cache keys at `graph_page.py:280-283` omit vault generation and link topology. Cache invalidation happens in some commands but not all note-save paths, so grouping positions can remain stale after edits while cluster colours refresh.

**Recommendation:** use one reusable generation-token pattern for every background computation. Worker closures should consume immutable snapshots and return values only; mutate widget caches on the GUI thread. Include the relevant data generation/topology in cache keys or centralize invalidation.

### M5. The import UI can block the GUI for large supported inputs

`MainWindow._import` at `ui/main_window.py:770-793` executes `import_path` synchronously under a wait cursor. The importer deliberately supports large folders/archives, so parsing, hashing, image copying, and thousands of database writes can freeze the Windows event loop and trigger “Not responding”. Export correctly uses a background task and a dedicated read-only connection (`main_window.py:745-756`), showing the preferred pattern.

**Recommendation:** parse and stage imports off the GUI thread, then commit through a bounded GUI-safe/database transaction or a dedicated connection. Provide progress and cancellation semantics that preserve atomicity.

### M6. Coverage is respectable overall but weak at important Windows and UI boundaries

The corrected run reached 71% branch coverage. Notable low or zero areas:

- `app.py`: 0%; startup, IPC, crash hook, and application lifecycle are mostly untested directly.
- `winintegration.py`: 34%; registry and shell behavior are high-value Windows-specific code.
- `paths.py`: 43%.
- `mindmap.py`: 19%; this gap allowed the depth-loss defect.
- `preview.py`: 39%; this is a rendering/security boundary.
- `markdown_editor.py`: 44%.
- `zotero_dialog.py`: 0%.
- `review_page.py`: 50%; `ask_page.py`: 55%; `main_window.py`: 56%.

The CI has no coverage measurement or threshold.

**Recommendation:** add targeted behavior tests, not blanket line tests. Prioritize import rollback, mind-map limits, URL/registry quoting, IPC size and malformed messages, preview resource loading, async stale-result suppression, and packaged app behavior. Add a modest branch threshold after stabilizing the measurement.

### M7. Release signing is optional and unsigned release publication can proceed silently

`packaging/build.ps1:29-37` signs only when `ZETTELAPP_SIGN_PFX` is set. `.github/workflows/release.yml:40-49` treats signing credentials as optional and still publishes a release when absent.

**Impact:** unsigned Windows binaries produce publisher warnings and reduced SmartScreen trust; a missing secret can silently turn a normally signed release into an unsigned one.

**Recommendation:** keep signing optional for local builds but require it for production tags, or make unsigned release status explicit and manually approved. Verify signatures after signing. Consider generating an SBOM and provenance attestation in the release workflow.

### M8. MCP configuration mutation assumes `mcpServers` is an object

`ui/settings_dialog.py:393-403` validates only the root JSON object. `config.setdefault("mcpServers", {})["zettelapp"] = ...` raises `TypeError` if the existing `mcpServers` value is a list, string, or null; the handler catches only `OSError` and `ValueError`.

**Recommendation:** validate the nested shape and present a normal error without modifying the file. Keep the existing backup and atomic `os.replace` pattern, which are good.

### M9. Strict public API documentation is sparse

Pydocstyle reports 486 findings, dominated by missing public method/function/class docstrings. Applying PEP 257 blindly to Qt overrides would add noise, but public core APIs such as `Vault`, import/export entry points, protocol handlers, and integration clients need contracts covering mutability, transaction behavior, thread affinity, exceptions, and limits.

**Recommendation:** configure pydocstyle/Ruff documentation rules narrowly for exported core and service APIs. Exclude obvious Qt overrides and private helpers. Document behavior that callers cannot infer from the signature.

### M10. Image “verification” is signature validation, not complete decode validation

`security.py:104-114` recognizes image type from magic bytes. `Vault.store_asset` uses that result and a 25 MB compressed-byte limit, while preview decoding occurs later through `QImage`. The documentation states that images are “verified by content” (`docs/privacy-and-security.md:53-54`), which is directionally true but stronger than the implementation: it does not validate pixel dimensions or decoded memory cost before storage.

**Impact:** malformed or decompression-heavy raster files can reach Qt image decoders and may cause excessive memory use or decoder-specific failures.

**Recommendation:** decode in a controlled step before acceptance, reject invalid images, impose pixel/dimension limits, and re-encode accepted raster data where practical. At minimum, make the documentation precise about signature and size checks.

---

## Low severity and maintainability findings

### L1. Broad exception handling obscures failure contracts

Examples include `MainWindow.open_vault` at `ui/main_window.py:336-342`, whose tuple `(VaultError, OSError, Exception)` is equivalent to `Exception`, and multiple broad handlers justified as UI/error boundaries. Broad handling is valid at top-level task/process boundaries, but redundant tuples and broad catches inside workflows make expected errors unclear.

Use narrow exceptions in services and broad logging only at application/thread/protocol boundaries.

### L2. LLM cancellation is cooperative and reports completion after stop

`StreamThread.cancel` sets an event; it cannot interrupt a blocked network read. After the loop breaks, `finished_ok` is emitted (`ui/workers.py:137-152`), so `AskPage._done` can report “Answer complete” after the user pressed Stop. The documentation says Stop “cancels it”.

Track a cancelled terminal state, emit a distinct signal, and close/cancel the provider stream when supported.

### L3. One Zotero lookup runs synchronously in the dialog accept path

`ui/zotero_dialog.py:129-140` calls `pdf_attachment` on the GUI thread. The client has a timeout, so “New literature note” can briefly freeze the dialog when Zotero is slow. Reuse `run_task` and disable the relevant buttons while resolving the attachment.

### L4. Documentation-generated content should remain explicitly generated

The repository has strong source documentation plus generated website content. Preserve a one-way `docs/ -> website/docs/` workflow and add a CI check that regenerated output is clean. This prevents DRY drift without trying to hand-maintain both forms.

### L5. CI tests only one Python/Windows combination

The project declares Python >=3.12 but CI uses only Python 3.14 on `windows-latest`. Test at least the minimum supported Python and the release Python. If Windows 10 support is contractual, include periodic Windows 10 packaging/manual validation because GitHub-hosted runners do not cover it directly.

### L6. GitHub Actions use moving major tags

Actions are referenced as `actions/checkout@v5`, `setup-python@v6`, and `upload-artifact@v4`. Pinning immutable commit SHAs is stronger supply-chain practice for a release pipeline. Dependabot can maintain those pins.

### L7. The installer language setting is not consumed by the application

`packaging/installer.iss:6-7,106-107` stores the installer language in QSettings, but the application has no translation loading path; the roadmap says translations are future work. The installer itself is translated, but comments/developer docs should not imply that this currently selects application UI language.

---

## Windows development conventions

## What is done well

- **Correct data locations:** `paths.py` uses Documents for the default vault and Local AppData for logs, backups, and cache. Settings use `QSettings` under HKCU.
- **Per-user installation:** Inno defaults to `{autopf}\ZettelApp` with `PrivilegesRequired=lowest`; admin rights are not required.
- **Upgrade identity:** a stable Inno `AppId` supports upgrades rather than parallel installs.
- **Uninstall safety:** user vaults, backups, and settings are intentionally not removed wholesale.
- **Custom protocol safety:** registry command quoting is correct in `installer.iss:100-105`; runtime registration is per-user; parsed URLs can only open a validated note ID.
- **Single instance:** server names are user-specific; `QLocalServer.UserAccessOption` restricts IPC to the current user; message size is bounded.
- **Taskbar identity:** `APP_USER_MODEL_ID = "ZettelApp.Desktop"` is applied and matches shortcuts.
- **Shell invocation:** Explorer is launched with argument lists rather than a shell command string.
- **Credential handling:** Windows Credential Manager is used; the native memory buffer is cleared on successful reads; no key is written to QSettings.
- **Theme and accessibility:** Windows light/dark preference and accent are respected; high-DPI pixmaps are generated; Qt 6 handles high DPI; accessible names and keyboard shortcuts are common; link types use both colour and dash patterns.
- **Logging:** rotating Local AppData logs with fallback handling are appropriate.
- **Packaging:** one-folder PyInstaller reduces startup delay and antivirus friction; version resources, icon, separate GUI/console executables, portable zip, checksums, packaged self-tests, and optional signing are present.
- **Installer:** architecture and Windows build minimum are explicit; URL protocol registration uses HKA correctly for per-user/all-user mode; files remain dynamically linked for LGPL compliance.
- **Build verification:** the actual Windows portable build and both packaged self-tests passed.

## Improvements

- Make signing mandatory or explicitly approved for official releases.
- Add an application/installer mutex or verify Inno Restart Manager behavior during upgrades while the app/MCP process is running.
- Test installer install, upgrade, URL opening, repair, all-user override, and uninstall in a disposable Windows VM.
- Investigate or suppress the `tzdata` PyInstaller warning.
- Verify the packaged executable on both Windows 10 21H2 and current Windows 11, including high DPI, multiple monitors, dark title bars, and non-ASCII user/vault paths.
- Add Authenticode verification and installer smoke tests to release CI.
- Clarify that installer language does not yet localize application content.

---

## PEP and Python-quality evaluation

## PEP 8

Strengths:

- consistent four-space indentation and conventional naming;
- modern type syntax (`X | None`, built-in generics);
- `pathlib` and explicit UTF-8 use;
- no wildcard imports;
- generally narrow modules in core algorithms;
- context managers around files, archives, registry keys, and database transactions;
- module docstrings across nearly all application modules.

Weaknesses:

- 45 Ruff `E501` findings and 44 formatter-drift files;
- one real `F841` unused variable;
- dense long lines and compound expressions in UI code;
- no project formatter/linter policy or CI gate;
- broad exceptions in several non-top-level workflows;
- local imports are sometimes used to avoid cycles/heavy startup but also reveal coupling.

## PEP 257

Module-level intent is usually documented, and complex security/algorithm helpers often have useful docstrings. Public API contracts are incomplete. A strict default pydocstyle run yields 486 findings, but enforcing every Qt callback docstring would be counterproductive. Apply a curated policy to public core/service APIs.

## PEP 484 and typing

The code has broad annotation coverage but no checked baseline. Untyped dictionaries at import/protocol boundaries and untyped page host objects weaken the value of those annotations. Establish a staged type-checking target and avoid “fixing” Qt stub false positives with blanket ignores.

## Packaging PEPs

`pyproject.toml` correctly uses a PEP 517 build backend and PEP 621 project metadata. Runtime dependencies in project metadata are lower-bounded, while release requirements are pinned. This is reasonable for an installable package plus reproducible application releases. Consider pinning the build-system requirement for fully reproducible releases and generating a lock/constraints artifact with hashes.

---

## Documentation evaluation

## Strengths

- README gives concise feature, installation, build, documentation, licensing, and security entry points.
- `docs/` has 16 focused guides covering onboarding, method, notes, graph, review, integrations, AI, MCP, security, import/export, shortcuts, FAQ, and development.
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `ROADMAP.md`, license, and third-party notices are present.
- Security documentation describes assets, links, archives, MCP write gating, local connections, logs, backups, and credentials concretely.
- Development documentation explains architecture and release procedures.
- Automated scan found zero broken local Markdown links.
- UI text and docs generally agree on menu names and major workflows.

## Gaps

- Correct the import claim in `docs/privacy-and-security.md:55-56`: malformed mind-map shape is not safely rejected and failed imports are not atomic.
- Clarify image validation as described in M10.
- Correct testing instructions/configuration as described in H1.
- Add architecture documentation for transaction boundaries, thread affinity, background-task snapshots, cache invalidation, and the database schema/migration policy.
- Add a release checklist that verifies signing, checksums, dependency audit, CI, portable build, installer upgrade/uninstall, and release artifacts.
- Document recovery from partial/corrupt imports after the implementation is corrected.
- Keep public API docstrings focused on contracts, not restating implementation.

---

## SOLID evaluation

### Single Responsibility Principle

**Good:** Qt-free core modules separate similarity, clustering, graph layout, rendering, security, LLM, Zotero, Anki, and quiz logic. `workers.py` centralizes common task execution. `security.py` centralizes trust-boundary helpers.

**Weak:** `MainWindow`, `Vault`, `Editor`, `OptionsDialog`, importer, and exporter each own too many reasons to change. The very low maintainability indices corroborate this rather than relying on file length alone.

### Open/Closed Principle

**Good:** AI providers use a registry and adapter map; export dispatch uses a writer map; suggestion features are declarative; link types are data-driven. These make common extensions local.

**Weak:** adding a complete page/integration still requires edits across `MainWindow`, menus, navigation, settings, docs, and often page internals. Import format dispatch and large procedural import logic are less extensible than export dispatch.

### Liskov Substitution Principle

The project has few business-class inheritance hierarchies, reducing LSP risk. Qt subclasses generally honor required callbacks. However, attributes shadow inherited Qt methods (`thread`, `depth`, `items`), which weakens substitutability and confuses tooling/callers. Rename these fields.

### Interface Segregation Principle

Core functions usually accept focused data. UI pages instead receive and retain the whole main window and directly reach into `window.vault`, `window.resolve_scope`, `window.open_note`, `window.export_dialog`, and other members. Each page therefore depends on a broad implicit interface.

Define small host protocols or inject focused callbacks/services. Do not create interfaces where a simple function argument is sufficient.

### Dependency Inversion Principle

The Qt-free core is a strong boundary. The UI still constructs concrete clients and accesses global settings, the concrete `Vault`, and the concrete main window directly. A thin application-service layer would let pages depend on use-case operations and immutable view data rather than persistence/UI internals.

---

## DRY evaluation

## Good reuse

- one renderer/security model is reused for notes, AI answers, exports, and Anki;
- URL, note-ID, asset-name, filename, archive, and image checks are centralized;
- `run_task`, `SuggestionService`, widgets, theme, icon, graph-common, and scope helpers avoid substantial duplication;
- atomic export output is centralized;
- network clients share no-proxy loopback behavior where appropriate;
- data-driven registries reduce provider/format/type duplication.

## Repetition to reduce

- note renderer construction is repeated in `MainWindow`, `AskPage`, and `ReviewPage`;
- list/tag/count/side/graph/suggestion refresh and invalidation sequences occur in many command handlers;
- several pages repeat “snapshot -> background work -> stale-result guard -> publish” with inconsistent guards;
- page classes repeatedly depend on broad `window` access;
- file-dialog/result-notification patterns repeat;
- database methods repeat transaction/commit wrappers, making a cross-operation import transaction difficult.

Prefer a few named application commands (`save_note_and_refresh`, `publish_vault_change`, transactional import service) over a generic event framework. DRY should remove divergent behavior, not hide straightforward code behind abstractions.

---

## KISS evaluation

## Good simplicity

- algorithms are largely explicit NumPy/Python implementations with deterministic seeds and understandable limits;
- standard library HTTP is used for small local/OpenAI-compatible clients;
- SQLite is accessed directly with bound parameters;
- export dispatch is a simple mapping;
- the application avoids a plugin framework, ORM, dependency-injection container, web runtime, and unnecessary process architecture;
- PyInstaller one-folder packaging is simpler and more reliable than one-file packaging.

## Complexity hotspots

- `import_data` at complexity 43 is too branch-dense for a trust boundary;
- 2D/3D graph painting combines data, geometry, hit testing, styling, and interaction;
- nested callbacks and lambdas in UI coordinators obscure control flow and cancellation/error states;
- giant window/editor/settings classes make simple feature changes traverse many mutable fields;
- status, cache, and invalidation state are distributed rather than represented by a small explicit change model.

Refactor around tested use cases and data snapshots. Avoid introducing generalized buses, repositories for every table, or a service locator; those would exchange current complexity for abstraction complexity.

---

## Security and dependency assessment

## Strong controls

- bound SQL parameters and FTS query escaping;
- archive path traversal, entry-count, per-file, and aggregate-size controls;
- content-addressed asset names and safe filename handling;
- raw HTML disabled in Markdown; generated links/HTML escaped;
- preview resource loading restricted to validated vault asset names;
- external URL scheme allowlist;
- HTTPS required for remote AI endpoints, with HTTP restricted to loopback;
- no-proxy local Anki/Zotero connections;
- API key scrubbing from errors and Credential Manager storage;
- MCP read-only default plus dual write authorization;
- MCP stdout protection and bounded JSON-RPC inputs;
- per-user local IPC restriction and bounded message size;
- no shell-string construction for Explorer or application protocol invocation;
- dependency audit found no known vulnerabilities in pinned packages.

## Remaining work

- fix malformed/partial import handling;
- strengthen raster decode validation and limits;
- add security regression tests for all malformed collection shapes, not only oversized scalar fields;
- audit GitHub Actions with immutable pins and release provenance;
- require or explicitly approve release signing;
- consider fuzz/property tests for archive manifests, Markdown front matter, JSON-RPC messages, SSE parsing, URL parsing, and renderer links.

---

## Recommended implementation plan

### Phase 0: release blockers

1. Add/pin `pytest-timeout` or remove `--timeout=30`; prove `python -m pytest -q` and both CI workflows.
2. Add regression tests for import rollback and malformed nested structures.
3. Refactor import into validate/stage/commit with one transaction.
4. Add mind-map depth checks in UI and reject silent truncation.
5. Correct security and testing documentation.

### Phase 1: automated quality baseline

1. Pin Ruff; format in one mechanical commit; remove all default lint findings.
2. Add CI jobs for Ruff, tests at Python 3.12 and 3.14, branch coverage, and dependency audit.
3. Establish Pyright for `core/` first and reduce genuine errors before extending to UI.
4. Add package/install smoke tests and retain the current packaged self-tests.

### Phase 2: architectural risk reduction

1. Extract import/export application services and a reusable vault-change publication path.
2. Split `MainWindow` by command domains while keeping composition centralized.
3. Split `OptionsDialog` into page widgets.
4. Introduce narrow page host protocols/callbacks.
5. Split `Vault` internal repositories only where needed to support transactions and focused testing.
6. Standardize generation-token handling for all background tasks.

### Phase 3: Windows release hardening

1. Run installer install/upgrade/uninstall/protocol tests in disposable VMs.
2. Require Authenticode for official tags and verify signatures.
3. Add SBOM/provenance and immutable Action pins.
4. Test Windows 10/11, non-ASCII paths, synced folders, multi-monitor DPI, and portable mode.
5. Decide whether `tzdata` must be bundled and remove unexplained build warnings.

---

## Existing working-tree state

Before this report was created, the audit observed the following non-clean state:

- branch `feature/zettelapp-1.0`, ahead of its remote by 3 commits;
- modified: `README.md`;
- untracked: `.github/workflows/pages.yml`, `CHANGELOG.md`, `CONTRIBUTING.md`, `ROADMAP.md`, `SECURITY.md`, `THIRD_PARTY_NOTICES.md`, `docs/`, `tools/build_site.py`, and `website/`.

Those files were reviewed as part of the current working tree. This report does not assert that they belong to commit `f977dcedd3df608694028604e60d0fb870d92265`, and it did not modify them.

## Final conclusion

ZettelApp has a better security model, Windows integration layer, packaging story, and end-user documentation than most projects at this size. The core design choices are generally sound. The immediate risks are not conceptual; they are enforceability and state integrity: the declared test gate is broken, imports can partially commit, and mind maps can be silently truncated. Fix those first. Then enforce the existing quality intent with Ruff, a staged type checker, coverage at critical boundaries, and smaller application coordinators.
