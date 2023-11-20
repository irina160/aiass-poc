import React, { createContext, useContext, useMemo, useState } from "react";

export interface Settings {
    id: string;
    general: GeneralSettings;
    indices: GeneralSettings;
    categories: GeneralSettings;
    chat: GeneralSettings;
    overrides: GeneralSettings;
}

export interface GeneralSettings {
    [key: string]: StandardSetting;
}

export interface StandardSetting {
    type: SettingTypes;
    name_de: string;
    name_en: string;
    description_de: string;
    description_en: string;
    values?: string[]; //TODO: Probably add new type
    default: boolean | string | number;
}

export enum SettingTypes {
    checkbox,
    radio,
    multiselect,
    "input:number",
    "input:string"
}

const SettingsContext = createContext<{ settings: Settings[]; setSettings: React.Dispatch<React.SetStateAction<Settings[]>> } | undefined>(undefined);

export const SettingsProvider = ({ children }: React.PropsWithChildren) => {
    const [settings, setSettings] = useState<Settings[]>([] as Settings[]);

    const value = useMemo(() => ({ settings, setSettings }), [settings]);

    return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (context === undefined) throw new Error("useUser must be used inside a UserProvider");
    return context;
};
