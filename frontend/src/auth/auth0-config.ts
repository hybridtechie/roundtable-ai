// Auth0 configuration
export const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN || "NotLoadedCorrectly",
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID || "NotLoadedCorrectly",
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
    scope: "openid profile email",
  },
}
