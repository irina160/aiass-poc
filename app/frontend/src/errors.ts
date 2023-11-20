export class AuthenticationError extends Error {
    code: string;
    constructor(description: string, code: string) {
        super(description);
        this.code = code;
        Object.setPrototypeOf(this, AuthenticationError.prototype);
    }
}
