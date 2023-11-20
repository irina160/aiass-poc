import styles from "./UserChatMessage.module.css";

interface Props {
    message: string;
}

export const UserChatMessage = ({ message }: Props) => {
    return (
        <div className={"flex justify-end mb-5 max-w-[80%] ml-auto"}>
            <div className={"p-5 bg-accent rounded-md shadow-md"}>{message}</div>
        </div>
    );
};
