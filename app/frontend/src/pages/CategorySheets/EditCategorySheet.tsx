import { Button } from "@components/ui/button";
import { Input } from "@components/ui/input";
import { Label } from "@components/ui/label";
import { RadioGroup, RadioGroupItem } from "@components/ui/radio-group";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@components/ui/sheet";
import { Textarea } from "@components/ui/textarea";
import { Model, Temperature, useMetadata } from "@hooks/useMetadata";
import { Settings, useSettings } from "@hooks/useSettings";
import { ICategory, IDocTemplate } from "@pages/UseCaseTypePage/UseCaseTypePage";
import { Eye, Trash2 } from "lucide-react";
import { useOutletContext, useParams } from "react-router-dom";

export const EditCategorySheet = () => {
    const [
        openCreateModal,
        handleCloseModal,
        handleSubmit,
        waitingForUpload,
        openEditSheet,
        handleCloseEditModal,
        handlePut,
        editCategoryElement,
        handleDeleteFile
    ]: [boolean, () => void, () => void, boolean, boolean, () => void, (e: React.FormEvent<HTMLFormElement>) => void, ICategory, (id: string) => void] =
        useOutletContext();
    const { metadata } = useMetadata();
    const { settings } = useSettings();
    const { usecasetypeid } = useParams();
    return (
        <Sheet
            open={openEditSheet}
            onOpenChange={open => {
                open ? null : handleCloseEditModal();
            }}
        >
            <SheetContent className="overflow-auto">
                <SheetHeader>
                    <SheetTitle>Edit your category</SheetTitle>
                </SheetHeader>
                <form className="flex justify-end flex-col gap-3" onSubmit={e => handlePut(e)}>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="input_name_de_cat">*Name DE</Label>
                            <Input
                                id="input_name_de_cat"
                                type="text"
                                required
                                placeholder="Name DE"
                                defaultValue={editCategoryElement.name_de}
                                name={`category<${editCategoryElement.id}>:name_de`}
                            />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="input_name_en_cat">*Name EN</Label>
                            <Input
                                id="input_name_en_cat"
                                type="text"
                                required
                                placeholder="Name EN"
                                defaultValue={editCategoryElement.name_en}
                                name={`category<${editCategoryElement.id}>:name_en`}
                            />
                        </div>
                    </div>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="input_desc_de_cat">*Description DE</Label>
                            <Textarea
                                id="input_desc_de_cat"
                                required
                                placeholder="Description DE"
                                defaultValue={editCategoryElement.description_de}
                                name={`category<${editCategoryElement.id}>:description_de`}
                            />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="input_desc_en_cat">*Description EN</Label>
                            <Textarea
                                id="input_desc_en_cat"
                                required
                                placeholder="Description EN"
                                defaultValue={editCategoryElement.description_en}
                                name={`category<${editCategoryElement.id}>:description_en`}
                            />
                        </div>
                    </div>
                    <div className="flex flex-row justify-between gap-4">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_system_prompt`}>System Prompt</Label>
                            <Textarea
                                id={`input_system_prompt`}
                                placeholder="System Prompt"
                                defaultValue={editCategoryElement.system_prompt}
                                name={`category<${editCategoryElement.id}>:system_prompt`}
                            />
                        </div>
                        <div className="flex flex-col gap-1">
                            <Label>Temperature</Label>
                            <RadioGroup defaultValue={editCategoryElement.temperature}>
                                {metadata.temperature.map((temp: Temperature) => {
                                    return (
                                        <div className="flex items-center space-x-2" key={temp.id}>
                                            <RadioGroupItem value={temp.id} id={`${temp.id}`} /> <Label htmlFor={`${temp.id}`}>{temp.display_name_en}</Label>
                                        </div>
                                    );
                                })}
                            </RadioGroup>
                        </div>
                        <div className="flex flex-col gap-1">
                            <Label>Model</Label>
                            <RadioGroup defaultValue={editCategoryElement.model}>
                                {metadata.model.map((mod: Model) => {
                                    return (
                                        <div className="flex items-center space-x-2" key={mod.id}>
                                            <RadioGroupItem value={mod.id} id={`${mod.id}`} /> <Label htmlFor={`${mod.id}`}>{mod.display_name_en}</Label>
                                        </div>
                                    );
                                })}
                            </RadioGroup>
                        </div>
                    </div>
                    {settings.filter((itm: Settings) => itm.id === usecasetypeid)[0].categories["enableFileUpload"].default && (
                        <>
                            <div className=" max-h-[400px] overflow-y-auto">
                                <Label>Files: </Label>
                                {editCategoryElement.files?.map((file: IDocTemplate) => {
                                    return (
                                        <div
                                            className="pr-2 pl-2 pb-2 relative flex flex-row justify-between gap-2 after:w-full after:content-[''] after:absolute after:bottom-0 after:right-0 after:h-1 after:bg-accent"
                                            key={file.id}
                                        >
                                            <div className="flex flex-row gap-1 flex-1 overflow-hidden">
                                                <span className=" text-ellipsis overflow-hidden whitespace-nowrap">{file.name}</span>
                                            </div>
                                            <div className="flex flex-row gap-2">
                                                <Eye className="w-6 hover:cursor-pointer hover:text-primary" />
                                                <Trash2
                                                    className="w-6 text-destructive hover:text-destructive/70 hover:cursor-pointer"
                                                    onClick={() => handleDeleteFile(file.id)}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="flex flex-col gap-2">
                                <Label htmlFor={`files`}>Upload new Files</Label>
                                <Input id={`files`} type="file" accept="application/pdf" multiple name={`category<${editCategoryElement.id}>:files`} />
                            </div>
                        </>
                    )}
                    <div className="flex justify-end gap-2">
                        <Button type="submit" id="edit-category">
                            Save
                        </Button>
                    </div>
                </form>
                {waitingForUpload ? (
                    <div className="absolute w-full h-full bg-secondary/60 top-0 left-0 before:w-6 before:h-6 before:content-[''] before:border-2 before:border-secondary before:border-t-primary before:rounded-full before:absolute before:animate-spinner before:top-1/2 before:left-1/2"></div>
                ) : null}
            </SheetContent>
        </Sheet>
    );
};
