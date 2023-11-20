import React, { useState, useEffect, Suspense } from "react";
import { ReactComponent as KPMG } from "@assets/kpmg.svg";
import { NavLink } from "react-router-dom";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { UserSkeleton } from "@components/Skeletons/UserSkeleton";
import { useUser } from "@hooks/useUser";
import { AccountInfo, EventMessage, EventType } from "@azure/msal-browser";
import { ReactComponent as ArrowBack } from "@assets/ArrowBack.svg";
//import { User } from "@components/User/User";

const User = React.lazy(() => import("@components/User/User").then(module => ({ default: module.User })));

interface NavbarProps {}

export const Navbar = (props: NavbarProps): JSX.Element => {
    return (
        <header className="p-1 h-[3.5rem] pl-5 pr-5 flex items-center justify-between bg-background top-0 sticky z-10">
            <NavLink to={"/"} className="" title="Navigate Back">
                <KPMG className="fill-primary h-12 hidden" />
                <ArrowBack className="text-primary h-12 " />
            </NavLink>
            <Suspense fallback={<UserSkeleton />}>
                <User />
            </Suspense>
        </header>
    );
};
