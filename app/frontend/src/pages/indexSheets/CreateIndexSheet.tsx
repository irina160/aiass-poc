import { Button } from "@components/ui/button";
import { Input } from "@components/ui/input";
import { Label } from "@components/ui/label";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@components/ui/sheet";
import { Textarea } from "@components/ui/textarea";
import { CategoryTemplate, ICategory } from "@pages/UseCaseTypePage/UseCaseTypePage";
import { useOutletContext } from "react-router-dom";
import { ReactComponent as Add } from "@assets/Add.svg";

export const CreateIndexSheet = () => {
    const id = window.crypto.randomUUID();
    const [openCreateModal, handleCloseModal, handlePost, categories, handleRemoveCategory, handleAddCategory, waitingForUpload, ...rest]: [
        boolean,
        () => void,
        (e: React.FormEvent<HTMLFormElement>) => Promise<void>,
        ICategory[],
        (id: string) => void,
        () => void,
        boolean,
        any
    ] = useOutletContext();
    return (
        <Sheet
            open={openCreateModal}
            onOpenChange={open => {
                open ? null : handleCloseModal();
            }}
        >
            <SheetContent className="overflow-auto">
                <SheetHeader>
                    <SheetTitle>Create a new index</SheetTitle>
                </SheetHeader>
                <form className="flex justify-end flex-col gap-2" onSubmit={handlePost} id={"upload-index"}>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="index_name_de">*Name DE</Label>
                            <Input id="index_name_de" type="text" required placeholder="Name DE" name={`index<${id}>:name_de`} />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="index_name_en">*Name EN</Label>
                            <Input id="index_name_en" type="text" required placeholder="Name EN" name={`index<${id}>:name_en`} />
                        </div>
                    </div>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="index_description_de">*Description DE</Label>
                            <Textarea id="index_description_de" required placeholder="Description DE" name={`index<${id}>:description_de`} />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="index_description_en">*Description EN</Label>
                            <Textarea id="index_description_en" required placeholder="Description EN" name={`index<${id}>:description_en`} />
                        </div>
                    </div>
                    {categories.map((cat: ICategory, idx: number) => (
                        <CategoryTemplate no={idx} key={cat.id} id={cat.id} removeCategory={handleRemoveCategory} />
                    ))}
                    <div className="flex flex-row items-center gap-2 hover:bg-secondary hover:cursor-pointer hover:rounded-md" onClick={handleAddCategory}>
                        <Add className="text-foreground w-10" />
                        <span>Add a category</span>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button type="submit" id={"submit-new-index"}>
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
