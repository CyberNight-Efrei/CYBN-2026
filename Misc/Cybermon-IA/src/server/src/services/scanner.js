import { config } from "../config.js";

export async function selectScanner() {
  const backup = config.mlServiceUrl.replace(/\/$/, "");
  const primary = config.mlPrimaryUrl.replace(/\/$/, "");
  if (!primary || primary === backup) return backup;
  try {
    const response = await fetch(`${primary}/health`, {
      signal: AbortSignal.timeout(config.mlHealthTimeoutMs),
      redirect: "error",
    });
    if (!response.ok) return backup;
    const health = await response.json();
    if (
      health.ok === true && health.model === config.model.id &&
      health.revision === config.model.revision && health.jobApiVersion === 1 &&
      health.generation?.numBeams === config.model.generation.numBeams &&
      health.generation?.maxNewTokens === config.model.generation.maxNewTokens &&
      health.generation?.doSample === config.model.generation.doSample
    ) return primary;
  } catch {
    // A health check contains no credentials or illustration; retry selection next import.
  }
  return backup;
}
