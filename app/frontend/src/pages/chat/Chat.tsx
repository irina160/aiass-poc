import React, { useRef, useState, useEffect, useReducer } from "react";
import { Checkbox, Panel, DefaultButton, TextField, SpinButton, Dropdown, IDropdownOption } from "@fluentui/react";
import { SparkleFilled } from "@fluentui/react-icons";

import styles from "./Chat.module.css";

import { chatApi, RetrievalMode, Approaches, AskResponse, ChatRequest, ChatTurn } from "../../api";
import { Answer, AnswerError, AnswerLoading } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { ExampleList, ExampleModel } from "../../components/Example";
import { UserChatMessage } from "../../components/UserChatMessage";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { useLocation } from "react-router";
import { useFetchWithMsal } from "@hooks/useFetchWithMsal";
import { Settings, useSettings } from "@hooks/useSettings";
import { Link, NavLink, useNavigate, useOutletContext, useParams, useSearchParams } from "react-router-dom";
import { IChatHistory } from "@pages/ChatContextPage/ChatContextPage";

import { MessageSquare, Plus, Trash, Trash2 } from "lucide-react";
import { Button } from "@components/ui/button";
import { ChatHistory } from "@components/ChatHistory/ChatHistory";

function groupBy<T, K extends keyof any>(list: T[], getKey: (item: T) => K): Record<K, T[]> {
    return list.reduce(
        (previous, currentItem) => {
            const group = getKey(currentItem);
            if (!previous[group]) {
                previous[group] = [];
            }
            previous[group].push(currentItem);
            return previous;
        },
        {} as Record<K, T[]>
    );
}

type ChatHistoryByTimestamp = { [date: string]: IChatHistory[] };

export const Chat = () => {
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [retrieveCount, setRetrieveCount] = useState<number>(3);
    const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>(RetrievalMode.Hybrid);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(true);
    const [excludeCategory, setExcludeCategory] = useState<string>("");
    const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] = useState<boolean>(true);
    const [exampleQuestions, setExampleQuestions] = useState<string[]>([] as string[]);

    const lastQuestionRef = useRef<string>("");
    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [answers, setAnswers] = useState<[user: string, response: AskResponse][]>([]);

    const [setting, setSetting] = useState<Settings>({} as Settings);
    const [showChatHistory, setShowChatHistory] = useState<boolean>(false);
    const [_chatHistory, set_ChatHistory] = useState<[string, IChatHistory[]][]>([]);
    const [chatHistory, setChatHistory]: [IChatHistory[], React.Dispatch<React.SetStateAction<IChatHistory[]>>] = useOutletContext();
    const location = useLocation();
    const params = useParams();
    const { customFetch } = useFetchWithMsal();
    const { settings } = useSettings();
    const { usecasetypeid } = useParams();
    const navigate = useNavigate();

    useEffect(() => {
        const sorted_chat_history = chatHistory.sort((a, b) => b.timestamp - a.timestamp);

        const chatHistory_by_ts: ChatHistoryByTimestamp = groupBy(sorted_chat_history, ({ timestamp }: IChatHistory) =>
            new Date(timestamp * 1000).toDateString()
        );
        const chatHistory_by_ts_array = Object.entries(chatHistory_by_ts);
        set_ChatHistory(chatHistory_by_ts_array);
    }, [chatHistory]);

    useEffect(() => {
        setExampleQuestions({} as string[]);
        customFetch({ scopes: [] }, `/api${location.pathname}/example_questions`, { method: "GET" }).then(data => {
            setExampleQuestions(data["example_questions"]);
            setIsLoading(false);
        });
    }, []);

    useEffect(() => {
        setSetting(settings.filter((itm: Settings) => itm.id === usecasetypeid)[0]);
    }, []);

    const makeApiRequest = async (question: string) => {
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        if (location.search) {
            navigate(`${location.pathname}${location.search.split("?new_conversation=")[1]}`, { replace: true });
        }

        try {
            const history: ChatTurn[] = answers.map(a => ({ user: a[0], bot: a[1].answer }));
            const request: ChatRequest = {
                history: [...history, { user: question, bot: undefined }],
                approach: setting.chat["approach"].default as Approaches,
                overrides: {
                    promptTemplate: (setting.overrides["prompt template"].default as string) || undefined, //promptTemplate.length === 0 ? undefined : promptTemplate,
                    excludeCategory: undefined, //excludeCategory.length === 0 ? undefined : excludeCategory,
                    top: (setting.overrides["top"].default as number) || undefined, //retrieveCount,
                    retrievalMode: (setting.overrides["retrieval mode"].default as RetrievalMode) || undefined, //retrievalMode,
                    semanticRanker: (setting.overrides["semantic ranker"].default as boolean) || undefined, //useSemanticRanker,
                    semanticCaptions: (setting.overrides["semantic captions"].default as boolean) || undefined, //useSemanticCaptions,
                    suggestFollowupQuestions: (setting.overrides["suggest followup questions"].default as boolean) || undefined //useSuggestFollowupQuestions
                },
                new_conversation: location.search.includes("?new_conversation") ? true : false
            };
            const result = await customFetch(
                { scopes: [] },
                `/api${location.pathname}${location.search ? location.search.split("?new_conversation=")[1] : ""}` /*  */,
                {
                    method: "POST",
                    headers: new Headers({ "Content-Type": "application/json" }),
                    body: JSON.stringify(request)
                }
            );
            result?.conversation_details && setChatHistory(prev => [...prev, result.conversation_details]);
            setAnswers([...answers, [question, result]]);
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        lastQuestionRef.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswers([]);
    };

    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }), [isLoading]);

    const onPromptTemplateChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplate(newValue || "");
    };

    const onRetrieveCountChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setRetrieveCount(parseInt(newValue || "3"));
    };

    const onRetrievalModeChange = (_ev: React.FormEvent<HTMLDivElement>, option?: IDropdownOption<RetrievalMode> | undefined, index?: number | undefined) => {
        setRetrievalMode(option?.data || RetrievalMode.Hybrid);
    };

    const onUseSemanticRankerChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticRanker(!!checked);
    };

    const onUseSemanticCaptionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticCaptions(!!checked);
    };

    const onExcludeCategoryChanged = (_ev?: React.FormEvent, newValue?: string) => {
        setExcludeCategory(newValue || "");
    };

    const onUseSuggestFollowupQuestionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSuggestFollowupQuestions(!!checked);
    };

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
    };

    const onShowCitation = (citation: string, index: number) => {
        if (activeCitation === citation && activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab && selectedAnswer === index) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveCitation(citation);
            setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
        }

        setSelectedAnswer(index);
    };

    const onToggleTab = (tab: AnalysisPanelTabs, index: number) => {
        if (activeAnalysisPanelTab === tab && selectedAnswer === index) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveAnalysisPanelTab(tab);
        }

        setSelectedAnswer(index);
    };

    const getExampleQuestions = (id: string) => {
        setExampleQuestions({} as string[]);
        customFetch(
            { scopes: [] },
            `/api/usecasetypes/${params.usecasetypeid}/indices/${params.indexid}/categories/${params.categoryid}/chat/example_questions`,
            { method: "GET" }
        ).then(data => {
            setExampleQuestions(data["example_questions"]);
            setIsLoading(false);
        });
    };

    const refreshPage = () => {
        const new_id = window.crypto.randomUUID();
        navigate(`/usecasetypes/${params.usecasetypeid}/indices/${params.indexid}/categories/${params.categoryid}/chat/?new_conversation=${new_id}`, {
            replace: true
        });
        lastQuestionRef.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswers([]);
        getExampleQuestions(new_id);
    };

    const handleDeleteChatConversation = (e: React.MouseEvent<SVGElement>, id: string) => {
        e.preventDefault();
        e.stopPropagation();
        customFetch({ scopes: [] }, `/api/usecasetypes/${params.usecasetypeid}/indices/${params.indexid}/categories/${params.categoryid}/chat/${id}`, {
            method: "DELETE"
        }).then(data => {
            const rest = chatHistory.filter((item: IChatHistory) => item.conversation_id !== id);
            setChatHistory(rest);
            if (params.chatid === id) {
                refreshPage();
            }
        });
    };

    const getSelectedConversation = (id: string) => {
        navigate(`/usecasetypes/${params.usecasetypeid}/indices/${params.indexid}/categories/${params.categoryid}/chat/${id}`, { replace: true });
        customFetch({ scopes: [] }, `/api/usecasetypes/${params.usecasetypeid}/indices/${params.indexid}/categories/${params.categoryid}/chat/${id}`, {
            method: "GET"
        })
            .then(data => {
                const cleaned_up_data = data["history"].reduce((acc: [user: string, response: AskResponse][], currentItem: { user: string } | AskResponse) => {
                    if (acc.length === 0) {
                        if ("user" in currentItem) {
                            // @ts-ignore
                            acc.push([currentItem.user]);
                        }
                    } else {
                        const lastGroup = acc[acc.length - 1];
                        // @ts-ignore
                        if (lastGroup.length === 1) {
                            // @ts-ignore
                            acc[acc.length - 1] = [lastGroup[0], currentItem];
                        } else {
                            // @ts-ignore
                            acc.push([currentItem.user]);
                        }
                    }
                    return acc;
                }, []);
                setAnswers(cleaned_up_data);
                lastQuestionRef.current = data["history"][data["history"].length - 2]["user"];
            })
            .then(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }));
    };

    return (
        <div className={"min-h-[calc(100vh-56px)] max-h-[calc(100vh-56px)] flex flex-1 flex-col overflow-hidden mt-0"}>
            <div className="flex-1 flex h-full overflow-hidden gap-1 pr-1 relative">
                <ChatHistory
                    showChatHistory={showChatHistory}
                    refreshPage={refreshPage}
                    setShowChatHistory={setShowChatHistory}
                    chatHistory={_chatHistory}
                    getSelectedConversation={getSelectedConversation}
                    handleDeleteChatConversation={handleDeleteChatConversation}
                    chatId={params.chatid}
                />

                <div className="flex-1 flex flex-col items-center w-full bg-background">
                    {!lastQuestionRef.current ? (
                        <div className={"flex-1 flex flex-col justify-start items-center pt-14"}>
                            {/* <SparkleFilled fontSize={"120px"} primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Chat logo" /> */}
                            <svg xmlns="http://www.w3.org/2000/svg" xmlnsXlink="http://www.w3.org/1999/xlink" width="71" height="71" viewBox="0 0 71 71">
                                <defs>
                                    <linearGradient id="linear-gradient" y1="0.609" x2="0.965" y2="0.278" gradientUnits="objectBoundingBox">
                                        <stop offset="0" stopColor="#1e49e2" />
                                        <stop offset="1" stopColor="#7213ea" />
                                    </linearGradient>
                                </defs>
                                <g id="Gruppe_6" data-name="Gruppe 6" transform="translate(-31 -480)">
                                    <circle
                                        id="Ellipse_1"
                                        data-name="Ellipse 1"
                                        cx="35.5"
                                        cy="35.5"
                                        r="35.5"
                                        transform="translate(31 480)"
                                        fill="url(#linear-gradient)"
                                    />
                                    <g id="noun-ai-5258822" transform="translate(-43.292 445.987)">
                                        <path
                                            id="Pfad_9"
                                            data-name="Pfad 9"
                                            d="M132.772,67.663q-.088,0-.175.006L130.609,60.3a2.807,2.807,0,1,0-3.262-4.474l-5.806-3.755a2.808,2.808,0,1,0-5.3-1.859l-7.538-.765a2.808,2.808,0,1,0-5.58.635L95.105,52.8a2.807,2.807,0,1,0-4.287,3.514L87.7,61.7a2.808,2.808,0,1,0-.33,5.414L89.713,72.6a2.807,2.807,0,1,0,3.8,4.045l4.04,2.027a2.808,2.808,0,1,0,5.519.733c0-.016,0-.032,0-.048l4.774-1.057a2.807,2.807,0,0,0,3.686,1.432l5.359,7.64a2.807,2.807,0,1,0,3.606-.4l2.4-5.8a2.808,2.808,0,0,0,3.339-2.757,2.788,2.788,0,0,0-.348-1.353l5.157-4.38a2.807,2.807,0,1,0,1.733-5.015ZM129.352,56.1a1.687,1.687,0,1,1-1.687,1.687A1.689,1.689,0,0,1,129.352,56.1Zm-1.978,3.677a2.817,2.817,0,0,0,.679.5l-4.41,15.336c-.073-.006-.147-.009-.222-.009a2.813,2.813,0,0,0-.326.019l-2.777-8.456a2.806,2.806,0,0,0,1.21-3.5Zm-8.447,6.637a1.687,1.687,0,1,1,1.687-1.686A1.689,1.689,0,0,1,118.928,66.415Zm2-13.406,5.806,3.755a2.808,2.808,0,0,0,.014,2.082l-5.846,3.892a2.8,2.8,0,0,0-1.417-.761V53.8a2.808,2.808,0,0,0,1.444-.788Zm-2-3.651a1.687,1.687,0,1,1-1.687,1.687A1.689,1.689,0,0,1,118.928,49.358Zm-1.73,3.9a2.8,2.8,0,0,0,1.169.541v8.18a2.8,2.8,0,0,0-1.137.517l-3.776-3.313a2.8,2.8,0,0,0,.02-2.751ZM107.626,66l2.685-5.494a2.8,2.8,0,0,0,2.4-.483l3.776,3.313a2.8,2.8,0,0,0,.421,3.344L111.5,74.571a2.808,2.808,0,0,0-1.829-.123l-2.022-4.02a2.806,2.806,0,0,0-.025-4.43ZM106.62,65.5a2.806,2.806,0,0,0-2.784.833l-3.167-1.879a2.8,2.8,0,0,0-.8-3.031l5.167-9.036a2.806,2.806,0,0,0,1.876-.042l2.16,3.413a2.8,2.8,0,0,0,.233,4.248Zm.982,2.718a1.687,1.687,0,1,1-1.687-1.687A1.689,1.689,0,0,1,107.6,68.223Zm1.728-10.436a1.687,1.687,0,1,1,1.686,1.686A1.689,1.689,0,0,1,109.33,57.787ZM108.6,50.56l7.537.765a2.785,2.785,0,0,0,.337,1.077l-3.724,3.174a2.8,2.8,0,0,0-2.727-.414l-2.16-3.413a2.819,2.819,0,0,0,.737-1.189Zm-2.681-2.522a1.687,1.687,0,1,1-1.687,1.687A1.689,1.689,0,0,1,105.915,48.038ZM95.489,54.219a2.8,2.8,0,0,0-.022-.354l8.024-2.725a2.821,2.821,0,0,0,.573.693L98.9,60.869a2.809,2.809,0,0,0-1.76,0l-2.6-4.543a2.8,2.8,0,0,0,.955-2.107ZM99.7,63.536a1.687,1.687,0,1,1-1.687-1.687A1.689,1.689,0,0,1,99.7,63.536Zm-7.022-11a1.687,1.687,0,1,1-1.687,1.686A1.689,1.689,0,0,1,92.681,52.533ZM86.812,66.047A1.687,1.687,0,1,1,88.5,64.361,1.689,1.689,0,0,1,86.812,66.047Zm1.594.624a2.8,2.8,0,0,0,.269-4.41l3.114-5.38a2.812,2.812,0,0,0,1.774,0l2.6,4.543a2.8,2.8,0,0,0-.027,4.191l-3.914,6.635a2.812,2.812,0,0,0-1.478-.1Zm2.9,9.926a1.687,1.687,0,1,1,1.686-1.687A1.689,1.689,0,0,1,91.307,76.6Zm1.88-3.77L97.1,66.192a2.805,2.805,0,0,0,2.994-.769l3.167,1.879a2.811,2.811,0,0,0-.083,1.558l-9.606,4.4a2.873,2.873,0,0,0-.387-.429Zm7.077,8.265a1.687,1.687,0,1,1,1.687-1.687A1.689,1.689,0,0,1,100.264,81.092Zm7.338-3.934c0,.016,0,.032,0,.048l-4.774,1.057a2.806,2.806,0,0,0-4.772-.592l-4.04-2.027a2.813,2.813,0,0,0,.025-1.369l9.606-4.4a2.805,2.805,0,0,0,3,1.056l2.022,4.02a2.8,2.8,0,0,0-1.071,2.2Zm2.808,1.687a1.687,1.687,0,1,1,1.687-1.687A1.689,1.689,0,0,1,110.41,78.845Zm7.425-11.53a2.808,2.808,0,0,0,1.419.2l2.777,8.456a2.82,2.82,0,0,0-1.294,1.616l-7.535-.726a2.8,2.8,0,0,0-.776-1.657Zm2.78,21.987a1.687,1.687,0,1,1-1.687-1.687A1.689,1.689,0,0,1,120.615,89.3Zm-1.155-2.757a2.807,2.807,0,0,0-1.653.183l-5.359-7.64a2.813,2.813,0,0,0,.647-1.107l7.535.726a2.811,2.811,0,0,0,1.225,2.034Zm3.963-6.446a1.687,1.687,0,1,1,1.687-1.687A1.689,1.689,0,0,1,123.422,80.1Zm6.542-9.627a2.788,2.788,0,0,0,.348,1.353l-5.157,4.38a2.821,2.821,0,0,0-.434-.281l4.41-15.336q.11.009.222.009.088,0,.175-.006l1.988,7.371a2.812,2.812,0,0,0-1.551,2.51Zm2.808,1.687a1.687,1.687,0,1,1,1.687-1.686A1.689,1.689,0,0,1,132.772,72.157Z"
                                            transform="translate(0)"
                                            fill="#fff"
                                        />
                                    </g>
                                </g>
                            </svg>

                            <h1 className=" text-6xl font-KPMGBold mt-0 mb-7 text-foreground">Chat with your data</h1>
                            <h2 className="font-KPMGBold mb-2 text-foreground text-4xl">Ask me something:</h2>
                            {exampleQuestions?.length ? (
                                <ExampleList onExampleClicked={onExampleClicked} exampleQuestions={exampleQuestions} />
                            ) : (
                                <span className=" text-foreground flex-1">Loading...</span>
                            )}
                        </div>
                    ) : (
                        <div className={"flex-grow max-h-[1024px] max-w-[1028px] w-full overflow-y-auto px-8 flex flex-col no-scrollbar"}>
                            {answers.map((answer, index) => (
                                <div key={index}>
                                    <UserChatMessage message={answer[0]} />
                                    <div className={"mb-5 max-w-[80%] flex min-w-[500px]"}>
                                        <Answer
                                            key={index}
                                            answer={answer[1]}
                                            isSelected={selectedAnswer === index && activeAnalysisPanelTab !== undefined}
                                            onCitationClicked={c => onShowCitation(c, index)}
                                            onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab, index)}
                                            onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab, index)}
                                            onFollowupQuestionClicked={q => makeApiRequest(q)}
                                            showFollowupQuestions={
                                                (setting.overrides["suggest followup questions"].default as boolean) && answers.length - 1 === index
                                            }
                                        />
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <>
                                    <UserChatMessage message={lastQuestionRef.current} />
                                    <div className={styles.chatMessageGptMinWidth}>
                                        <AnswerLoading />
                                    </div>
                                </>
                            )}
                            {error ? (
                                <>
                                    <UserChatMessage message={lastQuestionRef.current} />
                                    <div className={styles.chatMessageGptMinWidth}>
                                        <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                                    </div>
                                </>
                            ) : null}
                            <div ref={chatMessageStreamEnd} />
                        </div>
                    )}

                    <div className={"w-full max-w-5xl pb-3"}>
                        <QuestionInput
                            clearOnSend
                            placeholder="Insert your question..."
                            disabled={isLoading}
                            onSend={question => makeApiRequest(question)}
                            deleteChat={clearChat}
                        />
                    </div>
                </div>

                {answers.length > 0 && activeAnalysisPanelTab && (
                    <AnalysisPanel
                        className={"flex-1 overflow-y-auto max-h-[89vh] ml-5 mr-5 flex flex-col h-full"}
                        activeCitation={activeCitation}
                        onActiveTabChanged={x => onToggleTab(x, selectedAnswer)}
                        citationHeight="810px"
                        answer={answers[selectedAnswer][1]}
                        activeTab={activeAnalysisPanelTab}
                    />
                )}
            </div>
        </div>
    );
};
