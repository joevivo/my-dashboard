export function parseCardOutcomeProfile(rawText = "") {
  const text = rawText.toLowerCase();

  const count = (pattern) => {
    const matches = text.match(pattern);
    return matches ? matches.length : 0;
  };

  return {
    singles:
      count(/\bsingle\b/g) +
      count(/\bsi\*/g) +
      count(/\bsi\*\*/g),

    doubles:
      count(/\bdo\b/g) +
      count(/\bdo\*\*/g),

    triples:
      count(/\btr\b/g),

    homers:
      count(/\bhr\b/g) +
      count(/\bhomerun\b/g),

    walks:
      count(/\bwalk\b/g),

    hbp:
      count(/\bhbp\b/g),

    strikeouts:
      count(/\bstrikeout\b/g),

    groundballs:
      count(/\bgb\(/g) +
      count(/\bgb\w*/g),

    flyballs:
      count(/\bfly\(/g) +
      count(/\bfb\(/g),

    lineouts:
      count(/\blineout\b/g) +
      count(/\blo max\b/g),

    xChances:
      count(/\bx\b/g),
  };
}

export function describeOutcomeProfile(profile, cardType = "hitter") {
  const tags = [];
if (cardType === "pitcher") {
  if (profile.homers >= 4) tags.push("HR risk");
  if (profile.homers <= 1) tags.push("HR suppression");

  if (profile.doubles >= 4) tags.push("extra-base risk");

  if (profile.singles >= 8) tags.push("allows contact");

  if (profile.walks >= 3) tags.push("walk risk");
  if (profile.walks <= 1) tags.push("low-walk");

  if (profile.strikeouts >= 7) tags.push("strikeout arm");
  else if (profile.strikeouts >= 4) tags.push("some strikeouts");

  if (profile.groundballs >= 8) tags.push("groundball-heavy");
  if (profile.flyballs >= 8) tags.push("flyball-heavy");

  if (profile.xChances >= 9) tags.push("X-chart heavy");
  else if (profile.xChances >= 5) tags.push("X-chart involved");

  return tags.length ? tags.join(" · ") : "balanced pitcher profile";
}
  if (profile.homers >= 4) tags.push("HR threat");
if (profile.homers <= 1) tags.push("HR suppression");

if (profile.doubles >= 4) tags.push("gap power");

if (profile.singles >= 8) tags.push("contact-heavy");

if (profile.walks >= 3) tags.push("walks");
if (profile.walks <= 1) tags.push("low-walk");

if (profile.strikeouts >= 4) tags.push("strikeout risk");
if (profile.strikeouts >= 7) tags.push("strikeout arm");

if (profile.groundballs >= 8) tags.push("groundball-heavy");

if (profile.flyballs >= 8) tags.push("flyball-heavy");

if (profile.xChances >= 5) tags.push("X-chart involved");
if (profile.xChances >= 9) tags.push("X-chart heavy");

  return tags.length ? tags.join(" · ") : "balanced profile";
}