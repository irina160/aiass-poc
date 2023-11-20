import { EventMessage, EventType } from "@azure/msal-browser";
import { useMsal } from "@azure/msal-react";
import { UserSkeleton } from "@components/Skeletons/UserSkeleton";
import { useUser } from "@hooks/useUser";
import { useEffect, useState, useRef } from "react";
import { ReactComponent as Logout } from "@assets/Logout.svg";
import { ReactComponent as Theme } from "@assets/Theme.svg";

interface UserProps {}

export const User = (props: UserProps) => {
    const [tokenAvailable, setTokenAvailable] = useState<boolean>(false);
    const [userDone, setUserDone] = useState<boolean>(false);
    const [openCollapsible, setOpenCollapsible] = useState<boolean>(false);
    const { instance, accounts } = useMsal();
    const { user, login } = useUser();
    const userRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        loginUser();
        setTokenAvailable(true);
    }, []);

    useEffect(() => {
        const clickOutside = (event: MouseEvent) => {
            if (userRef.current && !userRef.current.contains(event.target as Node)) setOpenCollapsible(false);
        };
        document.documentElement.addEventListener("click", clickOutside);
        return () => {
            document.documentElement.removeEventListener("click", clickOutside);
        };
    }, []);

    /**
     * TODO: This may be ThemeProvider with several themes. Currently only light and dark. Default light. User preference is not used
     */

    const loginUser = async () => {
        login({
            name: accounts[0].name as string,
            role: "Admin",
            theme: "Light",
            language: window.navigator.language
        });
    };

    const logoutUser = () => {
        instance.logout();
    };

    /**
     * TODO: See TODO above
     */

    const toggleTheme = () => {
        window.document.documentElement.classList.toggle("dark");
        //document.getElementById("root")?.classList.toggle("dark");
    };

    if (!tokenAvailable) return <UserSkeleton />;

    return (
        <>
            <div className="flex flex-row items-center gap-2 relative" ref={userRef}>
                <div
                    className="flex items-center group hover:bg-secondary hover:cursor-pointer rounded-md"
                    onClick={() => setOpenCollapsible(!openCollapsible)}
                >
                    <div className=" rounded-full p-2 text-background bg-primary">
                        {user.name.split(" ")[0].slice(0, 1) + user.name.split(" ").slice(-1)[0].slice(0, 1)}
                    </div>
                    <div className=" p-1 text-foreground">
                        <div>{user.name}</div>
                        <div>{user.role}</div>
                    </div>
                    <div
                        className={`relative w-4 h-4 after:right-0 after:top-1/4 after:content-[' '] after:absolute after:border-l-transparent after:border-l-8 after:border-r-transparent after:border-r-8 after:border-t-8 after:border-t-primary after:transition-transform ${
                            openCollapsible ? "after:-rotate-180" : "after:rotate-0"
                        } `}
                    ></div>
                </div>
                <ul
                    className={`absolute w-full h-fit bg-background top-full transition-opacity rounded-md ${
                        openCollapsible ? " visible opacity-100" : "opacity-0 collapse"
                    }`}
                >
                    <li className=" cursor-pointer p-1 pl-2 hover:bg-secondary rounded-md flex flex-row items-center text-foreground" onClick={logoutUser}>
                        <Logout className="  w-6" /> Logout
                    </li>
                    <li className=" cursor-pointer p-1 pl-2 hover:bg-secondary rounded-md flex flex-row items-center text-foreground" onClick={toggleTheme}>
                        <Theme className=" w-6" /> Toggle Theme
                    </li>
                </ul>
            </div>
        </>
    );
};
