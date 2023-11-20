import { LogLevel, Configuration } from "@azure/msal-browser";
import { redirect } from "react-router-dom";

// cudos: https://github.com/Azure-Samples/ms-identity-ciam-javascript-tutorial/blob/main/1-Authentication/1-sign-in-react/SPA/src/authConfig.js
/**
 * TODO: Change clientID and authority to correct web App in Sandbox if available
 */
export const msalConfig: Configuration = {
    auth: {
        clientId: import.meta.env.VITE_AZURE_CLIENT_ID, //"beb5eb2b-2dae-4509-912c-6a8bc57c9c2d", // "236b2225-0285-4856-9ec7-168a9f780f00", // This is the ONLY mandatory field that you need to supply.
        authority: `https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_TENANT_ID}`, //90bd379f-df7f-40a7-b835-5a61899674db //56b70827-d607-442e-822e-329d195ec9f4", //'https://Enter_the_Tenant_Subdomain_Here.ciamlogin.com/', // Replace the placeholder with your tenant subdomain
        redirectUri: "/", // Points to window.location.origin. You must register this URI on Azure Portal/App Registration.
        postLogoutRedirectUri: "/", // Indicates the page to navigate after logout.
        navigateToLoginRequestUrl: false, // If "true", will navigate back to the original request location before processing the auth code response.
        clientCapabilities: ["CP1"]
    },
    cache: {
        cacheLocation: "sessionStorage", // Configures cache location. "sessionStorage" is more secure, but "localStorage" gives you SSO between tabs.
        storeAuthStateInCookie: false // Set this to "true" if you are having issues on IE11 or Edge
    },
    system: {
        loggerOptions: {
            loggerCallback: (level: number, message: string, containsPii: boolean) => {
                if (containsPii) {
                    return;
                }
                switch (level) {
                    case LogLevel.Error:
                        console.error(message);
                        return;
                    case LogLevel.Info:
                        console.info(message);
                        return;
                    case LogLevel.Verbose:
                        console.debug(message);
                        return;
                    case LogLevel.Warning:
                        console.warn(message);
                        return;
                    default:
                        return;
                }
            }
        }
    }
};
