/** Server-only integration readiness checks. Never expose credential values. */
export function integrationStatus(env=process.env) {
  const googleConfigured=Boolean(env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET && env.GOOGLE_REDIRECT_URI);
  const authConfigured=Boolean(env.ONYX_SESSION_SECRET && env.ONYX_OWNER_AUTH_ENABLED==='true');
  const encryptedStoreConfigured=Boolean(env.ONYX_TOKEN_ENCRYPTION_KEY && env.DATABASE_URL);
  return {
    googleCalendar: {
      configured:googleConfigured,
      available:false,
      reason:!googleConfigured?'oauth_configuration_required':!authConfigured?'owner_auth_required':!encryptedStoreConfigured?'encrypted_storage_required':'oauth_callback_not_implemented'
    },
    ownerAuthentication:{configured:authConfigured},
    encryptedTokenStorage:{configured:encryptedStoreConfigured},
    liveConnectionsEnabled:false
  };
}
