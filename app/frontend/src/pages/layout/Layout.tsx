import { Outlet, NavLink, Link } from "react-router-dom";

import github from "../../assets/github.svg";

import styles from "./Layout.module.css";

import { Navbar } from "@components/Navbar/Navbar";

const Layout = (): JSX.Element => {
    return (
        <div className="relative bg-background">
            <Navbar />
            <main className="">
                <Outlet />
            </main>
            <footer>
                <span className=" font-KPMGBoldItalic text-foreground hidden">
                    © 2022 KPMG AG Wirtschaftsprüfungsgesellschaft, a corporation under German law and a member firm of the KPMG global organization of
                    independent member firms affiliated with KPMG International Limited, a private English company limited by guarantee. All rights reserved.
                    The KPMG name and logo are trademarks used under license by the independent member firms of the KPMG global organization.
                </span>
            </footer>
        </div>
    );
};

//<Outlet />

export default Layout;

/*
            <div className={styles.layout}>
                <header className={styles.header} role={"banner"}>
                    <div className={styles.headerContainer}>
                        <Link to="/" className={styles.headerTitleContainer}>
                            <h1 className={styles.headerTitle}>TaxTalk</h1>
                        </Link>
                        <nav>
                            <ul className={styles.headerNavList}>
                                <li>
                                    <NavLink to="/" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                        Chat
                                    </NavLink>
                                </li>
                            </ul>
                        </nav>
                        <a className={styles.headerRightText}>Revolutionize your tax communication. Powered by passion.</a>
                    </div>
                </header>

                <Outlet />
            </div>
    */
