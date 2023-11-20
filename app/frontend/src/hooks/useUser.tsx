import React, { createContext, useContext, useMemo, useState } from "react";

export interface User {
    name: string;
    role: string;
    theme: string;
    language: string;
}

const UserContext = createContext<{ user: User; login: (userImpl: User) => void; logout: () => void; getCurrentIdToken: () => string } | undefined>(undefined);

export const UserProvider = ({ children }: React.PropsWithChildren) => {
    const [user, setUser] = useState<User>({} as User);

    const getCurrentIdToken = () => {
        const idtokenkey: string = JSON.parse(window.sessionStorage.getItem(`msal.token.keys.${import.meta.env.VITE_AZURE_CLIENT_ID}`) as string)?.idToken[0];
        const idtoken: string = JSON.parse(window.sessionStorage.getItem(idtokenkey) as string)?.secret;
        return idtoken;
    };

    const login = (userImpl: User) => {
        setUser(userImpl);
    };

    const logout = () => {
        setUser({} as User);
    };

    const value = useMemo(() => ({ user, login, logout, getCurrentIdToken }), [user]);

    return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

export const useUser = () => {
    const context = useContext(UserContext);
    if (context === undefined) throw new Error("useUser must be used inside a UserProvider");
    return context;
};
