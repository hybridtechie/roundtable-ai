# Auth0 Setup for Roundtable AI

This guide will help you set up Auth0 authentication with Google Sign-In for the Roundtable AI application.

## 1. Create an Auth0 Account

If you don't already have an Auth0 account, sign up at [auth0.com](https://auth0.com/).

## 2. Create a New Application

1. Log in to your Auth0 dashboard
2. Navigate to "Applications" > "Applications"
3. Click "Create Application"
4. Name your application (e.g., "Roundtable AI")
5. Select "Single Page Web Applications" as the application type
6. Click "Create"

## 3. Configure Application Settings

1. In your new application settings, find the "Application URIs" section
2. Set the following URLs:
   - Allowed Callback URLs: `http://localhost:5173, http://localhost:3000` (add your production URL if needed)
   - Allowed Logout URLs: `http://localhost:5173, http://localhost:3000` (add your production URL if needed)
   - Allowed Web Origins: `http://localhost:5173, http://localhost:3000` (add your production URL if needed)
3. Scroll down and click "Save Changes"

## 4. Set Up Google as an Identity Provider

1. In the Auth0 dashboard, navigate to "Authentication" > "Social"
2. Find Google in the list and click on it
3. Toggle the switch to enable Google connections
4. You'll need to create a Google OAuth 2.0 client:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Set the application type to "Web application"
   - Add authorized JavaScript origins: `https://YOUR_AUTH0_DOMAIN`
   - Add authorized redirect URIs: `https://YOUR_AUTH0_DOMAIN/login/callback`
   - Click "Create"
5. Copy the Client ID and Client Secret from Google
6. Paste them into the respective fields in Auth0's Google connection settings
7. Click "Save"

## 5. Update Environment Variables

Update the `.env.local` file with your Auth0 credentials:

```
VITE_AUTH0_DOMAIN=your-auth0-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-auth0-client-id
VITE_AUTH0_AUDIENCE=https://your-api-identifier (optional for API access)
```

## 6. Test the Authentication

1. Start your application with `npm run dev`
2. Click the "Sign In" button in the navigation bar
3. You should be redirected to Auth0's login page
4. Select Google as the login option
5. After successful authentication, you should be redirected back to your application

## Troubleshooting

- If you encounter CORS issues, make sure your application's URL is properly added to the Allowed Web Origins in Auth0
- Check the browser console for any errors related to Auth0
- Verify that your environment variables are correctly set and accessible to your application
- Make sure your Auth0 application is of type "Single Page Web Applications"
