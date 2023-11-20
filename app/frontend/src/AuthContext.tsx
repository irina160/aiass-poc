import React, { useState, createContext, useContext, useEffect, ReactNode } from "react";

interface User {
    email: string;
}

interface ContextValue {
    currentUser: User | null;
    login: (email: string, password: string) => boolean;
    logout: () => void;
}

const AuthContext = createContext<ContextValue | undefined>(undefined);

export function useAuth(): ContextValue {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [currentUser, setCurrentUser] = useState<User | null>(null);

    useEffect(() => {
        const user = JSON.parse(localStorage.getItem("user") || "null");
        if (user) {
            setCurrentUser(user);
        }
    }, []);

    const login = (email: string, password: string): boolean => {
        // For simplicity, we're hardcoding a single user.
        // In a real application, you'd fetch this info from a server.
        if (email === "rregendantz@kpmg.com" && password === 'H0i"qGNy:"NYS!rarE*EysyZ9^!Qy0.++bc_OPYps`/86ehGTAL+Bv@6m/?_=Jqn') {
            const user = { email };
            localStorage.setItem("user", JSON.stringify(user));
            setCurrentUser(user);
            return true;
        }
        return false;
    };

    const logout = () => {
        localStorage.removeItem("user");
        setCurrentUser(null);
    };

    const value = {
        currentUser,
        login,
        logout
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
