# Russian Abstract Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Russian-only abstract page to the thesis and ensure it's displayed in "senior" mode.

**Architecture:** Update the custom LaTeX class `BYUPhysForDegree.cls` to modify the default `makepreliminarypages` and simplify the `abstractpage` layout. Add the `\Abstract` content to `main.tex`.

**Tech Stack:** LaTeX

---

### Task 1: Modify BYUPhysForDegree.cls

**Files:**
- Modify: `/Users/andreytrifonov/Development/diploma/thesis/BYUPhysForDegree.cls`

- [ ] **Step 1: Update makepreliminarypages for senior mode**
Change the default `\makepreliminarypages` (lines 204-212) to include `\abstractpage`.

```latex
  \newcommand{\makepreliminarypages}{
    \preliminarymargins 
    \titlepage 
    \abstractpage 
%	\copyrightpage 
%	\seniorapprovalpage 
%    \acknowledgmentspage 
    \fixmargins
    \renewcommand{\clearemptydoublepage}{\cle@remptydoublep@ge}
  }
```

- [ ] **Step 2: Simplify abstractpage to Russian-only**
Replace the content of `\abstractpage` (lines 571-600) to remove the English section.

```latex
\newcommand{\abstractpage}{

    \thispagestyle{empty}
    \begin{abstractenv}
    \begin{center}
    \providecommand\pdfbookmark[3][]{} \pdfbookmark[1]{Abstract}{bm:Abstract}    
    \vspace*{0.375in}
    {\bf \@AbstractText}\\[1\baselineskip]
    {\large \@TitleTop\\
    \@TitleBottom}\\[1\baselineskip]
    {\em \@Author}\\[\baselineskip]
    \end{center}   
    \renewcommand{\baselinestretch}{1.33}\small\normalsize
    \@Abstract
    \end{abstractenv}
    \clearemptydoublepage
  }
```

- [ ] **Step 3: Commit class changes**

```bash
git add /Users/andreytrifonov/Development/diploma/thesis/BYUPhysForDegree.cls
git commit -m "style: add abstract page to senior mode and simplify layout"
```

### Task 2: Update main.tex

**Files:**
- Modify: `/Users/andreytrifonov/Development/diploma/thesis/main.tex`

- [ ] **Step 1: Add Abstract content placeholder**
Insert the `\Abstract` command before `\begin{document}`.

```latex
...
\AbstractText{Аннотация}
\Abstract{Ваш текст аннотации здесь...}

\begin{document}
...
```

- [ ] **Step 2: Commit main.tex changes**

```bash
git add /Users/andreytrifonov/Development/diploma/thesis/main.tex
git commit -m "docs: add Russian abstract placeholder to main.tex"
```
