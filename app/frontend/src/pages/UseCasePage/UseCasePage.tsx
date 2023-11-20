import { NavLink, Outlet, useLocation, useNavigate, useParams } from "react-router-dom";
import { useEffect, useState, forwardRef, ReactNode } from "react";
import { LandingPageTiles } from "@pages/landingpage/LandingpageTiles";
import { ReactComponent as Add } from "@assets/Add.svg";
import { useUser } from "@hooks/useUser";
import { ICategory, IDocTemplate, convertToBase64 } from "@pages/UseCaseTypePage/UseCaseTypePage";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@components/ui/sheet";
import { Input } from "@components/ui/input";
import { Label } from "@components/ui/label";
import { Button } from "@components/ui/button";
import { Textarea } from "@components/ui/textarea";
import { Eye, Trash2, View } from "lucide-react";
import { RadioGroup, RadioGroupItem } from "@components/ui/radio-group";
import { Model, Temperature, useMetadata } from "@hooks/useMetadata";
import { useFetchWithMsal } from "@hooks/useFetchWithMsal";
import { Settings, useSettings } from "@hooks/useSettings";

interface CreateCategoryProps {
    onOpenModal: () => void;
}

export const CreateCategory = (props: CreateCategoryProps) => {
    return (
        <NavLink to={`${location.pathname}/create`} className={"p-6 rounded-md bg-background hover:bg-accent group"} onClick={() => props.onOpenModal()}>
            <div className="relative after:content-[''] after:absolute after:-top-[2px] after:w-10 after:bg-primary after:h-[2px] after:left-0 group-hover:text-accent-foreground font-sans text-foreground">
                Create a Category
            </div>
            <div className="flex items-center flex-col group-hover:text-accent-foreground font-sans gap-4 text-bg-foreground">
                <Add />
                <div>Add a Category</div>
            </div>
        </NavLink>
    );
};

interface CategoryProps {
    id: string;
    description_de: string;
    description_en: string;
    name_de: string;
    name_en: string;
    handleEdit: () => void;
    handleDelete: () => void;
}

export const Category = (props: CategoryProps) => {
    const { settings } = useSettings();
    const { usecasetypeid } = useParams();
    return (
        <LandingPageTiles
            title={props.name_en}
            description={props.description_en}
            link={`${location.pathname}/${props.id}/chat`}
            id={props.id}
            handleEdit={props.handleEdit}
            handleDelete={props.handleDelete}
            disableDeleteButton={settings.filter((itm: Settings) => itm.id === usecasetypeid)[0].categories["allowDeleteCategory"].default ? false : true}
            disableEditButton={settings.filter((itm: Settings) => itm.id === usecasetypeid)[0].categories["allowEditCategory"].default ? false : true}
        />
    );
};

interface IUpdateCategory extends ICategory {
    filesToDelete: { id: string }[];
}

interface UseCasePageProps {}

//TODO: Enhance in new PBI regarding Categories

export const UseCasePage = (props: UseCasePageProps) => {
    const [useCases, setUseCases] = useState<ICategory[] | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [waitingForUpload, setWaitingForUpload] = useState<boolean>(false);
    const [waitingForDelete, setWaitingForDelete] = useState<boolean>(false);
    const [openEditSheet, setOpenEditSheet] = useState<boolean>(false);
    const [openCreateModal, setOpenCreateModal] = useState<boolean>(false);
    const [openModal, setOpenModal] = useState<boolean>(false);
    const [editCategoryElement, setEditCategoryElement] = useState<ICategory>({} as ICategory);
    const [filesToDelete, setFilesToDelete] = useState<{ id: string }[]>([]);
    const { getCurrentIdToken } = useUser();
    const { metadata } = useMetadata();
    const { customFetch } = useFetchWithMsal();
    const { settings } = useSettings();
    const { usecasetypeid } = useParams();
    /**
     * TODO: add this in PBI Knowledge-Management
     */
    //
    //const [showModal, setShowModal] = useState<boolean>(false);
    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        setLoading(true);
        customFetch({ scopes: [] }, `/api${location.pathname}`, { method: "GET" })
            .then(data => setUseCases(data))
            .then(() => setLoading(false));
    }, []);

    const handleCloseModal = () => {
        setOpenCreateModal(false);
        setEditCategoryElement({} as ICategory);
        setFilesToDelete([]);
        navigate(-1);
    };

    const handleCloseEditModal = () => {
        setOpenEditSheet(false);
        setEditCategoryElement({} as ICategory);
        setFilesToDelete([]);
        navigate(-1);
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setWaitingForUpload(true);
        const event_targets = e.currentTarget.elements;
        const submit_button = document.getElementById("submit-new-category") as HTMLButtonElement;
        const formdata = new FormData(e.currentTarget, submit_button);
        const id = (event_targets.namedItem(`input_name_de_cat`) as HTMLInputElement).name.split("<")[1].split(">")[0];
        const temp = metadata.temperature.filter((temp: Temperature) => {
            return (event_targets.namedItem(`${temp.id}`) as HTMLButtonElement).dataset.state === "checked";
        })[0];
        const model = metadata.model.filter((mod: Model) => {
            return (event_targets.namedItem(`${mod.id}`) as HTMLButtonElement).dataset.state === "checked";
        })[0];
        formdata.append(`category<${id}>:temperature`, temp.id);
        formdata.append(`category<${id}>:model`, model.id);
        customFetch({ scopes: [] }, `/api${location.pathname.replace("/create", "")}`, {
            method: "POST",
            body: formdata
        })
            .then(data => setUseCases(data))
            .then(() => {
                setWaitingForUpload(false);
                handleCloseModal();
            });
    };

    const handlePut = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setWaitingForUpload(true);
        const event_targets = e.currentTarget.elements;
        const submit_button = document.getElementById("submit-new-category") as HTMLButtonElement;
        const formdata = new FormData(e.currentTarget, submit_button);
        const temp = metadata.temperature.filter((temp: Temperature) => {
            return (event_targets.namedItem(`${temp.id}`) as HTMLButtonElement).dataset.state === "checked";
        })[0];
        const model = metadata.model.filter((mod: Model) => {
            return (event_targets.namedItem(`${mod.id}`) as HTMLButtonElement).dataset.state === "checked";
        })[0];
        formdata.append(`category<${editCategoryElement.id}>:temperature`, temp.id);
        formdata.append(`category<${editCategoryElement.id}>:model`, model.id);
        formdata.append(`category<${editCategoryElement.id}>:filesToDelete`, JSON.stringify(filesToDelete));
        customFetch({ scopes: [] }, `/api${location.pathname.replace("/edit", "")}`, {
            method: "PUT",
            body: formdata
        })
            .then(data => setUseCases(data))
            .then(() => {
                setWaitingForUpload(false);
                handleCloseModal();
            });
    };

    const handleDelete = (id: string) => {
        setWaitingForDelete(true);
        customFetch({ scopes: [] }, `/api${location.pathname}/${id}`, {
            method: "DELETE"
        })
            .then(data => setUseCases(data))
            .then(() => {
                setWaitingForDelete(false);
            });
    };

    const handleEdit = (id: string) => {
        const editCategoryElement_ = { ...useCases?.filter((item: ICategory) => item.id === id)[0] } as ICategory;
        setEditCategoryElement(prev => ({ ...editCategoryElement_ }));
        setFilesToDelete(prev => []);
        setOpenEditSheet(true);
        navigate(location.pathname + "/edit");
    };

    const handleDeleteFile = (id: string) => {
        const editCategoryElementCopy = structuredClone(editCategoryElement);
        const idx = editCategoryElementCopy.files.findIndex((value: IDocTemplate) => value.id === id);
        const deletedFile = editCategoryElementCopy.files.splice(idx, 1);
        setEditCategoryElement({ ...editCategoryElementCopy });
        setFilesToDelete(prev => [...prev, { id: deletedFile[0].id }]);
    };

    if (loading) return <div className=" text-white">Loading...</div>;

    return (
        <>
            {/**
             * TODO: This may be Grid and GridItems (see TODO in LandingpageTiles)
             */}
            <div className="grid grid-cols-dynamic_250_300 gap-8 auto-rows-[1fr] pt-5">
                {waitingForDelete ? (
                    <div className="absolute w-full h-full bg-secondary/60 top-0 left-0 before:w-6 before:h-6 before:content-[''] before:border-2 before:border-secondary before:border-t-primary before:rounded-full before:absolute before:animate-spinner before:top-1/2 before:left-1/2"></div>
                ) : null}
                {useCases?.map((value: ICategory, idx: number) => (
                    <Category {...value} key={"usecase-" + idx} handleEdit={() => handleEdit(value.id)} handleDelete={() => handleDelete(value.id)} />
                ))}

                {settings.filter((itm: Settings) => itm.id === usecasetypeid)[0].general["allowCreationOfCategories"].default && (
                    <CreateCategory onOpenModal={() => setOpenCreateModal(true)} />
                )}
                <Outlet
                    context={[
                        openCreateModal,
                        handleCloseModal,
                        handleSubmit,
                        waitingForUpload,
                        openEditSheet,
                        handleCloseEditModal,
                        handlePut,
                        editCategoryElement,
                        handleDeleteFile
                    ]}
                />
            </div>
        </>
    );
};
