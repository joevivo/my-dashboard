# BIE 1968 Astrodome Wrap-Up Report v0

## Summary

This session completed the 1968 Astrodome draft-prep phase for BIE.

BIE is now positioned as draft intelligence and roster-construction support, not as an autonomous drafter.

The user remains the drafter, strategist, and final decision-maker.

## What We Built

During this phase, we built and committed the final layers of the 1968 Astrodome draft-prep workflow:

1. Manual draft interpretation.
2. Draft-room cheat sheet.
3. BIE 1968 Astrodome phase closeout document.

These sit on top of the already-built pipeline:

parsed card evidence -> hitter defense assignments -> hitter card mechanics -> pitcher card mechanics -> Astrodome fit and pivots -> legal roster scenarios -> scenario review -> draft-prep report -> ranked draft board -> manual interpretation -> draft-room cheat sheet -> phase closeout

## Final Commits From This Closeout

- 36bac94 Add 1968 Astrodome manual draft interpretation
- 6f86dbf Add 1968 Astrodome draft room cheat sheet
- d30e4aa Add 1968 Astrodome BIE phase closeout

## Draft-Room Identity

The working 1968 Astrodome identity is:

- run prevention
- OB pressure
- up-the-middle defense
- pitching depth and flexibility
- selective premium bats

The draft strategy should not be built around HR-only salary.

Cheap legal roster filler should not drive draft strategy.

## Draft List v0

### Tier 1: True Anchors

Pitchers:

1. Luis Tiant
2. Bob Gibson
3. Lindy McDaniel
4. Dean Chance
5. Joe Hoerner

Hitters:

1. Pete Rose
2. Felipe Alou
3. Al Kaline
4. Bill Freehan
5. Rick Monday
6. Carl Yastrzemski
7. Curt Flood

### Tier 2: Premium With Construction Review

- Merv Rettenmund
- Willie Mays
- Andy Messersmith
- Vicente Romo
- Dal Maxvill
- Pat Corrales
- Manny Mota

Notes:

- Rettenmund is a premium bat and OB piece, but should not be treated as a clean CF solution.
- Mays is a clean CF path, but salary requires care.
- Messersmith and Romo are strong because of flexibility and closer qualification, but walk risk requires review.
- Maxvill matters because he solves SS cleanly.
- Corrales is a strong C2/value catcher, but should not replace Freehan evaluation.
- Mota is useful as a CF/contact/value option, not as a build-around.

### Structure Targets

Clean or usable CF paths:

- Rose
- Alou
- Monday
- Flood
- Mays
- Stanley
- Mota
- Unser
- Bonds
- Reggie Smith
- Blair

Preferred SS paths:

1. Maxvill
2. Aparicio
3. Fregosi
4. Alley
5. Belanger
6. Kessinger

Catcher paths:

- Freehan
- Corrales
- Hundley
- Fernandez
- Satriano
- Etchebarren

Preferred catcher construction: Freehan plus Corrales.

Fallback catcher constructions: Freehan plus Fernandez, Corrales plus Hundley, or Corrales plus Etchebarren.

### Pitching Depth

High-priority relief and closer-qualified targets:

- McDaniel
- Hoerner
- Romo
- Wilhelm
- Hamilton
- Taylor
- Upshaw
- Locker
- Richert
- Worthington

Starter depth and rotation pool:

- Tiant
- Gibson
- Chance
- Messersmith
- Seaver
- McLain
- McNally
- McDowell
- Niekro
- Drysdale
- Siebert
- Stottlemyre

The key rule is five usable starter-endurance pitchers, not merely five legal starter labels.

## What BIE Can Do Now

BIE can now support a manual 1968 Astrodome draft by providing:

1. Role coverage.
2. Card-backed mechanics.
3. Astrodome fit scoring.
4. Position pivots.
5. Legal roster scenarios.
6. Scenario sanity review.
7. Draft-prep report.
8. Ranked draft board.
9. Manual interpretation buckets.
10. Draft-room cheat sheet.

## What BIE Cannot Do Yet

BIE cannot yet:

1. Draft autonomously.
2. Track a live draft board.
3. React to taken players in real time.
4. Build complete contingency trees.
5. Simulate full Strat-O-Matic outcomes.
6. Guarantee the final best roster.
7. Replace manual strategy.

## Known Model Debt

1. Scenario builder still creates some filler-heavy legal rosters.
2. Salary efficiency can still distort some value targets.
3. Rettenmund requires manual interpretation because CF-4 risk changes his use case.
4. Card mechanics are not a full game simulation.
5. Live draft state is not modeled.

## Recommended Pause Point

BIE development should pause here unless new draft-specific information arrives, such as draft slot, taken-player data, actual league context, or a park change.

The next practical use of BIE should be manual draft support using the draft-room cheat sheet and ranked board.

## Pivot Back To Music

After this wrap-up is committed and pushed, the next project should be Music Workbench requirements.

The Music restart point should be requirements and product-shape review before UI work.

Primary Music topics to resume:

1. Query Workbench requirements before UI.
2. Data provenance and source separation.
3. Normalized terminology.
4. Dashboard versus Workbench responsibilities.
5. Artist profile cleanup.
6. Playlist intelligence and listening-era placement.
7. Technical debt and generated-text cleanup.
