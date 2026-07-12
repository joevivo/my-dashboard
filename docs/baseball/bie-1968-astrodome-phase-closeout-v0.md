# BIE 1968 Astrodome Phase Closeout v0

## Status

BIE now supports a complete 1968 Astrodome draft-prep workflow.

This is draft intelligence, not an autonomous drafter.

The user remains the drafter, strategist, and final decision-maker.

## Current Capability

BIE can now parse 1968 hitter defense, build hitter and pitcher card-mechanics summaries, score Astrodome fit, build position pivots, generate legal roster scenarios, review scenario quality, produce a draft-prep report, produce a ranked draft board, produce manual interpretation buckets, and produce a draft-room cheat sheet.

## Artifact Chain

parsed card evidence -> hitter defense assignments -> hitter card mechanics -> pitcher card mechanics -> Astrodome fit and pivots -> legal roster scenarios -> scenario sanity review -> consolidated draft-prep report -> ranked draft board -> manual draft interpretation -> draft-room cheat sheet

## Draft-Room Identity

Astrodome 1968 identity: run prevention, OB pressure, up-the-middle defense, pitching depth/flexibility, and selective premium bats.

Do not build around HR-only salary.

Do not let cheap legal roster filler drive draft strategy.

## Current Draft-Room Read

Hitter A-list: Rose, Pete; Alou, Felipe; Kaline, Al; Monday, Rick; Yastrzemski, Carl.

Hitter A-list with review: Rettenmund, Merv; Freehan, Bill; Flood, Curt; Corrales, Pat; Mays, Willie; Maxvill, Dal; Mota, Manny.

Pitcher A-list: McDaniel, Lindy; Tiant, Luis; Gibson, Bob; Chance, Dean; Hoerner, Joe.

Pitcher A-list with review: Messersmith, Andy; Romo, Vicente.

## Draft-Room Rules

1. Solve CF intentionally. Do not treat a CF-4 bat as a clean CF solution.
2. Solve SS intentionally. Maxvill, Aparicio, Fregosi, and Alley are the main planned paths.
3. Build around real starter depth, not just legal starter count.
4. Draft high-leverage relief deliberately. Do not back into cheap bullpen filler.
5. Treat value pieces as late structure support, not as the foundation.

## Known Model Debt

1. Legal roster scenarios can still contain too much punt bench or cheap pitcher filler.
2. Rettenmund grades highly as a bat, but CF-4 risk means he should not be treated as a clean CF solution.
3. Salary efficiency can still distort value players and requires human review.
4. Card mechanics are not full simulation.
5. BIE does not track live draft state, taken-player updates, or draft order.

## What BIE Cannot Do Yet

BIE cannot draft autonomously, track a live draft board, react to taken players in real time, produce complete contingency trees, simulate full Strat-O-Matic outcomes, guarantee the final best roster, or replace manual strategy.

## How To Use BIE For The Actual Draft

1. Read the draft-room cheat sheet.
2. Keep the manual draft interpretation open for bucket-level alternatives.
3. Use the ranked draft board for pivots.
4. Use the position pivot board when a target is taken.
5. Use roster scenarios only as construction references, not final recommendations.
6. Keep legality rules visible.

## Recommended Draft Posture

Early: prioritize Tiant/Gibson, clean CF, Freehan, Kaline/Rose/Alou/Flood, or high-leverage RP.

Middle: lock SS, C2, bullpen leverage, and fifth usable starter.

Late: use value targets only after roster structure is solved.

If the board collapses, preserve defense and pitcher flexibility before chasing corner bats.

## UI Implications For A Future BIE Surface

A future BIE UI should expose park context, hitter target buckets, pitcher target buckets, position pivot board, scenario comparison, manual interpretation buckets, draft-room cheat sheet, legality indicators, model warnings, and known debt.

The UI should not imply autonomous drafting.

## Phase Closeout

This phase is complete when this document is committed and the repo is clean for baseball/data-baseball scope.

At that point, BIE should pause unless new draft-specific information arrives.
