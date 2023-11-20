import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate, useParams } from "react-router-dom";
import { useEffect, useRef, useState, forwardRef, ReactNode } from "react";
import { LandingPageTiles } from "@pages/landingpage/LandingpageTiles";
import { useUser } from "@hooks/useUser";
import { ReactComponent as Add } from "@assets/Add.svg";
import { ReactComponent as Close } from "@assets/Close.svg";
import { ReactComponent as AddOutlined } from "@assets/AddOutlined.svg";
import { ReactComponent as ArrowDown } from "@assets/ArrowDown.svg";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@components/ui/sheet";
import { Input } from "@components/ui/input";
import { Label } from "@components/ui/label";
import { Button } from "@components/ui/button";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@components/ui/accordion";
import { Textarea } from "@components/ui/textarea";
import { Slider } from "@components/ui/slider";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator } from "@components/ui/dropdown-menu";
import { useMetadata, Temperature, Model } from "@hooks/useMetadata";
import { RadioGroup, RadioGroupItem } from "@components/ui/radio-group";
import { useFetchWithMsal } from "@hooks/useFetchWithMsal";
import { Settings, useSettings } from "@hooks/useSettings";

interface CreateIndexProps {
    onOpenModal: () => void;
}

export const CreateIndex = (props: CreateIndexProps) => {
    return (
        <Link to={`${location.pathname}/create`} className={"p-6 rounded-md bg-background hover:bg-accent group"} onClick={() => props.onOpenModal()}>
            <div className="relative after:content-[''] after:absolute after:-top-[2px] after:w-10 after:bg-primary after:h-[2px] after:left-0 group-hover:text-accent-foreground font-sans text-foreground">
                Create an Index
            </div>
            <div className="flex items-center flex-col group-hover:text-accent-foreground font-sans gap-4 text-bg-foreground">
                <Add />
                <div>Add an Index</div>
            </div>
        </Link>
    );
};

interface UseCaseTypeProps {
    id: string;
    description_de: string;
    description_en: string;
    name_de: string;
    name_en: string;
    logo: string;
    handleEdit: () => void;
    handleDelete: () => void;
}

export const UseCaseType = (props: UseCaseTypeProps) => {
    const { settings } = useSettings();
    const { usecasetypeid } = useParams();
    return (
        <LandingPageTiles
            title={props.name_en}
            description={props.description_en}
            link={`${location.pathname}/${props.id}/categories`}
            id={props.id}
            handleEdit={props.handleEdit}
            handleDelete={props.handleDelete}
            disableDeleteButton={settings.filter((itm: Settings) => itm.id === usecasetypeid)[0].indices["allowDeleteIndex"].default ? false : true}
            disableEditButton={settings.filter((itm: Settings) => itm.id === usecasetypeid)[0].indices["allowEditIndex"].default ? false : true}
        />
    );
};

export const convertToBase64 = async (file_: File): Promise<string | ArrayBuffer | null> => {
    return new Promise((resolve, reject) => {
        const fileReader = new FileReader();
        fileReader.onload = () => {
            resolve(fileReader.result);
        };
        fileReader.onerror = error => {
            reject(error);
        };
        fileReader.readAsDataURL(file_);
    });
};

export interface IDocTemplate {
    id: string;
    name: string;
    data?: string;
}

export interface ICategory {
    id: string;
    name_en: string;
    name_de: string;
    description_de: string;
    description_en: string;
    system_prompt: string;
    temperature: Temperature["id"];
    model: Model["id"];
    files: IDocTemplate[];
}

export interface Index {
    id: string;
    name_en: string;
    name_de: string;
    description_de: string;
    description_en: string;
    logo: string;
    categories?: ICategory[];
}

export const CategoryTemplate = (props: { no: number; id: string; removeCategory: (id: string) => void }) => {
    const [expandableOpen, setExpandableOpen] = useState<boolean>(true);
    const { metadata } = useMetadata();

    const toggleExpandable = () => {
        setExpandableOpen(!expandableOpen);
    };
    return (
        <>
            <div className="flex flex-col border-b">
                <div className="flex flex-row justify-between">
                    <div className="flex flex-row gap-2 items-center ">
                        <ArrowDown
                            className={`text-foreground hover:cursor-pointer rounded-md transition-all ${expandableOpen ? "rotate-180" : "rotate-0"}`}
                            onClick={toggleExpandable}
                        />
                        <span>Category {props.no + 1}</span>
                    </div>
                    <Button className=" text-xs underline" variant={"ghost"} type="button" onClick={() => props.removeCategory(props.id)}>
                        Remove
                    </Button>
                </div>
                <div
                    className={`flex flex-col gap-2 transition-all overflow-hidden  ${
                        expandableOpen ? " animate-accordion-down" : " animate-accordion-up max-h-0"
                    }`}
                >
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_name_de_cat_${props.id}`}>*Name DE</Label>
                            <Input id={`input_name_de_cat_${props.id}`} type="text" required placeholder="Name DE" name={`category<${props.id}>:name_de`} />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_name_en_cat_${props.id}`}>*Name EN</Label>
                            <Input id={`input_name_en_cat_${props.id}`} type="text" required placeholder="Name EN" name={`category<${props.id}>:name_en`} />
                        </div>
                    </div>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_description_de_cat_${props.id}`}>*Description DE</Label>
                            <Textarea
                                id={`input_description_de_cat_${props.id}`}
                                required
                                placeholder="Description DE"
                                name={`category<${props.id}>:description_de`}
                            />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_description_en_cat_${props.id}`}>*Description EN</Label>
                            <Textarea
                                id={`input_description_en_cat_${props.id}`}
                                required
                                placeholder="Description EN"
                                name={`category<${props.id}>:description_en`}
                            />
                        </div>
                    </div>
                    <div className="flex flex-row justify-between gap-4">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_system_prompt_cat_${props.id}`}>System Prompt</Label>
                            <Textarea id={`input_system_prompt_cat_${props.id}`} placeholder="System Prompt" name={`category<${props.id}>:system_prompt`} />
                        </div>
                        <div className="flex flex-col gap-1">
                            <Label>Temperature</Label>
                            <RadioGroup defaultValue="precise">
                                {metadata.temperature.map((temp: Temperature) => {
                                    return (
                                        <div className="flex items-center space-x-2" key={temp.id}>
                                            <RadioGroupItem value={temp.display_name_en} id={`cat_${props.id}_temp_${temp.id}`} />{" "}
                                            <Label htmlFor={`cat_${props.id}_temp_${temp.id}`}>{temp.display_name_en}</Label>
                                        </div>
                                    );
                                })}
                            </RadioGroup>
                        </div>
                        <div className="flex flex-col gap-1">
                            <Label>Model</Label>
                            <RadioGroup defaultValue="gpt-3.5-turbo">
                                {metadata.model.map((mod: Model) => {
                                    return (
                                        <div className="flex items-center space-x-2" key={mod.id}>
                                            <RadioGroupItem value={mod.display_name_en} id={`cat_${props.id}_temp_${mod.id}`} />{" "}
                                            <Label htmlFor={`cat_${props.id}_temp_${mod.id}`}>{mod.display_name_en}</Label>
                                        </div>
                                    );
                                })}
                            </RadioGroup>
                        </div>
                    </div>
                    <div className="flex flex-col gap-1">
                        <Label htmlFor={`file_for_${props.id}`}>*File</Label>
                        <Input id={`file_for_${props.id}`} type="file" accept="application/pdf" multiple required name={`category<${props.id}>:files`} />
                    </div>
                </div>
            </div>
        </>
    );
};

interface UseCaseTypesPageProps {}

// TODO: Add Delete Index in Frontend

export const UseCaseTypesPage = (props: UseCaseTypesPageProps) => {
    const [useCaseTypes, setUseCaseTypes] = useState<Index[] | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [waitingForUpload, setWaitingForUpload] = useState<boolean>(false);
    const [waitingForDelete, setWaitingForDelete] = useState<boolean>(false);
    const [openEditSheet, setOpenEditSheet] = useState<boolean>(false);
    const [openCreateModal, setOpenCreateModal] = useState<boolean>(false);
    const [editIndexElement, setEditIndexElement] = useState<Index>({} as Index);
    const [openDropdownMenu, setOpenDropdownMenu] = useState<boolean>(false);
    const [openModal, setOpenModal] = useState<boolean>(false);
    const [categories, setCategories] = useState<ICategory[]>([] as ICategory[]);
    const location = useLocation();
    const { usecasetypeid } = useParams();
    const { getCurrentIdToken } = useUser();
    const divRef = useRef<HTMLDivElement>(null);
    const { metadata } = useMetadata();
    const { customFetch } = useFetchWithMsal();
    const { settings } = useSettings();
    const navigate = useNavigate();

    //TODO: Add error handling with .catch -> move to different folder and handle Server stuff there
    useEffect(() => {
        customFetch({ scopes: [] }, `/api${location.pathname}`, { method: "GET" })
            .then(data => setUseCaseTypes(data))
            .then(() => setLoading(false));
        return () => {
            setLoading(true);
        };
    }, [usecasetypeid]);

    const handleCloseModal = () => {
        setOpenCreateModal(false);
        setCategories([] as ICategory[]);
        setEditIndexElement({} as Index);
        navigate(-1);
    };

    const handleCloseEditModal = () => {
        setOpenEditSheet(false);
        setCategories([] as ICategory[]);
        setEditIndexElement({} as Index);
        navigate(-1);
    };

    const handleAddCategory = () => {
        setCategories([...categories, { id: window.crypto.randomUUID() } as ICategory]);
    };

    const handlePost = async (e: React.FormEvent<HTMLFormElement>) => {
        setWaitingForUpload(true);
        e.preventDefault();
        const event_targets = e.currentTarget.elements;
        const submit_button = document.getElementById("submit-new-index") as HTMLButtonElement;
        const formdata = new FormData(e.currentTarget, submit_button);
        for (const cat of categories) {
            const temp = metadata.temperature.filter((temp: Temperature) => {
                return (event_targets.namedItem(`cat_${cat.id}_temp_${temp.id}`) as HTMLButtonElement).dataset.state === "checked";
            })[0];
            const model = metadata.model.filter((mod: Model) => {
                return (event_targets.namedItem(`cat_${cat.id}_temp_${mod.id}`) as HTMLButtonElement).dataset.state === "checked";
            })[0];
            formdata.append(`category<${cat.id}>:temperature`, temp.id);
            formdata.append(`category<${cat.id}>:model`, model.id);
        }
        customFetch({ scopes: [] }, `/api${location.pathname.replace("/create", "")}`, {
            method: "POST",
            body: formdata
        })
            .then(data => setUseCaseTypes(data))
            .then(() => {
                setWaitingForUpload(false);
                handleCloseModal();
            });
    };

    const handlePut = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setWaitingForUpload(true);
        const index: Index = {
            id: editIndexElement.id,
            name_de: (e.currentTarget.elements.namedItem("index_name_de") as HTMLInputElement).value,
            name_en: (e.currentTarget.elements.namedItem("index_name_en") as HTMLInputElement).value,
            description_de: (e.currentTarget.elements.namedItem("index_description_de") as HTMLTextAreaElement).value,
            description_en: (e.currentTarget.elements.namedItem("index_description_en") as HTMLTextAreaElement).value,
            logo: editIndexElement.logo,
            categories: []
        };
        customFetch({ scopes: [] }, `/api${location.pathname.replace("/edit", "")}`, {
            method: "PUT",
            body: JSON.stringify(index),
            headers: new Headers({ "Content-Type": "application/json" })
        })
            .then(data => setUseCaseTypes(data))
            .then(() => {
                setWaitingForUpload(false);
                handleCloseEditModal();
            });
    };

    const handleRemoveCategory = (id: string) => {
        const index = categories.findIndex((cat: ICategory) => cat.id === id);
        categories.splice(index, 1);
        setCategories([...categories]);
    };

    const handleEdit = (id: string) => {
        setOpenEditSheet(true);
        setEditIndexElement(useCaseTypes?.filter((item: Index) => item.id === id)[0] as Index);
        navigate(location.pathname + "/edit");
    };

    const handleDelete = (id: string) => {
        setWaitingForDelete(true);
        /*
        fetch(`/api${location.pathname}`, {
            method: "DELETE",
            headers: new Headers({
                Authorization: `Bearer ${getCurrentIdToken()}`,
                "Content-Type": "application/json"
            }),
            body: JSON.stringify({ id: id })
        })
        */
        customFetch({ scopes: [] }, `/api${location.pathname}/${id}`, {
            method: "DELETE"
            //body: JSON.stringify({ id: id }),
            //headers: new Headers({ "Content-Type": "application/json" })
        })
            .then(data => setUseCaseTypes(data))
            .then(() => {
                setWaitingForDelete(false);
            });
    };

    if (loading) return <div className=" text-white">Loading...</div>;

    /**
     * TODO: Adjust  way of representing localization (new PBI)
     */
    return (
        <>
            <div className="grid grid-cols-dynamic_250_300 gap-8 auto-rows-[1fr] pt-5">
                {waitingForDelete ? (
                    <div className="absolute w-full h-full bg-secondary/60 top-0 left-0 before:w-6 before:h-6 before:content-[''] before:border-2 before:border-secondary before:border-t-primary before:rounded-full before:absolute before:animate-spinner before:top-1/2 before:left-1/2"></div>
                ) : null}
                {useCaseTypes?.map((value: Index, idx: number) => {
                    return (
                        <UseCaseType
                            {...value}
                            key={"usecasetype-" + idx}
                            handleEdit={() => handleEdit(value.id)}
                            handleDelete={() => handleDelete(value.id)}
                        />
                    );
                })}

                {settings.filter((itm: Settings) => itm.id === usecasetypeid)[0].general["allowCreationOfIndices"].default && (
                    <CreateIndex onOpenModal={() => setOpenCreateModal(true)} />
                )}
                <Outlet
                    context={[
                        openCreateModal,
                        handleCloseModal,
                        handlePost,
                        categories,
                        handleRemoveCategory,
                        handleAddCategory,
                        waitingForUpload,
                        openEditSheet,
                        handlePut,
                        handleCloseEditModal,
                        editIndexElement
                    ]}
                />
            </div>
        </>
    );
};
