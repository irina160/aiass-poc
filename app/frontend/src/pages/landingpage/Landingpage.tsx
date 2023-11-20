import { useUser } from "@hooks/useUser";
import { LandingPageTiles } from "./LandingpageTiles";
import { Outlet, useNavigate, NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { AuthenticationError } from "../../errors";
import { useMetadata } from "@hooks/useMetadata";
import { useFetchWithMsal } from "@hooks/useFetchWithMsal";
import { useSettings } from "@hooks/useSettings";

interface LandingpageProps {}

interface Tab {
    name_de: string;
    name_en: string;
    id: string;
}

export const Landingpage = (props: LandingpageProps): JSX.Element => {
    const [tabs, setTabs] = useState<Tab[] | null>(null);
    const navigate = useNavigate();
    const { getCurrentIdToken } = useUser();
    const { setMetadata } = useMetadata();
    const { customFetch } = useFetchWithMsal();
    const { settings, setSettings } = useSettings();

    useEffect(() => {
        const getFromServer = async () => {
            const res = await fetch("/api/usecasetypes", {
                method: "GET",
                headers: new Headers({
                    Authorization: `Bearer ${getCurrentIdToken()}`,
                    "Content-Type": "application/json"
                })
            });
            return res;
        };
        //useFetchWithMsal()
        customFetch({ scopes: [] }, "/api/usecasetypes", { method: "GET" }).then(data => {
            setTabs(data.usecasetypes.map((itm: any) => ({ id: itm.id, name_de: itm.name_de, name_en: itm.name_en })));
            setSettings(data.usecasetypes.map((itm: { id: string; name_de: string; name_en: string; features: any }) => ({ id: itm.id, ...itm.features })));
            setMetadata(data.metadata);
        });
    }, []);

    useEffect(() => {
        if (tabs) {
            navigate(`/usecasetypes/${tabs[0].id}/indices`);
        }
    }, [tabs]);

    if (!tabs) return <div>Loading ... </div>;

    return (
        <div className="min-h-[100vh] bg-startpage-background bg-cover bg-no-repeat ">
            <div className="pl-[15%] pr-[15%] pt-20 pb-20">
                <h1 className="font-KPMGBold text-white text-5xl">KPMG AI UseCases</h1>
                <div className="flex flex-row justify-between bg-background rounded-md mt-2 mb-2">
                    {tabs.map((tab: Tab, idx: number) => {
                        return (
                            <NavLink
                                to={`/usecasetypes/${tab.id}/indices`}
                                className={({ isActive }) =>
                                    `flex-1 box-border text-center rounded-md p-1 ${isActive ? "bg-primary text-background" : " text-foreground"}`
                                }
                                key={tab.name_en + idx}
                                id={tab.id}
                            >
                                {tab.name_en}
                            </NavLink>
                        );
                    })}
                </div>
                <Outlet />
            </div>
        </div>
    );
};

/*<LandingPageTiles name={"ChatGPT"} description={"This is the ChatGPT-Usecase"} logo={"../../assets/Chatbot.svg"} link={"/chat"} />
                    <LandingPageTiles
                        name={"Another"}
                        description={
                            "This is the ChatGPT-Usecase with some really long text and even more text just for testing purposes. Now even longer i added something new"
                        }
                        logo={"../../assets/Robot.svg"}
                        link={"/chat"}
                    />
                    <LandingPageTiles name={"ChatGPT"} description={"This is the ChatGPT-Usecase"} logo={"../../assets/Robot.svg"} link={"/chat"} />
                    <LandingPageTiles
                        name={"Another"}
                        description={
                            "This is the ChatGPT-Usecase with some really long text and even more text just for testing purposes. Now even longer i added something new"
                        }
                        logo={"../../assets/Robot.svg"}
                        link={"/chat"}
                    />
                    
                    <div className="grid grid-cols-dynamic_250 gap-8 auto-rows-[1fr] pt-5">
                    <Outlet />
                </div>
                    */
