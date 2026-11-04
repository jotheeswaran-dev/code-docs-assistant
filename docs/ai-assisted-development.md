# How I used AI tools

## 1. The short version

Claude Code wrote most of the lines in this repository. I chose what to build, in what
order, and what to keep. No change entered the history until I had read it and said so.

The point of the method below is not speed. It is that I can defend every line here,
and that a reader can see why each decision was made.

## 2. The loop

I use the same loop for each step of work.

| Step | What happens | Who decides |
|---|---|---|
| Clarify | Questions before code. Options, with a recommendation. | Me |
| Decide | One choice, with the reason written down | Me |
| Slice | The smallest step that still makes sense | Me |
| Build | The assistant writes the code and runs the checks | The assistant |
| Verify | I read the change. I run it. | Me |
| Commit | Only after I say so. One logical change for each commit. | Me |

The loop never skips a step. The assistant does not commit, and it does not push.

## 3. The rule that matters most

**I verify before anything is committed.**

A model is fluent. Fluent and wrong looks the same as fluent and right, and it looks
right for longer than it should. Reading the change is the only control that catches
that, and it has to happen before the change is in the history.

The commit log shows the shape this gives:

| Measure | Value |
|---|---|
| Commits | 48 |
| Files changed in a commit, median | 2 |
| Commit kinds | 36 `Add.`, 7 `Modify.`, 5 `Fix.` |

A commit of two files is a commit I can read in a minute. A commit of forty is one I
would wave through.

## 4. What this caught

Each row below is a real fault from this build. The order is the order they happened.

| What went wrong | How it was caught |
|---|---|
| A decision record claimed 450 chunks each second. The test had used one short string many times. | Running it on a real repository. The true rate is 12.5 each second. |
| Two ways to make the embedding faster were proposed as obvious wins. | Measuring both. Both were slower, so both are recorded as rejected. |
| `DELETE` on the word index passes while the table is empty, and fails once it holds rows. | A test. A second index build would have failed for every user. |
| A record said the repository map needed a model call. The code used none. | Reading the record against the code before the step closed. |
| A record said the server deletes a claim with no citation. It reports it instead. | The same reading. |
| The citation check reported four faults on an answer that was correctly cited. | Reading a real answer. A full stop in a file name was cutting a line in two. |
| The eval said the system refused only one of three questions it must refuse. | Reading the three answers before changing any code. The answers were right. The grading rule was wrong. |
| A global ignore file on my machine hid three source files from the repository. | A clone test. The web app would not have built for anyone else. |
| The same file hid the environment template. | The same test, at an earlier step. |
| A production build during a dev run broke the page. Twice. | Me, opening the page. The checks were all green. |
| Every `make` command failed on my shell, because a tool was not on the path. | Me, running `make eval` myself. The assistant had set the path in its own shell, so it never saw the fault. |

The last two rows are the important ones. Every automated check passed while the thing
was broken. A green check is evidence about the checks, not about the product.

## 5. Do

- **Ask for the trade-off, not the answer.** Two or three options with a recommendation.
  A single answer hides the choice I need to make.
- **Make it measure before it claims.** Any number in a document must come from a run.
  Three wrong numbers in this build came from a plausible guess.
- **Read the real output.** Not the summary of the output. Two faults here were found by
  reading one answer and three by reading one log.
- **Keep the slices small.** Two files in a commit is a commit I will actually read.
- **Write the decision down while it is fresh.** The reason for a choice is gone a day later.
- **Let the record argue with the code.** Three records in this repository were wrong,
  and reading them against the code is what found it.
- **Run it yourself.** My own shell, my own browser. Not the assistant's.

## 6. Do not

- **Do not let it commit.** The gate is the method. Without it there is no review.
- **Do not accept a number that was not measured.** Especially a flattering one.
- **Do not accept a test that was written after the code to match the code.** Say what
  the rule is first.
- **Do not take a comment on every line.** Dense comments read as filler and hide the
  one comment that matters.
- **Do not let it widen the task.** A step that grows past its slice is a step to stop
  and question.
- **Do not trust a green check as proof that the product works.** Open it.
- **Do not ask it to write my own words.** This document is the clear case. The README
  prose and the judgement in it are mine.

## 7. What makes it repeatable

| Control | Effect |
|---|---|
| The method is written down, not in my head | The same loop runs on day one and day five |
| `<Verb>. <lower-case summary>` for each commit | The log reads as a list of decisions |
| One record for each decision | A later change has to argue with the record |
| `make lint`, `make test` on each slice | A fault surfaces in the slice that caused it |
| `make eval` | A change to retrieval shows as a number in under a second |
| A clone test before a push | The repository that others get is the one I tested |

## 8. What I would do differently

- I let the assistant work in a shell it had set up itself. That hid a broken `make` for
  the whole build. I would run the commands in my own shell at every step, not at the end.
- I accepted three documents with numbers that had not been measured. The fix is simple:
  a number goes in a document only after a command has printed it.
- I would write the evaluation set earlier. It arrived in the last step, and two faults
  it found had been in the code for hours.
