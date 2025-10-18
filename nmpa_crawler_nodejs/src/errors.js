class RequestBlockedError extends Error {
    constructor(message, context = {}) {
        super(message);
        this.name = 'RequestBlockedError';
        this.context = context;
    }
}

class PersistentFailureError extends Error {
    constructor(message, context = {}) {
        super(message);
        this.name = 'PersistentFailureError';
        this.context = context;
    }
}

class RunAbortedError extends Error {
    constructor(message, context = {}) {
        super(message);
        this.name = 'RunAbortedError';
        this.context = context;
    }
}

export { RequestBlockedError, PersistentFailureError, RunAbortedError };
