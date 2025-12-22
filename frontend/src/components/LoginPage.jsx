import React, { useState } from 'react';

const LoginPage = ({ onLogin }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        setIsLoading(true);
        // Simulate network delay
        setTimeout(() => {
            setIsLoading(false);
            onLogin(username);
        }, 800);
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-[var(--bg-dark)] relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[var(--primary)] opacity-[0.05] blur-[120px]"></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-[var(--accent)] opacity-[0.05] blur-[120px]"></div>

            <div className="w-full max-w-md p-8 card border-[var(--border)] relative z-10 backdrop-blur-xl">
                <div className="text-center mb-8">
                    <div className="w-12 h-12 bg-[var(--primary)] rounded mx-auto flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M2 12h20" /></svg>
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight mb-2">Ellie</h1>
                    <p className="text-[var(--text-muted)] text-sm">Secure Access for Medical Personnel</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Username</label>
                        <input
                            type="text"
                            className="w-full bg-[var(--bg-dark)] border border-[var(--border)] rounded p-3 text-sm focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] outline-none transition"
                            placeholder="Ex: dr.umut"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Password</label>
                        <input
                            type="password"
                            className="w-full bg-[var(--bg-dark)] border border-[var(--border)] rounded p-3 text-sm focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] outline-none transition"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full btn btn-primary py-3 mt-4 flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        ) : (
                            <>
                                <span>Sign In</span>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>
                            </>
                        )}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <a href="#" className="text-xs text-[var(--text-muted)] hover:text-[var(--primary)] transition">Forgot your credentials?</a>
                </div>
            </div>

            <div className="absolute bottom-6 text-center w-full text-[10px] text-[var(--text-muted)] uppercase tracking-[0.2em] opacity-50">
                Restricted Access System • v2.4.0
            </div>
        </div>
    );
};

export default LoginPage;
