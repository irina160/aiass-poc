import { ErrorComponent } from "@components/ErrorCmpt/ErrorComponent";
import { useFetchWithMsal } from "@hooks/useFetchWithMsal";
import { useState, useEffect } from "react";
import { Outlet, useLocation, useNavigate, useParams } from "react-router-dom";

export interface IChatHistory {
    conversation_id: string;
    timestamp: number;
    topic: string;
}

export const ChatContextPage = () => {
    const [chatHistory, setChatHistory] = useState<IChatHistory[]>([]);
    const [error, setError] = useState<boolean>(false);
    const [errorMessage, setErrorMessage] = useState<string>("");
    const location = useLocation();
    const params = useParams();
    const { customFetch } = useFetchWithMsal();
    const navigate = useNavigate();

    useEffect(() => {
        customFetch({ scopes: [] }, `/api${location.pathname}`, {
            method: "GET"
        })
            .then(data => setChatHistory(data["conversations"]))
            .then(() =>
                navigate(
                    `/usecasetypes/${params.usecasetypeid}/indices/${params.indexid}/categories/${
                        params.categoryid
                    }/chat/?new_conversation=${window.crypto.randomUUID()}`
                )
            )
            .catch(err => {
                setError(true);
                setErrorMessage(err.message);
            });
    }, []);

    if (error) return <ErrorComponent open={error} setOpen={setError} error={errorMessage} />;
    if (!chatHistory) return <div>Loading ...</div>;
    return <Outlet context={[chatHistory, setChatHistory]} />;
};
