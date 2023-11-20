import { Button } from "@components/ui/button";
import { Input } from "@components/ui/input";
import { Label } from "@components/ui/label";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@components/ui/sheet";
import { Textarea } from "@components/ui/textarea";
import { ICategory, Index } from "@pages/UseCaseTypePage/UseCaseTypePage";
import { useOutletContext } from "react-router-dom";

export const EditIndexSheet = () => {
    const [
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
    ]: [
        boolean,
        () => void,
        (e: React.FormEvent<HTMLFormElement>) => Promise<void>,
        ICategory[],
        (id: string) => void,
        () => void,
        boolean,
        boolean,
        () => void,
        () => void,
        Index
    ] = useOutletContext();
    return (
        <Sheet
            open={openEditSheet}
            onOpenChange={open => {
                open ? null : handleCloseEditModal();
            }}
        >
            <SheetContent className="overflow-auto">
                <SheetHeader>
                    <SheetTitle>Edit your index</SheetTitle>
                </SheetHeader>
                <form className="flex justify-end flex-col gap-2" onSubmit={handlePut}>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="index_name_de">*Name DE</Label>
                            <Input id="index_name_de" type="text" required placeholder="Name DE" defaultValue={editIndexElement.name_de} />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="index_name_en">*Name EN</Label>
                            <Input id="index_name_en" type="text" required placeholder="Name EN" defaultValue={editIndexElement.name_en} />
                        </div>
                    </div>
                    <div className="flex flex-row justify-between gap-2">
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="index_description_de">*Description DE</Label>
                            <Textarea id="index_description_de" required placeholder="Description DE" defaultValue={editIndexElement.description_de} />
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <Label htmlFor="index_description_en">*Description EN</Label>
                            <Textarea id="index_description_en" required placeholder="Description EN" defaultValue={editIndexElement.description_en} />
                        </div>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button type="submit">Save</Button>
                    </div>
                </form>
                {waitingForUpload ? (
                    <div className="absolute w-full h-full bg-secondary/60 top-0 left-0 before:w-6 before:h-6 before:content-[''] before:border-2 before:border-secondary before:border-t-primary before:rounded-full before:absolute before:animate-spinner before:top-1/2 before:left-1/2"></div>
                ) : null}
            </SheetContent>
        </Sheet>
    );
};
