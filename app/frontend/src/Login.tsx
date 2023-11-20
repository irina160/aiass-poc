import React, { FormEvent, useState } from "react";
import { useAuth } from "./AuthContext";

export function LoginForm() {
    const { login } = useAuth();
    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = (event: FormEvent) => {
        event.preventDefault();
        const success = login(email, password);
        if (!success) {
            setError("Invalid email or password");
        }
    };

    return (
        <div>
            <h1>Login Form</h1>
            <form onSubmit={handleSubmit}>
                {error && <p>{error}</p>}
                <label>
                    Email:
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
                </label>
                <br />
                <label>
                    Password:
                    <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
                </label>
                <br />
                <button type="submit">Login</button>
            </form>
        </div>
    );
}
