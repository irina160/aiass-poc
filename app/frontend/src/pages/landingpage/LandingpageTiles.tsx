import React, { Suspense, useState, useEffect } from "react";
import { ReactComponent as Robot } from "@assets/Robot.svg";
import { NavLink, useLocation } from "react-router-dom";
import { Button } from "@components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from "@components/ui/dropdown-menu";

import { Bot, Edit, Trash2 } from "lucide-react";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger
} from "@components/ui/alert-dialog";

interface LandingPageTilesProps {
    id: string;
    title: string;
    description: string;
    //logo: string;
    link: string;
    disableEditButton: boolean;
    disableDeleteButton: boolean;
    handleEdit: () => void;
    handleDelete: () => void;
}
/**
 * TODO: Rename and move to different location
 * TODO: This may be Grid and GridItem Components
 */

export const LandingPageTiles = (props: LandingPageTilesProps): JSX.Element => {
    const [element, setElement] = useState<JSX.Element | null>(null);
    const [openAlertDialog, setOpenAlertDialog] = useState<boolean>(false);
    /*
    useEffect(() => {
        import(props.logo).then(res => {
            const Icon = res.ReactComponent as React.ComponentType<JSX.IntrinsicElements["svg"]>;
            setElement(<Icon className="h-10 w-10 group-hover:fill-accent-foreground fill-foreground" />);
        });
    });
    */
    return (
        <>
            <NavLink
                to={props.link}
                className="relative p-6 rounded-md bg-background hover:bg-accent group"
                title={`Navigate to ${props.title}`}
                id={props.id}
                onClick={(e: React.MouseEvent<Element, MouseEvent>) => {
                    e.stopPropagation();
                }}
            >
                <div className="absolute top-[5%] right-[5%] z-10">
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button className=" w-2 h-3" variant={"secondary"}>
                                ...
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="relative">
                            <DropdownMenuLabel>{props.title}</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                                onClick={(e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    props.handleEdit();
                                }}
                                disabled={props.disableEditButton}
                            >
                                <Edit className="w-4 mr-2" />
                                <span>Edit</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem
                                className=" focus:bg-destructive group"
                                onClick={(e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setOpenAlertDialog(true);
                                }}
                                disabled={props.disableEditButton}
                            >
                                <Trash2 className="w-4 mr-2 group-focus:text-destructive-foreground" />
                                <span className=" group-focus:text-destructive-foreground">Delete</span>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
                <div className="relative after:content-[''] after:absolute after:-top-[2px] after:w-10 after:bg-primary after:h-[2px] after:left-0 group-hover:text-accent-foreground font-sans text-foreground">
                    {props.title}
                </div>
                <div className="flex items-center flex-col group-hover:text-accent-foreground font-sans gap-4 text-bg-foreground">
                    {/**TODO: Change this to dynamic icon */}
                    <Bot className="h-10 w-10 group-hover:text-accent-foreground text-foreground" />
                    <div className=" ">{props.description}</div>
                </div>
            </NavLink>
            <AlertDialog open={openAlertDialog} onOpenChange={setOpenAlertDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Please note that this action is irreversible. It will permanently delete the selected item and all associated data from our servers.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={() => props.handleDelete()}>Continue</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
};
