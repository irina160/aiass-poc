import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    {
        text: "I want to give my employee a bouquet of flowers worth 45 euros for their anniversary. What do I need to consider?",
        value: "I want to give my employee a bouquet of flowers worth 45 euros for their anniversary. What do I need to consider?"
    },
    {
        text: "I want to invite my employees to an event today, and I want the company to cover the costs. Can I do that?",
        value: "I want to invite my employees to an event today, and I want the company to cover the costs. Can I do that?"
    },
    {
        text: "I want to invite my employees to an event today, and I want the company to cover the costs. Can I do that?",
        value: "I want to invite my employees to an event today, and I want the company to cover the costs. Can I do that?"
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
    exampleQuestions: string[];
}

export const ExampleList = ({ onExampleClicked, exampleQuestions }: Props) => {
    return (
        <ul className={" list-none pl-0 flex flex-wrap gap-3 justify-center flex-row items-stretch mx-[5%] my-0"}>
            {exampleQuestions.map((x, i) => (
                <li className={" flex-1 flex justify-center"} key={i}>
                    {" "}
                    <Example text={x} value={x} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
