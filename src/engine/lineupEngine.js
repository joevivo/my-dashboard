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

function getSmallBallBonus(card) {
  let bonus = 0;

  if (card?.hitAndRun === "A") bonus += 4;
  if (card?.hitAndRun === "B") bonus += 2;

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
    if (profile.includes("gap power")) bonus += 3;
    if (profile.includes("strikeout risk")) bonus -= 7;
    if (profile.includes("hr threat")) bonus -= 3;
    if (profile.includes("groundball-heavy")) bonus -= 2;
  }

  if (park?.environment === "High Power") {
    if (profile.includes("hr threat")) bonus += 5;
    if (profile.includes("gap power")) bonus += 2;
    if (profile.includes("groundball-heavy")) bonus -= 2;
  }

  if (park?.environment === "Contact Friendly") {
    if (profile.includes("contact-heavy")) bonus += 6;
    if (profile.includes("walks")) bonus += 4;
    if (profile.includes("strikeout risk")) bonus -= 4;
  }

  return bonus;
}

function scoreBat(player, pitcherHand, park) {
  const cardMap = getCardMap();
  const card = cardMap[normalizeName(player.name)];

  const obp = getObp(player, pitcherHand);

  let score =
    obp * 100 +
    player.power * 4 +
    player.speed * 1.5;

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
    score += player.speed * 1.5;
    score -= player.power * 0.6;
  }

  if (card) {
    score += getRunningBonus(card);
    score += getSmallBallBonus(card);
    score += getOutcomeProfileBonus(card, park);
  }

  return score;
}

function scorePositionFit(player, position, pitcherHand, park) {
  const batScore = scoreBat(player, pitcherHand, park);
  const defenseScore = 6 - player.defense;

  if (position === "DH") {
    return (
      getObp(player, pitcherHand) * 130 +
      player.power * 8 +
      player.speed * 0.25 +
      scoreBat(player, pitcherHand, park) * 0.15
    );
  }

  let positionalWeight = 2;

  if (position === "C") positionalWeight = 10;
  if (position === "SS") positionalWeight = 9;
  if (position === "CF") positionalWeight = 11;
  if (position === "2B") positionalWeight = 6;
  if (position === "3B") positionalWeight = 4;

  let score = batScore + defenseScore * positionalWeight;

  if (["C", "SS", "2B"].includes(position) && player.defense >= 4) {
    score -= 25;
  }

  if (position === "CF" && player.defense >= 3) {
    score -= 30;
  }

  if (position === "C" && player.defense >= 4) {
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

function optimizeBattingOrder(lineup, pitcherHand, park) {
  const remaining = [...lineup];

  const pickBest = (fn) => {
    const sorted = [...remaining].sort((a, b) => fn(b) - fn(a));
    const pick = sorted[0];

    const index = remaining.findIndex((p) => p.name === pick.name);

    if (index !== -1) {
      remaining.splice(index, 1);
    }

    return pick;
  };

  const order = [];

  order[0] = pickBest(
    (p) =>
      getObp(p, pitcherHand) * 100 +
      p.speed * 3 +
      scoreBat(p, pitcherHand, park) * 0.15
  );

  order[1] = pickBest(
    (p) =>
      getObp(p, pitcherHand) * 115 +
      p.speed +
      p.power +
      scoreBat(p, pitcherHand, park) * 0.1
  );

  order[2] = pickBest(
  (p) =>
    getObp(p, pitcherHand) * 155 +
    p.power * 3 +
    scoreBat(p, pitcherHand, park) * 0.2
);

  order[3] = pickBest(
  (p) =>
    getObp(p, pitcherHand) * 120 +
    p.power * 5 +
    scoreBat(p, pitcherHand, park) * 0.2
);

  order[4] = pickBest(
    (p) =>
      getObp(p, pitcherHand) * 85 +
      p.power * 5 +
      scoreBat(p, pitcherHand, park) * 0.2
  );

  const rest = remaining.sort(
    (a, b) => scoreBat(b, pitcherHand, park) - scoreBat(a, pitcherHand, park)
  );

  order.push(...rest);

  return order.map((player) => ({
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

  return optimizeBattingOrder(lineup, pitcherHand, park);
}
