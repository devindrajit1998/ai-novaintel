import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { apiClient, User } from '@/lib/api';
import { systemWebSocket } from '@/lib/systemWebSocket';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string, fullName: string, role?: string) => Promise<User>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Function to restore user from token
  const restoreUserFromToken = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      setUser(null);
      return;
    }

    // First, try to fetch full user profile from API (most reliable)
    try {
      const fullUser = await apiClient.getCurrentUser();
      setUser(fullUser);
      localStorage.setItem('user_data', JSON.stringify(fullUser));
      setIsLoading(false);
      return;
    } catch (apiError) {
      // API call failed, fall back to token decoding
      console.warn('Failed to fetch user profile, falling back to token decode:', apiError);
    }

    // Try to decode token to get user info
    try {
      // Check if token is a valid JWT (has 3 parts separated by dots)
      const tokenParts = token.split('.');
      if (tokenParts.length !== 3) {
        console.error('Invalid token format');
        setIsLoading(false);
        return; // Don't clear tokens - might be a valid Supabase token
      }

      const payload = JSON.parse(atob(tokenParts[1]));
      
      // Check if token is expired (exp is in seconds, Date.now() is in milliseconds)
      const isExpired = payload.exp && payload.exp * 1000 < Date.now();
      
      if (isExpired) {
        // Token expired, try to refresh
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          try {
            const refreshed = await apiClient.refreshAccessToken(refreshToken);
            localStorage.setItem('access_token', refreshed.access_token);
            localStorage.setItem('refresh_token', refreshed.refresh_token);
            
            // Try to fetch full profile with new token
            try {
              const fullUser = await apiClient.getCurrentUser();
              setUser(fullUser);
              localStorage.setItem('user_data', JSON.stringify(fullUser));
              setIsLoading(false);
              return;
            } catch (e) {
              // Fall back to token decode
              const newTokenParts = refreshed.access_token.split('.');
              if (newTokenParts.length === 3) {
                const newPayload = JSON.parse(atob(newTokenParts[1]));
                if (newPayload.email) {
                  const userData = {
                    id: newPayload.sub || newPayload.user_id || newPayload.id || '1',
                    email: newPayload.email,
                    full_name: newPayload.full_name || newPayload.name || newPayload.email.split('@')[0],
                    role: newPayload.role || 'pre_sales_analyst',
                  };
                  setUser(userData);
                  localStorage.setItem('user_data', JSON.stringify(userData));
                }
              }
            }
          } catch (error) {
            // Refresh failed - don't clear tokens immediately, let backend verify
            console.error('Token refresh failed:', error);
            // Keep tokens and let backend verify - might be a valid token
            // Only clear if we're certain it's invalid
          }
        } else {
          // No refresh token, but keep access token - let backend verify
          console.warn('No refresh token, but access token exists');
        }
      } else {
        // Token is valid (not expired), set user from token
        if (payload.email) {
          const userData = {
            id: payload.sub || payload.user_id || payload.id || '1',
            email: payload.email,
            full_name: payload.full_name || payload.name || payload.email.split('@')[0],
            role: payload.role || 'pre_sales_analyst',
          };
          setUser(userData);
          localStorage.setItem('user_data', JSON.stringify(userData));
        } else {
          // Token doesn't have email, but it's valid - restore from stored data
          const storedUserData = localStorage.getItem('user_data');
          if (storedUserData) {
            try {
              const userData = JSON.parse(storedUserData);
              setUser(userData);
            } catch (e) {
              console.error('Failed to parse stored user data:', e);
            }
          }
        }
      }
    } catch (e) {
      // If token decode fails, don't clear tokens immediately
      // Supabase tokens might have different format
      console.warn('Failed to decode token:', e);
      // Try to restore from stored user data
      const storedUserData = localStorage.getItem('user_data');
      if (storedUserData) {
        try {
          const userData = JSON.parse(storedUserData);
          setUser(userData);
          // Keep tokens - backend will verify
        } catch (parseError) {
          console.error('Failed to parse stored user data:', parseError);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Check authentication status
  const checkAuth = useCallback(async () => {
    setIsLoading(true);
    await restoreUserFromToken();
  }, [restoreUserFromToken]);

  useEffect(() => {
    // Restore session on mount
    const restoreSession = async () => {
      setIsLoading(true);
      
      // First, check if token exists at all
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }
      
      // Try to restore from localStorage first (instant UI)
      const storedUserData = localStorage.getItem('user_data');
      if (storedUserData) {
        try {
          const userData = JSON.parse(storedUserData);
          setUser(userData);
          // User is restored immediately, but we still verify token and fetch fresh data
        } catch (e) {
          // Invalid stored data, clear it
          localStorage.removeItem('user_data');
        }
      }
      
      // Then verify token and fetch fresh user profile (including role)
      // This ensures role is always up-to-date
      try {
        const fullUser = await apiClient.getCurrentUser();
        setUser(fullUser);
        localStorage.setItem('user_data', JSON.stringify(fullUser));
        
        // Connect to system WebSocket for real-time updates
        if (fullUser.id) {
          const userId = parseInt(fullUser.id);
          systemWebSocket.connect(userId).catch((error) => {
            console.error("Failed to connect system WebSocket:", error);
          });
        }
        
        setIsLoading(false);
      } catch (error) {
        // If API call fails, fall back to token restoration
        await restoreUserFromToken();
      }
    };
    
    restoreSession();
  }, [restoreUserFromToken]);

  // Listen for storage changes (e.g., from other tabs)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'access_token') {
        if (e.newValue) {
          restoreUserFromToken();
        } else {
          setUser(null);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [restoreUserFromToken]);

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.login({ email, password });
      // Tokens are stored by apiClient in localStorage
      
      // Fetch full user profile to get role and other details
      try {
        const fullUser = await apiClient.getCurrentUser();
        // Update state and localStorage with complete user data
        setUser(fullUser);
        localStorage.setItem('user_data', JSON.stringify(fullUser));
        
        // Connect to system WebSocket for real-time updates
        if (fullUser.id) {
          const userId = parseInt(fullUser.id);
          systemWebSocket.connect(userId).catch((error) => {
            console.error("Failed to connect system WebSocket:", error);
          });
        }
        
        setIsLoading(false);
        return fullUser;
      } catch (profileError) {
        // If fetching profile fails, decode token to get basic info
        try {
          const token = response.access_token;
          const payload = JSON.parse(atob(token.split('.')[1]));
          const userData = {
            id: payload.sub || payload.user_id || payload.id || '1',
            email: payload.email || email,
            full_name: payload.full_name || payload.name || email.split('@')[0],
            role: payload.role || 'pre_sales_analyst',
          };
          
          // Update state and localStorage synchronously before returning
          setUser(userData);
          localStorage.setItem('user_data', JSON.stringify(userData));
          
          // Connect to system WebSocket for real-time updates
          if (userData.id) {
            const userId = parseInt(userData.id);
            systemWebSocket.connect(userId).catch((error) => {
              console.error("Failed to connect system WebSocket:", error);
            });
          }
          
          setIsLoading(false);
          return userData;
        } catch (e) {
          // If decode fails, use email-based fallback
          const userData = {
            id: '1',
            email,
            full_name: email.split('@')[0],
            role: 'pre_sales_analyst',
          };
          setUser(userData);
          localStorage.setItem('user_data', JSON.stringify(userData));
          setIsLoading(false);
          return userData;
        }
      }
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const register = async (email: string, password: string, fullName: string, role: string = "pre_sales_analyst") => {
    try {
      const user = await apiClient.register({ email, password, full_name: fullName, role });
      // Don't auto-login if email verification is required
      // Return user info so caller can handle verification message
      return user;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    apiClient.logout();
    systemWebSocket.disconnect();
    setUser(null);
    localStorage.removeItem('user_data');
  };

  // Check if authenticated - prioritize token existence over user state
  // This prevents false negatives during initial load
  // During initial load, user might be null but token and stored data exist
  const token = localStorage.getItem('access_token');
  const hasStoredUser = !!localStorage.getItem('user_data');
  
  // Consider authenticated if:
  // 1. Token exists AND user state is set, OR
  // 2. Token exists AND stored user data exists (during initial load)
  // This allows authentication to persist even if React state hasn't loaded yet
  // Don't include isLoading in the check - it should be a boolean based on actual auth state
  const isAuthenticated = !!token && (!!user || hasStoredUser);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
