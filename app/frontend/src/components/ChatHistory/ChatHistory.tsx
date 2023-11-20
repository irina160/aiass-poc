import { Button } from "@components/ui/button";
import { IChatHistory } from "@pages/ChatContextPage/ChatContextPage";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { ReactComponent as OpenPanel } from "@assets/CarbonSidePanelOpenFilled.svg";
import { ReactComponent as ClosePanel } from "@assets/CarbonSidePanelCloseFilled.svg";
import React from "react";

type TChatHistoryProps = {
    showChatHistory: boolean;
    refreshPage: () => void;
    setShowChatHistory: React.Dispatch<React.SetStateAction<boolean>>;
    chatHistory: [string, IChatHistory[]][];
    getSelectedConversation: (id: string) => void;
    handleDeleteChatConversation: (e: React.MouseEvent<SVGElement>, id: string) => void;
    chatId: string | undefined;
};

export const ChatHistory = ({
    showChatHistory,
    refreshPage,
    setShowChatHistory,
    chatHistory,
    getSelectedConversation,
    handleDeleteChatConversation,
    chatId
}: TChatHistoryProps) => {
    return (
        <>
            <div
                className={`bg-foregrund rounded-md overflow-y-auto border-r-2 border-t-2 shadow-custom flex flex-col ${
                    showChatHistory ? "w-[300px] visible transition-all duration-200" : "w-0 invisible -translate-x-[300px] transition-all duration-200"
                }`}
            >
                <div className="flex flex-row justify-center items-center pt-2 px-2 gap-2">
                    <Button onClick={refreshPage} className={"flex-1 flex flex-row gap-3 items-center justify-start"}>
                        <Plus /> New Chat
                    </Button>
                    <ClosePanel onClick={() => setShowChatHistory(false)} className="text-primary hover:cursor-pointer p-1 hover:bg-secondary rounded-md" />
                </div>
                <div className="p-2 overflow-y-auto">
                    <ul>
                        {chatHistory.map(([date, chathistorylist], index) => {
                            return (
                                <React.Fragment key={index}>
                                    <li>{date}</li>
                                    {chathistorylist.map((chathistory: IChatHistory) => {
                                        return (
                                            <li id={chathistory.conversation_id} className="flex py-1" key={chathistory.conversation_id}>
                                                <Button
                                                    variant={"outline"}
                                                    className={`box-border rounded-md hover:bg-accent flex justify-start gap-3 w-full text-start items-center ${
                                                        chatId === chathistory.conversation_id ? "bg-primary/20 hover:bg-primary/30" : ""
                                                    }`}
                                                    onClick={() => getSelectedConversation(chathistory.conversation_id)}
                                                    title={chathistory.topic}
                                                >
                                                    <MessageSquare width={20} />

                                                    <span className=" whitespace-nowrap flex-1 overflow-ellipsis overflow-hidden break-all text-primary">
                                                        {chathistory.topic}
                                                    </span>
                                                    <Trash2
                                                        width={20}
                                                        className="hover:text-destructive"
                                                        onClick={e => handleDeleteChatConversation(e, chathistory.conversation_id)}
                                                    />
                                                </Button>
                                            </li>
                                        );
                                    })}
                                </React.Fragment>
                            );
                        })}
                    </ul>
                </div>
            </div>

            <OpenPanel
                onClick={() => setShowChatHistory(true)}
                className={`absolute text-primary hover:cursor-pointer left-2 top-3 p-1 hover:bg-secondary rounded-md ${showChatHistory ? " hidden" : "block"}`}
            />
        </>
    );
};
