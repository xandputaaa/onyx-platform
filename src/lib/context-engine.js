/**
 * ONYX Context Engine v1
 * Pure, dependency-free context policy. No secrets, account credentials,
 * private messages, or financial balances should be persisted here.
 */
export const CONTEXT_DOMAINS = Object.freeze([
  "schedule", "health", "finance", "celvani", "communications", "systems"
]);

const ACTION_PERMISSIONS = Object.freeze({
  "schedule.read": "read",
  "schedule.propose": "suggest",
  "schedule.modify": "approval",
  "finance.read": "read",
  "finance.summarize": "read",
  "finance.transfer": "approval",
  "communications.read": "read",
  "communications.send": "approval",
  "celvani.analyze": "read",
  "celvani.publish": "approval",
  "systems.inspect": "read",
  "systems.connect": "approval"
});

export function createContextState() {
  return {
    version: 1,
    connections: {},
    grants: {},
    events: [],
    suggestions: []
  };
}

/**
 * Connection status alone never grants access.
 * Each source needs an explicit domain + capability grant.
 */
export function grantAccess(state, { source, domain, capabilities = [] }) {
  if (!source || !CONTEXT_DOMAINS.includes(domain)) throw new Error("Invalid context grant");
  const allowed = [...new Set(capabilities.filter(capability => Object.hasOwn(ACTION_PERMISSIONS, capability) && capability.startsWith(domain + ".")))];
  return {
    ...state,
    grants: {
      ...state.grants,
      [source]: { ...(state.grants[source] || {}), [domain]: allowed }
    }
  };
}

export function revokeAccess(state, source, domain) {
  const next = { ...(state.grants[source] || {}) };
  if (domain) delete next[domain];
  return {
    ...state,
    grants: {
      ...state.grants,
      ...(domain ? { [source]: next } : { [source]: {} })
    }
  };
}

export function authorizeAction(state, { source, domain, capability, approved = false }) {
  if (!CONTEXT_DOMAINS.includes(domain)) return { allowed: false, reason: "unknown_domain" };
  const permission = ACTION_PERMISSIONS[capability];
  if (!permission || !capability.startsWith(domain + ".")) return { allowed: false, reason: "unknown_capability" };
  if (!state.grants?.[source]?.[domain]?.includes(capability)) {
    return { allowed: false, reason: "grant_required" };
  }
  if (permission === "approval" && approved !== true) {
    return { allowed: false, reason: "explicit_approval_required" };
  }
  return { allowed: true, reason: "authorized" };
}

/** Return only context relevant to a request, with no raw secrets. */
export function selectContext(state, requestedDomains = []) {
  const domains = requestedDomains.filter(d => CONTEXT_DOMAINS.includes(d));
  return {
    version: state.version,
    domains,
    sources: Object.entries(state.grants || {})
      .filter(([, grants]) => domains.some(d => Array.isArray(grants[d]) && grants[d].length))
      .map(([source, grants]) => ({
        source,
        domains: domains.filter(d => Array.isArray(grants[d]) && grants[d].length)
      }))
  };
}

export function proposeAction(state, { domain, capability, summary }) {
  if (!CONTEXT_DOMAINS.includes(domain) || !ACTION_PERMISSIONS[capability] || !capability.startsWith(domain + ".")) {
    throw new Error("Unsupported action");
  }
  const proposal = {
    id: `proposal-${state.suggestions.length + 1}`,
    domain, capability, summary: String(summary || "").slice(0, 300),
    status: "pending"
  };
  return { ...state, suggestions: [...state.suggestions, proposal] };
}
