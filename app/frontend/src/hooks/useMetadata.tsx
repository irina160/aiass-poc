import React, { createContext, useContext, useMemo, useState } from "react";

export interface Metadata {
    temperature: Temperature[];
    model: Model[];
}

export interface Temperature {
    id: string;
    display_name_de: string;
    display_name_en: string;
}

export interface Model {
    id: string;
    display_name_de: string;
    display_name_en: string;
}

const MetadataContext = createContext<{ metadata: Metadata; setMetadata: React.Dispatch<React.SetStateAction<Metadata>> } | undefined>(undefined);

export const MetadataProvider = ({ children }: React.PropsWithChildren) => {
    const [metadata, setMetadata] = useState<Metadata>({} as Metadata);

    const value = useMemo(() => ({ metadata, setMetadata }), [metadata]);

    return <MetadataContext.Provider value={value}>{children}</MetadataContext.Provider>;
};

export const useMetadata = () => {
    const context = useContext(MetadataContext);
    if (context === undefined) throw new Error("useUser must be used inside a UserProvider");
    return context;
};
