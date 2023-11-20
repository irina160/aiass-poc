import { Button } from "@components/ui/button";
import { Input } from "@components/ui/input";
import { Label } from "@components/ui/label";
import { RadioGroup, RadioGroupItem } from "@components/ui/radio-group";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@components/ui/sheet";
import { Textarea } from "@components/ui/textarea";
import { Model, Temperature, useMetadata } from "@hooks/useMetadata";
import { Settings, useSettings } from "@hooks/useSettings";
import { useOutletContext, useParams } from "react-router-dom";

export const CreateCategorySheet = () => {
    const [openCreateModal, handleCloseModal, handleSubmit, waitingForUpload, ...rest]: [boolean, () => void, () => void, boolean, any] = useOutletContext();
    const { usecasetypeid } = useParams();
    const { metadata } = useMetadata();
    const { settings } = useSettings();
    const id = window.crypto.randomUUID();
    return (
        <Sheet
            open={openCreateModal}
            onOpenChange={open => {
                open ? null : handleCloseModal();
            }}
        >
            <SheetContent className="overflow-auto">
                <SheetHeader className="pb-3">
                    <SheetTitle>Create a new Category</SheetTitle>
                </SheetHeader>
                <form className="flex justify-end flex-col gap-2" onSubmit={handleSubmit}>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_name_de_cat`}>*Name DE</Label>
                            <Input id={`input_name_de_cat`} type="text" required placeholder="Name DE" name={`category<${id}>:name_de`} />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_name_en_cat`}>*Name EN</Label>
                            <Input id={`input_name_en_cat`} type="text" required placeholder="Name EN" name={`category<${id}>:name_en`} />
                        </div>
                    </div>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_desc_de_cat`}>*Description DE</Label>
                            <Textarea id={`input_desc_de_cat`} required placeholder="Description DE" name={`category<${id}>:description_de`} />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_desc_en_cat`}>*Description EN</Label>
                            <Textarea id={`input_desc_en_cat`} required placeholder="Description EN" name={`category<${id}>:description_en`} />
                        </div>
                    </div>
                    <div className="flex flex-row justify-between gap-4">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor={`input_system_prompt`}>System Prompt</Label>
                            <Textarea id={`input_system_prompt`} placeholder="System Prompt" name={`category<${id}>:system_prompt`} />
                        </div>
                        <div className="flex flex-col gap-1">
                            <Label>Temperature</Label>
                            <RadioGroup defaultValue="precise">
                                {metadata.temperature.map((temp: Temperature) => {
                                    return (
                                        <div className="flex items-center space-x-2" key={temp.id}>
                                            <RadioGroupItem value={temp.display_name_en} id={`${temp.id}`} />{" "}
                                            <Label htmlFor={`${temp.id}`}>{temp.display_name_en}</Label>
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
                                            <RadioGroupItem value={mod.display_name_en} id={`${mod.id}`} />{" "}
                                            <Label htmlFor={`${mod.id}`}>{mod.display_name_en}</Label>
                                        </div>
                                    );
                                })}
                            </RadioGroup>
                        </div>
                    </div>
                    {settings.filter((itm: Settings) => itm.id === usecasetypeid)[0].categories["enableFileUpload"].default && (
                        <div className="flex flex-col gap-1">
                            <Label htmlFor={`files`}>*File</Label>
                            <Input id={`files`} type="file" accept="application/pdf" multiple required name={`category<${id}>:files`} />
                        </div>
                    )}
                    <div className="flex justify-end gap-2">
                        <Button type="submit" id="submit-new-category">
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
