import React from "react"
import ReactDOM from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import { Auth0Provider } from "@auth0/auth0-react"
import App from "./App"
import "./index.css"
import { auth0Config } from "./auth/auth0-config"
import { AuthProvider } from "./context/AuthContext"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Auth0Provider
      domain={auth0Config.domain}
      clientId={auth0Config.clientId}
      authorizationParams={auth0Config.authorizationParams}
    >
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </Auth0Provider>
  </React.StrictMode>,
)
