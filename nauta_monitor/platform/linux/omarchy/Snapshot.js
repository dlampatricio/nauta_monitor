function parse(text) {
  if (!text || text.length > 4096) return null;
  let data;
  try {
    data = JSON.parse(text);
  } catch (_) {
    return null;
  }
  if (!data || data.version !== 1
      || (data.result !== "ok" && data.result !== "error")
      || !timestamp(data.last_attempt_at)
      || !Number.isSafeInteger(data.stale_after_seconds) || data.stale_after_seconds < 1
      || !amount(data.credit_cup, 1e12) || !amount(data.hours, 1e9)
      || !(data.account_status === null || (typeof data.account_status === "string"
        && data.account_status.length <= 256))) return null;

  if (data.last_success_at === null) {
    if (data.result !== "error" || data.credit_cup !== null || data.hours !== null
        || data.account_status !== null) return null;
  } else if (!timestamp(data.last_success_at) || data.last_success_at > data.last_attempt_at
             || data.credit_cup === null) {
    return null;
  }
  return data;
}

function timestamp(value) {
  return Number.isSafeInteger(value) && value > 0 && value <= 253402300799;
}

function amount(value, max) {
  return value === null || (Number.isFinite(value) && value >= 0 && value <= max);
}

function freshness(data, now) {
  if (!data) return "noData";
  if (data.result === "error") return data.last_success_at === null ? "errorNoData" : "error";
  const age = now - data.last_success_at;
  return age < -60 || age > data.stale_after_seconds ? "stale" : "fresh";
}

function hoursLabel(hours, formatNumber) {
  const minutes = Math.floor(hours * 60);
  const wholeHours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return formatNumber(wholeHours) + " h" + (remainder ? " " + formatNumber(remainder) + " m" : "");
}
