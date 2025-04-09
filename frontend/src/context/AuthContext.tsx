import { createContext, useContext, ReactNode, useEffect, useReducer, Dispatch } from "react";
import { useAuth0, User } from "@auth0/auth0-react";
import { login } from "@/lib/api";
import { Participant } from "@/types/types"; // Import Participant type

// Define the shape of the user data returned by your backend login, if any.
// It should include a participants array if that's where the data lives.
type BackendUserData = {
  participants?: Participant[]; // Assuming participants are part of backendUser
  [key: string]: unknown; // Allow other unknown properties
};

// Define the state managed by the reducer
interface AuthState {
  user: User | undefined; // User object from Auth0
  backendUser: BackendUserData | undefined; // Data merged from your backend, including participants
  isInitialized: boolean; // Tracks if backend login/sync is complete
}

// Define the actions that can be dispatched to the reducer
type AuthAction =
  | { type: 'SET_AUTH0_USER'; payload: User | undefined }
  | { type: 'SET_BACKEND_USER'; payload: BackendUserData }
  | { type: 'UPDATE_BACKEND_USER'; payload: Partial<BackendUserData> }
  | { type: 'INITIALIZE_COMPLETE' }
  | { type: 'RESET' }
  // Participant specific actions
  | { type: 'ADD_PARTICIPANT'; payload: Participant }
  | { type: 'UPDATE_PARTICIPANT'; payload: Participant }
  | { type: 'DELETE_PARTICIPANT'; payload: string }; // Payload is participant ID

// Initial state for the reducer
const initialState: AuthState = {
  user: undefined,
  backendUser: undefined,
  isInitialized: false,
};

// Helper to safely get participants array from state
const getParticipants = (state: AuthState): Participant[] => {
  return state.backendUser?.participants || [];
};

// The reducer function to handle state updates based on actions
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_AUTH0_USER':
      return { ...state, user: action.payload };
    case 'SET_BACKEND_USER':
      // Ensure participants array exists if backendUser is set
      const backendUserWithParticipants = action.payload
        ? { ...action.payload, participants: action.payload.participants || [] }
        : undefined;
      return { ...state, backendUser: backendUserWithParticipants };
    case 'UPDATE_BACKEND_USER': {
      const currentBackendUser = state.backendUser || {};
      const updatedBackendUser = { ...currentBackendUser, ...action.payload };
      // Ensure participants array exists after update
      if (!updatedBackendUser.participants) {
        updatedBackendUser.participants = [];
      }
      return {
        ...state,
        backendUser: updatedBackendUser as BackendUserData,
      };
    }
    case 'INITIALIZE_COMPLETE':
      return { ...state, isInitialized: true };
    case 'RESET':
      return initialState;

    // Participant Reducer Logic
    case 'ADD_PARTICIPANT': {
      if (!state.backendUser) return state; // Should not happen if initialized
      const participants = getParticipants(state);
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          participants: [...participants, action.payload],
        },
      };
    }
    case 'UPDATE_PARTICIPANT': {
      if (!state.backendUser) return state;
      const participants = getParticipants(state);
      const updatedParticipants = participants.map(p =>
        p.id === action.payload.id ? action.payload : p
      );
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          participants: updatedParticipants,
        },
      };
    }
    case 'DELETE_PARTICIPANT': {
      if (!state.backendUser) return state;
      const participants = getParticipants(state);
      const filteredParticipants = participants.filter(p => p.id !== action.payload);
      return {
        ...state,
        backendUser: {
          ...state.backendUser,
          participants: filteredParticipants,
        },
      };
    }

    default:
      // Ensure exhaustive check if using TypeScript 4.9+
      // const _exhaustiveCheck: never = action;
      return state;
  }
};

// Define the shape of the context value
interface AuthContextType {
  state: AuthState;
  dispatch: Dispatch<AuthAction>;
  isAuthenticated: boolean; // Directly from useAuth0
  isLoading: boolean;       // Directly from useAuth0
  loginWithRedirect: () => void; // Directly from useAuth0
  logout: () => void;           // Custom logout wrapping Auth0 logout
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// The provider component that wraps the application
export function AuthProvider({ children }: { children: ReactNode }) {
  const {
    isAuthenticated,
    isLoading,
    user: auth0User, // Rename to avoid conflict with state.user
    loginWithRedirect,
    logout: auth0Logout, // Rename to avoid conflict
    getIdTokenClaims,
  } = useAuth0();

  const [state, dispatch] = useReducer(authReducer, initialState);

  // Effect to sync Auth0 state and initialize backend session
  useEffect(() => {
    const initializeUser = async () => {
      if (isLoading) return; // Wait until Auth0 is done loading

      if (isAuthenticated && auth0User && !state.isInitialized) {
        dispatch({ type: 'SET_AUTH0_USER', payload: auth0User });
        localStorage.setItem("user", JSON.stringify(auth0User)); // Keep storing Auth0 user for quick access if needed

        try {
          const idTokenClaims = await getIdTokenClaims();
          const idToken = idTokenClaims?.__raw;

          if (idToken) {
            localStorage.setItem("idToken", idToken); // Store token

            // Call backend login endpoint
            const response = await login(); // Get the full Axios response
            const backendData: BackendUserData = response.data || {}; // Extract data

            // Ensure participants array exists in fetched data
            if (!backendData.participants) {
              backendData.participants = [];
            }

            // Dispatch SET_BACKEND_USER which now handles participants initialization
            dispatch({ type: 'SET_BACKEND_USER', payload: backendData });
            dispatch({ type: 'INITIALIZE_COMPLETE' }); // Mark initialization as complete

          } else {
             console.error("Could not get ID token.");
             // Handle token error, maybe logout?
          }
        } catch (error) {
          console.error("Error initializing user session:", error);
          // Handle initialization error, maybe logout?
        }
      } else if (!isAuthenticated && !isLoading) {
        // If user is not authenticated and Auth0 is not loading, reset state
        dispatch({ type: 'RESET' });
        localStorage.removeItem("idToken");
        localStorage.removeItem("user");
      }
    };

    initializeUser();
  }, [isAuthenticated, isLoading, auth0User, getIdTokenClaims, state.isInitialized, dispatch]);

  // Custom logout function to clear state and call Auth0 logout
  const logout = () => {
    dispatch({ type: 'RESET' });
    localStorage.removeItem("idToken");
    localStorage.removeItem("user");
    auth0Logout({ logoutParams: { returnTo: window.location.origin } });
  };

  return (
    <AuthContext.Provider
      value={{
        state,
        dispatch,
        isAuthenticated,
        isLoading,
        loginWithRedirect,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to consume the context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}