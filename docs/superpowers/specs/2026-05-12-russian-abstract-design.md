# Design: Russian Abstract Page Support

## Goal
Add a Russian-only abstract page to the thesis, ensuring it appears correctly in the "senior" thesis mode (default) and follows the existing document style.

## Current State
- `BYUPhysForDegree.cls` defines `\abstractpage` but it's only called in `honors`, `masters`, and `phd` modes.
- `\abstractpage` currently includes both Russian and English versions on one page.
- `main.tex` uses `senior` mode, which currently only outputs the title page.

## Proposed Changes

### 1. BYUPhysForDegree.cls
- Modify `\makepreliminarypages` (default version) to include `\abstractpage`.
- Update `\abstractpage` to remove the English section and only display the content provided in `\@Abstract`.
- Ensure proper spacing and layout for the Russian-only content.

### 2. main.tex
- Add a placeholder `\Abstract{...}` command before `\begin{document}` so the user can easily fill in their annotation.

## Verification Plan
- Manual check of the generated PDF (if environment supports it, otherwise trust the LaTeX syntax).
- Ensure no compilation errors are introduced.
