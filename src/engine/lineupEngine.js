function normalizeName(name) {
  return (name || "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "")
    .trim();
}

function getCardMap() {
  const saved = localStorage.getItem("stratPlayerCards1980");
  const cards = saved ? JSON.parse(saved) : [];

  const map = {};

  cards.forEach((card) => {
    map[normalizeName(card.name)] = card;
  });

  return map;
}

function parseRoster(hittersText = "") {
  return hittersText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(/\s+/);

      return {
        raw: line,
        positions: parts[0].split("/").map((p) => p.trim().toUpperCase()),
        bats: parts[1],
        defense: Number(parts[2]),
        name: parts.slice(3, parts.length - 4).join(" "),
        obpVsR: Number(parts[parts.length - 4]),
        obpVsL: Number(parts[parts.length - 3]),
        power: Number(parts[parts.length - 2]),
        speed: Number(parts[parts.length - 1]),
      };
    });
}

function getObp(player, pitcherHand) {
  return pitcherHand === "L" ? player.obpVsL : player.obpVsR;
}

function getRunningBonus(card) {
  if (!card?.running) return 0;

  const max = Number(card.running.split("-")[1]);

  if (max >= 17) return 4;
  if (max >= 15) return 2;
  if (max <= 11) return -2;

    return 0;
}

function getCardDefenseRating(player, position, card) {
  if (position === "DH") return Number(player.defense) || 5;

  const fallbackDefense = Number(player.defense) || 5;
  const defenseText = card?.defense?.toLowerCase();

  if (!defenseText) return fallbackDefense;

  const normalizedPosition = position.toLowerCase();
  const match = defenseText.match(
    new RegExp(`(^|[^a-z0-9])${normalizedPosition}-(\\d)`, "i")
  );

  if (!match) return fallbackDefense;

  return Number(match[2]) || fallbackDefense;
}
function getSmallBallBonus(card) {
  let bonus = 0;

  if (card?.hitAndRun === "A") bonus += 4;
  if (card?.hitAndRun === "B") bonus += 2;

  if (card?.stealing === "AAA") bonus += 6;
  if (card?.stealing === "AA") bonus += 5;
  if (card?.stealing === "A") bonus += 4;
  if (card?.stealing === "B") bonus += 2;

  if (card?.bunting === "A") bonus += 1.5;
  if (card?.bunting === "B") bonus += 0.75;

  return bonus;
}

function getOutcomeProfileBonus(card, park) {
  if (!card?.outcomeDescription) return 0;

  let bonus = 0;
  const profile = card.outcomeDescription.toLowerCase();

  if (park?.environment?.includes("Low")) {
    if (profile.includes("contact-heavy")) bonus += 9;
    if (profile.includes("walks")) bonus += 5;
    if (profile.includes("gap power")) bonus += 4;
    if (profile.includes("strikeout risk")) bonus -= 7;
    if (profile.includes("hr threat")) bonus -= 2;
    if (profile.includes("groundball-heavy")) bonus -= 2;
  }

  if (park?.environment === "High Power") {
    if (profile.includes("hr threat")) bonus += 7;
    if (profile.includes("gap power")) bonus += 3;
    if (profile.includes("groundball-heavy")) bonus -= 2;
  }

  if (park?.environment === "Contact Friendly") {
    if (profile.includes("contact-heavy")) bonus += 6;
    if (profile.includes("walks")) bonus += 4;
    if (profile.includes("strikeout risk")) bonus -= 4;
  }

  return bonus;
}

function getImpactBonus(player, pitcherHand, park) {
  const obp = getObp(player, pitcherHand);
  let bonus = 0;

  if (player.power >= 8) bonus += 14;
  else if (player.power >= 6) bonus += 10;
  else if (player.power >= 5) bonus += 7;
  else if (player.power <= 1) bonus -= 8;
  else if (player.power <= 2) bonus -= 5;

  if (obp >= 0.400) bonus += 10;
  else if (obp >= 0.370) bonus += 6;
  else if (obp < 0.300) bonus -= 14;
  else if (obp < 0.315) bonus -= 8;

  if (park?.environment?.includes("Low") && player.power >= 5 && obp >= 0.330) {
    bonus += 4;
  }
  const positions = player.positions || [];

  if (
    positions.includes("SS") &&
    player.power >= 3 &&
    obp >= 0.295
  ) {
    bonus += 10;
  }

  if (
    positions.includes("C") &&
    player.power >= 3 &&
    obp >= 0.310
  ) {
    bonus += 6;
  }

  if (
    positions.includes("CF") &&
    player.power >= 3 &&
    obp >= 0.310
  ) {
    bonus += 5;
  }
  return bonus;
}

function isWeakBat(player, pitcherHand) {
  return getObp(player, pitcherHand) < 0.325 && player.power <= 2;
}

function isBottomOnlyBat(player, pitcherHand) {
  return getObp(player, pitcherHand) < 0.315 && player.power <= 2;
}

function scoreBat(player, pitcherHand, park) {
  const cardMap = getCardMap();
  const card = cardMap[normalizeName(player.name)];

  const obp = getObp(player, pitcherHand);

  let score =
    obp * 100 +
    player.power * 4 +
    player.speed * 1.15 +
    getImpactBonus(player, pitcherHand, park);

  if (pitcherHand === "L") {
    if (player.bats === "R") score += 7;
    if (player.bats === "S") score += 4;
    if (player.bats === "L") score -= 4;
  }

  if (pitcherHand === "R") {
    if (player.bats === "L") score += 4;
    if (player.bats === "S") score += 3;
  }

  if (park?.environment?.includes("Low")) {
    score += player.speed * 0.75;
    score -= player.power * 0.25;
  }

  if (card) {
    score += getRunningBonus(card);
    score += getSmallBallBonus(card);
    score += getOutcomeProfileBonus(card, park);
  }

  return score;
}

function getLowRunEnvironmentDefenseAdjustment(player, position, park, defenseRating) {
  if (!park?.environment?.includes("Low")) return 0;

  let penalty = 0;

  // In Busch/Astrodome-type games, C/SS/CF defense should be treated
  // as run prevention, not cosmetic positioning.
  if (position === "C") {
    if (defenseRating >= 5) penalty -= 55;
    else if (defenseRating >= 4) penalty -= 35;
    else if (defenseRating <= 2) penalty += 8;
  }

  if (position === "SS") {
    if (defenseRating >= 4) penalty -= 45;
    else if (defenseRating <= 1) penalty += 12;
  }

  if (position === "CF") {
    if (defenseRating >= 4) penalty -= 60;
    else if (defenseRating >= 3) penalty -= 35;
    else if (defenseRating <= 2) penalty += 12;
  }

  if (position === "2B") {
    if (defenseRating >= 4) penalty -= 28;
    else if (defenseRating <= 2) penalty += 7;
  }

  // Corner outfield defense matters less than CF, but bad range can still
  // leak doubles and extra bases in low-HR tactical games.
  if (["LF", "RF"].includes(position)) {
    if (defenseRating >= 5) penalty -= 24;
    else if (defenseRating >= 4) penalty -= 14;
    else if (defenseRating <= 2) penalty += 5;
  }

  // Weak 1B defense is tolerable only if the bat clearly earns it.
  if (position === "1B" && defenseRating >= 5) {
    penalty -= player.power >= 7 ? 8 : 18;
  }

  return penalty;
}

function scorePositionFit(player, position, pitcherHand, park) {
  const cardMap = getCardMap();
  const card = cardMap[normalizeName(player.name)];
  const defenseRating = getCardDefenseRating(player, position, card);

  const batScore = scoreBat(player, pitcherHand, park);
  const defenseScore = 6 - defenseRating;

  if (position === "DH") {
    const hideBadDefenseBonus =
      defenseRating >= 5 ? 38 : defenseRating >= 4 ? 12 : 0;

    return (
      getObp(player, pitcherHand) * 135 +
      player.power * 10 +
      getImpactBonus(player, pitcherHand, park) +
      scoreBat(player, pitcherHand, park) * 0.1 +
      hideBadDefenseBonus
    );
  }

  let positionalWeight = 2;

  if (position === "C") positionalWeight = 10;
  if (position === "SS") positionalWeight = 9;
  if (position === "CF") positionalWeight = 11;
  if (position === "2B") positionalWeight = 6;
  if (position === "3B") positionalWeight = 4;

  let score =
    batScore +
    defenseScore * positionalWeight +
    getLowRunEnvironmentDefenseAdjustment(player, position, park, defenseRating);

  if (["SS", "2B"].includes(position) && defenseRating >= 4) {
    score -= 25;
  }

  if (position === "CF" && defenseRating >= 3) {
    score -= 30;
  }

  if (position === "CF" && defenseRating >= 4) {
    score -= 35;
  }

  if (position === "C" && defenseRating >= 4) {
    score -= 35;
  }

  if (position === "C" && defenseRating >= 5) {
    score -= 55;
  }

  if (["LF", "RF"].includes(position) && defenseRating >= 5) {
    score -= 25;
  }

  if (park?.environment?.includes("Low")) {
    if (["C", "SS", "CF", "2B"].includes(position)) {
      score += defenseScore * 3;
    }
  }

    return score;
}

function pickBestForPosition({ roster, usedNames, position, pitcherHand, park }) {
  const candidates = roster
    .filter((player) => !usedNames.has(player.name))
    .filter((player) => {
      if (position === "DH") return true;
      return player.positions.includes(position);
    })
    .map((player) => ({
      player,
      score: scorePositionFit(player, position, pitcherHand, park),
    }))
    .sort((a, b) => b.score - a.score);

  return candidates[0]?.player || null;
}

function improveLowRunDefense(lineup, roster, pitcherHand, park) {
  if (!park?.environment?.includes("Low")) return lineup;

  const usedNames = new Set(lineup.map((player) => player.name));
  const cardMap = getCardMap();
  const adjusted = [...lineup];

  const defensivePositions = ["C", "SS", "CF", "2B"];

  defensivePositions.forEach((position) => {
    const currentIndex = adjusted.findIndex((player) => player.fieldPos === position);
    const current = adjusted[currentIndex];

    if (!current) return;

    const currentCard = cardMap[normalizeName(current.name)];
    const currentDefenseRating = getCardDefenseRating(current, position, currentCard);
    const currentPenalty = getLowRunEnvironmentDefenseAdjustment(
      current,
      position,
      park,
      currentDefenseRating
    );

    // Only consider replacement if the current defender is materially risky.
    if (currentPenalty > -25) return;

    const candidates = roster
      .filter((player) => player.positions.includes(position))
      .filter((player) => !usedNames.has(player.name) || player.name === current.name)
      .map((player) => {
                const offensiveGap =
          scoreBat(current, pitcherHand, park) - scoreBat(player, pitcherHand, park);

        const playerCard = cardMap[normalizeName(player.name)];
        const playerDefenseRating = getCardDefenseRating(player, position, playerCard);

        const defensiveGain =
          getLowRunEnvironmentDefenseAdjustment(
            player,
            position,
            park,
            playerDefenseRating
          ) -
          getLowRunEnvironmentDefenseAdjustment(
            current,
            position,
            park,
            currentDefenseRating
          );

        return {
          player,
          netGain: defensiveGain - offensiveGap * 0.65,
        };
      })
      .sort((a, b) => b.netGain - a.netGain);

    const replacement = candidates[0];

    if (!replacement || replacement.player.name === current.name) return;

    // Require clear net gain so we do not make twitchy swaps.
    if (replacement.netGain < 12) return;

    usedNames.delete(current.name);
    usedNames.add(replacement.player.name);

    adjusted[currentIndex] = {
      ...replacement.player,
      fieldPos: position,
    };
  });

  return adjusted;
}

function optimizeBattingOrder(lineup, pitcherHand, park) {
  const remaining = [...lineup];

  const removePick = (pick) => {
    if (!pick) return null;

    const index = remaining.findIndex((p) => p.name === pick.name);

    if (index !== -1) {
      remaining.splice(index, 1);
    }

    return pick;
  };

  const pickBest = (fn) => {
    const sorted = [...remaining].sort((a, b) => fn(b) - fn(a));
    return removePick(sorted[0]);
  };

  const middleOrderPenalty = (p) => {
    let penalty = 0;

    if (isWeakBat(p, pitcherHand)) penalty -= 30;
    if (isBottomOnlyBat(p, pitcherHand)) penalty -= 45;
    if (p.power <= 2) penalty -= 16;
    if (getObp(p, pitcherHand) < 0.315) penalty -= 12;

    return penalty;
  };

  const impactBatBoost = (p) => {
    let boost = 0;
    const obp = getObp(p, pitcherHand);

    if (p.power >= 8) boost += 18;
    else if (p.power >= 6) boost += 13;
    else if (p.power >= 5) boost += 9;

    if (obp >= 0.390 && p.power >= 4) boost += 9;
    if (obp >= 0.370 && p.power >= 5) boost += 7;

    return boost;
  };

  const tableSetterBoost = (p) => {
    let boost = 0;
    const obp = getObp(p, pitcherHand);

    if (obp >= 0.400) boost += 14;
    else if (obp >= 0.370) boost += 8;

    if (p.power >= 7) boost -= 5;

    return boost;
  };

  const roleScore = {
    leadoff: (p) =>
      getObp(p, pitcherHand) * 125 +
      p.speed * 2.4 +
      scoreBat(p, pitcherHand, park) * 0.08,

    twoHole: (p) =>
      getObp(p, pitcherHand) * 160 +
      p.speed * 0.8 +
      tableSetterBoost(p) +
      scoreBat(p, pitcherHand, park) * 0.08,

    bestBat: (p) =>
      getObp(p, pitcherHand) * 125 +
      p.power * 7 +
      impactBatBoost(p) +
      middleOrderPenalty(p) +
      scoreBat(p, pitcherHand, park) * 0.18,

    cleanup: (p) =>
      getObp(p, pitcherHand) * 75 +
      p.power * 13 +
      impactBatBoost(p) +
      middleOrderPenalty(p) +
      scoreBat(p, pitcherHand, park) * 0.16,

    fifth: (p) =>
      getObp(p, pitcherHand) * 85 +
      p.power * 9 +
      impactBatBoost(p) +
      middleOrderPenalty(p) +
      scoreBat(p, pitcherHand, park) * 0.14,

    sixth: (p) =>
      getObp(p, pitcherHand) * 80 +
      p.power * 5 +
      scoreBat(p, pitcherHand, park) * 0.12 +
      (isWeakBat(p, pitcherHand) ? -25 : 0),

    bottom: (p) =>
      scoreBat(p, pitcherHand, park) +
      (isWeakBat(p, pitcherHand) ? -25 : 0) +
      (isBottomOnlyBat(p, pitcherHand) ? -20 : 0),
  };

  const order = [];

  order[0] = pickBest(roleScore.leadoff);

  order[3] = pickBest((p) => {
    let score = roleScore.cleanup(p);

    if (p.power <= 3) score -= 30;
    if (getObp(p, pitcherHand) >= 0.400 && p.power <= 3) score -= 12;

    return score;
  });

  order[1] = pickBest((p) => {
    let score = roleScore.twoHole(p);

    if (isWeakBat(p, pitcherHand)) score -= 35;
    if (p.power >= 7) score -= 5;

    return score;
  });

  order[2] = pickBest((p) => {
    let score = roleScore.bestBat(p);

    if (p.power <= 2) score -= 22;
    if (isWeakBat(p, pitcherHand)) score -= 35;

    return score;
  });

  order[4] = pickBest((p) => {
    let score = roleScore.fifth(p);

    if (p.power <= 2) score -= 25;
    if (isWeakBat(p, pitcherHand)) score -= 35;

    return score;
  });

  order[5] = pickBest(roleScore.sixth);

  const rest = remaining.sort((a, b) => roleScore.bottom(b) - roleScore.bottom(a));

  order.push(...rest);

  return order.filter(Boolean).map((player) => ({
    ...player,
    obp: getObp(player, pitcherHand),
  }));
}

export function buildCardAwareLineup({ hittersText, pitcherHand = "R", park }) {
  const roster = parseRoster(hittersText);
  const usedNames = new Set();
  const lineup = [];

  const positions = ["C", "SS", "CF", "2B", "1B", "3B", "LF", "RF", "DH"];

  positions.forEach((position) => {
    const pick = pickBestForPosition({
      roster,
      usedNames,
      position,
      pitcherHand,
      park,
    });

    if (pick) {
      usedNames.add(pick.name);

      lineup.push({
        ...pick,
        fieldPos: position,
      });
    }
  });

  const defenseAwareLineup = improveLowRunDefense(
    lineup,
    roster,
    pitcherHand,
    park
  );

  return optimizeBattingOrder(defenseAwareLineup, pitcherHand, park);
}

