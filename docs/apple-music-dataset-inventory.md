# Apple Music Dataset Inventory

## Purpose

This document inventories Apple Music export datasets and evaluates them for:

- Historical depth
- Identity value
- Privacy risk
- Dashboard suitability

## Dataset Inventory

| Dataset | Earliest Known | Record Count | Identity Value | Privacy Risk | Notes |
|----------|---------------|-------------|-------------|-------------|-------------|
| Music - Liked Radio Tracks.csv | 2013 | 128 | Very High | Medium | Explicit LIKE/BAN preference history |
| Music - Favorite Stations.csv | 2013 | TBD | High | Medium | Station creation, retention, and deletion behavior |
| Apple Music - Favorites.csv | 2015 | 526 | Very High | Medium | Songs, albums, and artists intentionally favorited |
| Apple Music Play Activity.csv | 2015 | 199,396 | Very High | High | Core listening history and behavioral telemetry |
| Apple Music - Feature Statistics.csv | 2025 | TBD | High | Low | Navigation and discovery behavior |
| Apple Music - Play Statistics.csv | TBD | TBD | Unknown | Low | Needs investigation |
| Apple Music - Recent Impressions.csv | TBD | TBD | Unknown | Medium | Needs investigation |
| Apple Music - Track Play History.csv | TBD | TBD | High | High | Needs investigation |
| Apple Music - Play History Daily Tracks.csv | TBD | TBD | High | High | Needs investigation |
| Identifier Information.json.zip | TBD | TBD | Low | Critical | Restricted dataset; never exposed |

## Working Principles

1. Raw Apple exports are never surfaced directly in the UI.
2. Dashboard analytics are generated only from sanitized rollups.
3. Identity-oriented metrics take priority over content-oriented metrics.
4. Privacy constraints take precedence over analytical value.
5. Metrics must justify why they matter to a person's relationship with music.

