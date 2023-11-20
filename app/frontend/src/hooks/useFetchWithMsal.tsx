import { InteractionType, AuthenticationResult, SilentRequest } from "@azure/msal-browser";
import { useMsal, useMsalAuthentication } from "@azure/msal-react";
import { useCallback } from "react";
import { AuthenticationError, ServerError } from "../errors/errors";

export const useFetchWithMsal = () => {
    const { instance, accounts } = useMsal();

    const catch_and_return = async (cb: Function) => {
        const response = await cb();
        const data = await response.json();
        if (response.ok) {
            return data;
        } else {
            if (response.status == 401) {
                throw new AuthenticationError("Not authenticated");
            } else if (response.status == 500) {
                throw new ServerError(data.traceback);
            } else {
                throw new Error(data.traceback);
            }
        }
    };

    const customFetch = (msalRequest: SilentRequest, endpoint: RequestInfo | URL, init: RequestInit) =>
        catch_and_return(async () => {
            const headers = new Headers(init.headers);
            let idToken;
            // User is logged in but potentially has no token yet
            if (accounts.length > 0) {
                if ("idToken" in accounts[0]) {
                    // Token is acquired, use provided token
                    idToken = accounts[0].idToken;
                } else {
                    // Token not yet acquired. acquire token silent
                    const data: AuthenticationResult = await instance.acquireTokenSilent(msalRequest);
                    idToken = data.idToken;
                }
            }
            const bearer = `Bearer ${idToken}`;
            headers.append("Authorization", bearer);
            return fetch(endpoint, {
                ...init,
                cache: "no-cache",
                headers: headers
            });
        });

    return { customFetch: useCallback(customFetch, []) };
};
