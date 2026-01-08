import { createContext } from 'react';

export interface User {
    id: number;
    email: string;
    username: string;
    role: 'admin' | 'user' | 'viewer';
    is_active: boolean;
    created_at?: string;
}

export interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, username: string, password: string, role?: string) => Promise<void>;
    logout: () => void;
    isLoading: boolean;
    error: string | null;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
