import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogAction,
    AlertDialogCancel
} from "@components/ui/alert-dialog";

type TErrorComponentProps = {
    open: boolean;
    setOpen: React.Dispatch<React.SetStateAction<boolean>>;
    error: string;
};

export const ErrorComponent = (props: TErrorComponentProps) => {
    return (
        <AlertDialog open={props.open} onOpenChange={props.setOpen}>
            <AlertDialogContent>
                <AlertDialogHeader className=" w-full overflow-x-auto">
                    <AlertDialogTitle>Something went wrong</AlertDialogTitle>
                    <AlertDialogDescription>Here is what went wrong:</AlertDialogDescription>
                    <AlertDialogDescription className="max-h-[50vh] overflow-y-auto whitespace-break-spaces ">{props.error}</AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
};
