import ReactDOM from "react-dom/client";
import { createBrowserRouter, LoaderFunctionArgs, RouterProvider, useParams } from "react-router-dom";
import { initializeIcons } from "@fluentui/react";

import "./index.css";

import Layout from "@pages/layout/Layout";
import { UserProvider } from "@hooks/useUser";
import { MsalProvider, MsalAuthenticationTemplate } from "@azure/msal-react";
import { EventType, PublicClientApplication, AccountInfo, EventMessage, InteractionType } from "@azure/msal-browser";
import { msalConfig } from "./authConfig";
import { MetadataProvider } from "@hooks/useMetadata";
import { SettingsProvider } from "@hooks/useSettings";
import { CreateIndexSheet } from "@pages/indexSheets/CreateIndexSheet";
import { EditIndexSheet } from "@pages/indexSheets/EditIndexSheet";
import { CreateCategorySheet } from "@pages/CategorySheets/CreateCategorySheet";
import { EditCategorySheet } from "@pages/CategorySheets/EditCategorySheet";
import { ChatContextPage } from "@pages/ChatContextPage/ChatContextPage";
import { Chat } from "@pages/chat/Chat";
import { useFetchWithMsal } from "@hooks/useFetchWithMsal";
import { useCallback, useMemo } from "react";

initializeIcons();

/**
 * TODO: The way this is implemented (i.e. on "/" a redirect happens to "/knowledge_management") leads to sideeffects in production mode. Adjust backend code or adjust routing.
 * Explanation: If a user visits "/" he is first authenticated using MSAL, then redirected to "/knowledge_management".
 * Since "/knowledge_management" is the "landingpage" this url would likely be the bookmark.
 * Upon visiting the page via "{url}/knowledge_management" (using for example a bookmark) a 404 Not Found error is thown because index.html is served from "/", not from "/knowledge_management"
 */

const router = createBrowserRouter([
    {
        element: (
            <MsalAuthenticationTemplate interactionType={InteractionType.Redirect} authenticationRequest={{ scopes: ["openid", "profile"] }}>
                <Layout />
            </MsalAuthenticationTemplate>
        ),
        children: [
            {
                path: "/",
                lazy: async () => {
                    let { Landingpage } = await import("@pages/landingpage/Landingpage");
                    return { Component: Landingpage };
                },
                children: [
                    {
                        path: "/usecasetypes/:usecasetypeid/indices",
                        lazy: async () => {
                            let { UseCaseTypesPage } = await import("@pages/UseCaseTypePage/UseCaseTypePage");
                            return { Component: UseCaseTypesPage };
                        },
                        children: [
                            {
                                path: "/usecasetypes/:usecasetypeid/indices/create",
                                element: <CreateIndexSheet />
                            },
                            {
                                path: "/usecasetypes/:usecasetypeid/indices/edit",
                                element: <EditIndexSheet />
                            }
                        ]
                    },
                    {
                        path: "/usecasetypes/:usecasetypeid/indices/:indexid/categories",
                        lazy: async () => {
                            let { UseCasePage } = await import("@pages/UseCasePage/UseCasePage");
                            return { Component: UseCasePage };
                        },
                        children: [
                            {
                                path: "/usecasetypes/:usecasetypeid/indices/:indexid/categories/create",
                                element: <CreateCategorySheet />
                            },
                            {
                                path: "/usecasetypes/:usecasetypeid/indices/:indexid/categories/edit",
                                element: <EditCategorySheet />
                            }
                        ]
                    }
                ]
            },
            {
                path: "/usecasetypes/:usecasetypeid/indices/:indexid/categories/:categoryid/chat",
                element: <ChatContextPage />,
                children: [
                    {
                        path: "/usecasetypes/:usecasetypeid/indices/:indexid/categories/:categoryid/chat/",
                        element: <Chat />
                    },
                    {
                        path: "/usecasetypes/:usecasetypeid/indices/:indexid/categories/:categoryid/chat/:chatid",
                        element: <Chat />
                    }
                ]
            }
        ]
    }
]);

/**
 * TODO: Maybe move interfaces to separate file
 */
interface AppProps {
    pca: PublicClientApplication;
}

const App = (props: AppProps) => {
    return (
        <MsalProvider instance={props.pca}>
            <UserProvider>
                <MetadataProvider>
                    <SettingsProvider>
                        <RouterProvider router={router} />
                    </SettingsProvider>
                </MetadataProvider>
            </UserProvider>
        </MsalProvider>
    );
};

const msalInstance = new PublicClientApplication(msalConfig);

/**
 * TODO: Maybe Refactor this (Tu comment in PBI 4080)
 */
msalInstance.initialize().then(() => {
    /**
     * TODO: Remove this. This code probably never runs because we use AuthenticationTemplate. Need to double check
     */
    // Default to using the first account if no account is active on page load
    if (!msalInstance.getActiveAccount() && msalInstance.getAllAccounts().length > 0) {
        // Account selection logic is app dependent. Adjust as needed for different use cases.
        const activeaccount: AccountInfo = msalInstance.getAllAccounts()[0] as AccountInfo;
        msalInstance.setActiveAccount(activeaccount);
    }

    // Listen for sign-in event and set active account
    msalInstance.addEventCallback((event: EventMessage) => {
        if (event.eventType === EventType.LOGIN_SUCCESS && event?.payload) {
            let account: AccountInfo | null;
            if ("homeAccountId" in event.payload) account = event?.payload as AccountInfo;
            else account = null;
            msalInstance.setActiveAccount(account);
        }
    });

    ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(<App pca={msalInstance} />);
});
