import styles from "./Example.module.css";

interface Props {
    text: string;
    value: string;
    onClick: (value: string) => void;
}

export const Example = ({ text, value, onClick }: Props) => {
    return (
        <div
            className=" flex bg-primary rounded-md flex-col p-5 mb-1 cursor-pointer text-primary-foreground justify-center flex-1 items-center"
            onClick={() => onClick(value)}
        >
            <p className="m-0 text-lg w-fit">{text}</p>
        </div>
    );
};
