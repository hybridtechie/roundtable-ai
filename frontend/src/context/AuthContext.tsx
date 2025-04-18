import { createContext, useContext, ReactNode, useEffect, useReducer, Dispatch } from "react"
import { useAuth0, User } from "@auth0/auth0-react"
import { login, listChatSessions } from "@/lib/api"
import { Participant, Group, Meeting, LLMAccountsResponse, LLMAccountCreate, ChatSession } from "@/types/types" // Import necessary types

// Define the shape of the user data returned by your backend login, if any.
// It should include a participants array if that's where the data lives.
type BackendUserData = {
  id: string
  email: string
  name: string
  participants?: Participant[]
  groups?: Group[]
  meetings?: Meeting[] // Use Meeting type
  llmAccounts?: LLMAccountsResponse // Keep this structure
  chat_sessions?: ChatSession[] // Add chat sessions
  [key: string]: unknown
}

// Define the state managed by the reducer
interface AuthState {
  user: User | undefined // User object from Auth0
  backendUser: BackendUserData | undefined // Data merged from your backend
  isInitialized: boolean // Tracks if backend login/sync is complete
}

// Define the actions that can be dispatched to the reducer
type AuthAction =
  | { type: "SET_AUTH0_USER"; payload: User | undefined }
  | { type: "SET_BACKEND_USER"; payload: BackendUserData }
  | { type: "UPDATE_BACKEND_USER"; payload: Partial<BackendUserData> }
  | { type: "INITIALIZE_COMPLETE" }
  | { type: "RESET" }
  // Participant specific actions
  | { type: "ADD_PARTICIPANT"; payload: Participant }
  | { type: "UPDATE_PARTICIPANT"; payload: Participant }
  | { type: "DELETE_PARTICIPANT"; payload: string } // Payload is participant ID
  // Group specific actions
  | { type: "ADD_GROUP"; payload: Group }
  | { type: "UPDATE_GROUP"; payload: Group }
  | { type: "DELETE_GROUP"; payload: string } // Payload is group ID
  // Meeting specific actions
  | { type: "ADD_MEETING"; payload: Meeting }
  | { type: "UPDATE_MEETING"; payload: Meeting }
  | { type: "DELETE_MEETING"; payload: string } // Payload is meeting ID
  // LLM Account specific actions
  | { type: "ADD_LLM_ACCOUNT"; payload: LLMAccountCreate }
  | { type: "UPDATE_LLM_ACCOUNT"; payload: LLMAccountCreate }
  | { type: "DELETE_LLM_ACCOUNT"; payload: string }
  | { type: "SET_DEFAULT_LLM_ACCOUNT"; payload: string }
  // Chat Session specific actions
  | { type: "SET_CHAT_SESSIONS"; payload: ChatSession[] }
  | { type: "ADD_CHAT_SESSION"; payload: ChatSession }
  | { type: "DELETE_CHAT_SESSION"; payload: string } // Payload is session ID

// Initial state for the reducer
const initialState: AuthState = {
  user: undefined,
  backendUser: undefined,
  isInitialized: false,
}
// Helper functions to safely get arrays/objects from state
const getParticipants = (state: AuthState): Participant[] => state.backendUser?.participants || []
const getGroups = (state: AuthState): Group[] => state.backendUser?.groups || []
const getMeetings = (state: AuthState): Meeting[] => state.backendUser?.meetings || []
const getLLMAccounts = (state: AuthState): LLMAccountsResponse => state.backendUser?.llmAccounts || { default: "", providers: [] }
const getChatSessions = (state: AuthState): ChatSession[] => state.backendUser?.chat_sessions || []
// The reducer function to handle state updates based on actions
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case "SET_AUTH0_USER":
      return { ...state, user: action.payload }
    case "SET_BACKEND_USER": {
      // Ensure nested arrays/objects exist if backendUser is set
      const backendUserWithDefaults = action.payload
        ? {
            ...action.payload,
            participants: action.payload.participants || [],
            groups: action.payload.groups || [],
            meetings: action.payload.meetings || [],
            llmAccounts: action.payload.llmAccounts || { default: "", providers: [] },
            chat_sessions: action.payload.chat_sessions || [], // Initialize chat_sessions
          }
        : undefined
      return { ...state, backendUser: backendUserWithDefaults }
    }
    case "UPDATE_BACKEND_USER": {
      const currentBackendUser = state.backendUser || {}
      const updatedBackendUser = { ...currentBackendUser, ...action.payload }
      // Ensure nested arrays/objects exist after update
      if (!updatedBackendUser.participants) updatedBackendUser.participants = []
      if (!updatedBackendUser.groups) updatedBackendUser.groups = []
      if (!updatedBackendUser.meetings) updatedBackendUser.meetings = []
      if (!updatedBackendUser.llmAccounts) updatedBackendUser.llmAccounts = { default: "", providers: [] }
      if (!updatedBackendUser.chat_sessions) updatedBackendUser.chat_sessions = [] // Ensure chat_sessions exists
      return {
        ...state,
        backendUser: updatedBackendUser as BackendUserData,
      }
    }
    case "INITIALIZE_COMPLETE":
      return { ...state, isInitialized: true }
    case "RESET":
      return initialState

    // Participant Reducer Logic
    case "ADD_PARTICIPANT": {
      if (!state.backendUser) return state // Should not happen if initialized
      const participants = getParticipants(state)
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          participants: [...participants, action.payload],
        },
      }
    }
    case "UPDATE_PARTICIPANT": {
      if (!state.backendUser) return state
      const participants = getParticipants(state)
      const updatedParticipants = participants.map((p) => (p.id === action.payload.id ? action.payload : p))
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          participants: updatedParticipants,
        },
      }
    }
    case "DELETE_PARTICIPANT": {
      if (!state.backendUser) return state
      const participants = getParticipants(state)
      const filteredParticipants = participants.filter((p) => p.id !== action.payload)
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          participants: filteredParticipants,
        },
      }
    }

    // Group Reducer Logic
    case "ADD_GROUP": {
      if (!state.backendUser) return state
      const groups = getGroups(state)
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          groups: [...groups, action.payload],
        },
      }
    }
    case "UPDATE_GROUP": {
      if (!state.backendUser) return state
      const groups = getGroups(state)
      const updatedGroups = groups.map((g) => (g.id === action.payload.id ? action.payload : g))
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          groups: updatedGroups,
        },
      }
    }
    case "DELETE_GROUP": {
      if (!state.backendUser) return state
      const groups = getGroups(state)
      const filteredGroups = groups.filter((g) => g.id !== action.payload)
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          groups: filteredGroups,
        },
      }
    }

    // Meeting Reducer Logic
    case "ADD_MEETING": {
      if (!state.backendUser) return state
      const meetings = getMeetings(state)
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          meetings: [...meetings, action.payload],
        },
      }
    }
    case "UPDATE_MEETING": {
      if (!state.backendUser) return state
      const meetings = getMeetings(state)
      const updatedMeetings = meetings.map((m) => (m.id === action.payload.id ? action.payload : m))
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          meetings: updatedMeetings,
        },
      }
    }
    case "DELETE_MEETING": {
      if (!state.backendUser) return state
      const meetings = getMeetings(state)
      const filteredMeetings = meetings.filter((m) => m.id !== action.payload)
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          meetings: filteredMeetings,
        },
      }
    }

    // LLM Account Reducer Logic
    case "ADD_LLM_ACCOUNT": {
      if (!state.backendUser) return state
      const llmAccounts = getLLMAccounts(state)
      // Prevent adding duplicates if provider name already exists
      if (llmAccounts.providers.some((p) => p.provider === action.payload.provider)) {
        return state
      }
      const updatedProviders = [...llmAccounts.providers, action.payload]
      // If this is the first provider added, make it the default
      const newDefault = updatedProviders.length === 1 ? action.payload.provider : llmAccounts.default
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          llmAccounts: {
            ...llmAccounts,
            default: newDefault,
            providers: updatedProviders,
          },
        },
      }
    }
    case "UPDATE_LLM_ACCOUNT": {
      // Note: API might not support direct update, usually delete/create
      if (!state.backendUser) return state
      const llmAccounts = getLLMAccounts(state)
      const updatedProviders = llmAccounts.providers.map((p) => (p.provider === action.payload.provider ? action.payload : p))
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          llmAccounts: {
            ...llmAccounts,
            providers: updatedProviders,
          },
        },
      }
    }
    case "DELETE_LLM_ACCOUNT": {
      if (!state.backendUser) return state
      const llmAccounts = getLLMAccounts(state)
      const filteredProviders = llmAccounts.providers.filter((p) => p.provider !== action.payload)
      // If the deleted provider was the default, and there are other providers left,
      // set the first remaining provider as the new default. Otherwise, clear the default.
      let newDefault = llmAccounts.default
      if (llmAccounts.default === action.payload) {
        newDefault = filteredProviders.length > 0 ? filteredProviders[0].provider : ""
      }
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          llmAccounts: {
            ...llmAccounts,
            default: newDefault,
            providers: filteredProviders,
          },
        },
      }
    }
    case "SET_DEFAULT_LLM_ACCOUNT": {
      if (!state.backendUser) return state
      const llmAccounts = getLLMAccounts(state)
      // Ensure the provider exists before setting it as default
      if (!llmAccounts.providers.some((p) => p.provider === action.payload)) {
        return state // Provider doesn't exist
      }
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          llmAccounts: {
            ...llmAccounts,
            default: action.payload, // Set the new default
          },
        },
      }
    }

    // Chat Session Reducer Logic
    case "SET_CHAT_SESSIONS": {
      if (!state.backendUser) return state
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          chat_sessions: action.payload,
        },
      }
    }
    case "ADD_CHAT_SESSION": {
      if (!state.backendUser) return state
      const chatSessions = getChatSessions(state)
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          chat_sessions: [...chatSessions, action.payload],
        },
      }
    }
    case "DELETE_CHAT_SESSION": {
      if (!state.backendUser) return state
      const chatSessions = getChatSessions(state)
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          chat_sessions: chatSessions.filter((session) => session.id !== action.payload),
        },
      }
    }

    default:
      // const _exhaustiveCheck: never = action; // Uncomment for exhaustive checks
      return state
  }
}

// Define the shape of the context value
interface AuthContextType {
  state: AuthState
  dispatch: Dispatch<AuthAction>
  isAuthenticated: boolean // Directly from useAuth0
  isLoading: boolean // Directly from useAuth0 (Auth0 loading state)
  loginWithRedirect: () => void // Directly from useAuth0
  logout: () => void // Custom logout wrapping Auth0 logout
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// The provider component that wraps the application
export function AuthProvider({ children }: { children: ReactNode }) {
  const {
    isAuthenticated,
    isLoading: isAuth0Loading, // Rename to distinguish from component loading
    user: auth0User, // Rename to avoid conflict with state.user
    loginWithRedirect,
    logout: auth0Logout, // Rename to avoid conflict
    getIdTokenClaims,
  } = useAuth0()

  const [state, dispatch] = useReducer(authReducer, initialState)

  // Effect to sync Auth0 state and initialize backend session
  useEffect(() => {
    const initializeUser = async () => {
      if (isAuth0Loading) return // Wait until Auth0 is done loading

      if (isAuthenticated && auth0User && !state.isInitialized) {
        dispatch({ type: "SET_AUTH0_USER", payload: auth0User })
        localStorage.setItem("user", JSON.stringify(auth0User)) // Keep storing Auth0 user for quick access if needed

        try {
          const idTokenClaims = await getIdTokenClaims()
          const idToken = idTokenClaims?.__raw

          if (idToken) {
            localStorage.setItem("idToken", idToken) // Store token

            // Call backend login endpoint
            const response = await login() // Get the full Axios response
            console.log("Backend login response:", response)
            const backendData: BackendUserData = response.data || {} // Extract data

            // Fetch chat sessions
            try {
              const chatSessionsResponse = await listChatSessions()
              // Ensure all required fields are present and use _ts for timestamp
              backendData.chat_sessions = chatSessionsResponse.data.chat_sessions.map((session) => ({
                id: session.id,
                meeting_id: session.meeting_id,
                user_id: session.user_id,
                title: session.title || "",
                messages: session.messages || [],
                display_messages: session.display_messages || [],
                _ts: session._ts || Math.floor(Date.now() / 1000), // Use current timestamp if _ts is missing
                // Optional fields
                participants: session.participants || [],
                meeting_name: session.meeting_name,
                meeting_topic: session.meeting_topic,
                group_name: session.group_name,
                group_id: session.group_id,
              }))
            } catch (error) {
              console.error("Failed to fetch chat sessions:", error)
              backendData.chat_sessions = [] // Initialize as empty array on error
            }

            // localStorage.setItem("backendData", JSON.stringify(backendData))

            // Dispatch SET_BACKEND_USER which now handles defaults initialization
            dispatch({ type: "SET_BACKEND_USER", payload: backendData })
            dispatch({ type: "INITIALIZE_COMPLETE" }) // Mark initialization as complete
          } else {
            console.error("Could not get ID token.")
            // Handle token error, maybe logout?
          }
        } catch (error) {
          console.error("Error initializing user session:", error)
          // Handle initialization error, maybe logout?
        }
      } else if (!isAuthenticated && !isAuth0Loading) {
        // If user is not authenticated and Auth0 is not loading, reset state
        dispatch({ type: "RESET" })
        localStorage.removeItem("idToken")
        localStorage.removeItem("user")
        localStorage.removeItem("backendData") // Clear backend data too
        dispatch({ type: "INITIALIZE_COMPLETE" }) // Mark initialization complete even if not logged in
      }
    }

    initializeUser()
  }, [isAuthenticated, isAuth0Loading, auth0User, getIdTokenClaims, state.isInitialized, dispatch])

  // Custom logout function to clear state and call Auth0 logout
  const logout = () => {
    dispatch({ type: "RESET" })
    localStorage.removeItem("idToken")
    localStorage.removeItem("user")
    localStorage.removeItem("backendData") // Clear backend data on logout
    auth0Logout({ logoutParams: { returnTo: window.location.origin } })
  }

  return (
    <AuthContext.Provider
      value={{
        state,
        dispatch,
        isAuthenticated,
        isLoading: isAuth0Loading || !state.isInitialized, // Combine Auth0 loading and app initialization state
        loginWithRedirect,
        logout,
      }}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook to consume the context
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
