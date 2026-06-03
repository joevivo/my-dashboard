\# Books Data Model



Date: 2026-06-03



\## Purpose



The Books section exists to capture reading as part of a person's intellectual history.



It should answer:



> What ideas have occupied my attention over time?



It is not primarily a reading tracker, streak counter, or ranking system.



\## Design Principles



1\. Prefer meaningful memory signals over numeric ratings.

2\. Avoid fields the user cannot realistically maintain.

3\. Keep book entry lightweight.

4\. Separate books, notes, quotes, and themes so the system can evolve into a knowledge graph.

5\. Treat rereading as a meaningful signal.

6\. Treat impact as more important than evaluation.



\## Core Book Schema



```js

{

&#x20; id: string,

&#x20; title: string,

&#x20; author: string,

&#x20; publicationYear: number | null,

&#x20; format: "Hardcover" | "Paperback" | "eBook" | "Audiobook" | "Other" | "Unknown",

&#x20; impact: "None" | "Low" | "Medium" | "High" | "Transformative",

&#x20; timesRead: number,

&#x20; readYear: number | null,

&#x20; themes: string\[],

&#x20; tags: string\[],

&#x20; source: "Purchased" | "Library" | "Gift" | "Borrowed" | "Subscription" | "Unknown"

}

```



\## Required Fields



Only these fields are required:



```js

title

author

```



All other fields are optional or defaulted.



\## Removed Fields



The following fields are intentionally excluded:



```text

Read Start

Read Finish

Numeric Rating

```



Reason:



Most users cannot reliably remember exact start and finish dates. Numeric ratings are also a poor fit because unread or abandoned bad books rarely enter the system, and unlike books are hard to compare on a single scale.



\## Impact Scale



Impact replaces rating.



```text

None

Low

Medium

High

Transformative

```



Impact asks:



> Did this book leave a mark?



It does not ask:



> Was this book objectively good?



\## Times Read



`timesRead` is included because rereading is a strong memory signal.



Default:



```js

timesRead: 1

```



Books read more than once should be treated as unusually meaningful unless marked otherwise.



\## Themes



Themes should be a controlled vocabulary used for analytics and long-term pattern recognition.



Examples:



```text

Philosophy

Stoicism

AI

AI Risk

History

Biography

Leadership

Product Management

Religion

Science

Economics

Politics

Literature

Poetry

```



Themes answer:



> What ideas keep returning?



\## Tags



Tags are free-form memory labels.



Examples:



```text

revisit

library

gift

vacation-read

recommended

unfinished

reference

favorite

```



Tags answer:



> What context do I want to remember?



\## Notes



Notes should not be embedded directly inside the book object long term.



Preferred relationship:



```text

Book -> Notes

```



A note may eventually connect to multiple books, themes, quotes, or calendar events.



\## Quotes



Quotes should not be embedded directly inside the book object long term.



Preferred relationship:



```text

Book -> Quotes

```



A quote may eventually connect to notes, themes, and broader knowledge graph entries.



\## Future Relationship Model



Long-term direction:



```text

Book

&#x20; -> Theme

&#x20; -> Note

&#x20; -> Quote

&#x20; -> Idea

```



The eventual goal is not just a book list.



The goal is a personal knowledge archive.



\## Deferred Features



Do not build these until the core model is stable:



```text

Large-scale book import

Library integration

E-reader integration

Reading streaks

Page-count analytics

Complex knowledge graph UI

Automated recommendation engine

```



\## Immediate Next Step



Before building UI, create a small mock dataset of 5–10 books and validate whether the schema feels natural to maintain.



