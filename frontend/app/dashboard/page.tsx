"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { workspaceService, Workspace } from '@/lib/api';
import { useAuth } from '@/lib/AuthContext';

export default function DashboardPage() {
    const { user, loading: authLoading, logout } = useAuth();
    const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
    const [newWorkspaceName, setNewWorkspaceName] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [isLoggingOut, setIsLoggingOut] = useState(false);
    const router = useRouter();

    useEffect(() => {
        if (!authLoading) {
            if (!user) {
                router.push('/login');
            } else {
                fetchWorkspaces();
            }
        }
    }, [user, authLoading, router]);

    const fetchWorkspaces = async () => {
        try {
            const data = await workspaceService.listWorkspaces();
            setWorkspaces(data);
        } catch (err: any) {
            if (err.response?.status === 401) {
                router.push('/login');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateWorkspace = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsCreating(true);
        try {
            await workspaceService.createWorkspace(newWorkspaceName);
            setNewWorkspaceName('');
            await fetchWorkspaces();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to create workspace');
        } finally {
            setIsCreating(false);
        }
    };

    const handleLogout = async () => {
        setIsLoggingOut(true);
        try {
            await logout();
        } finally {
            setIsLoggingOut(false);
        }
    };

    if (authLoading || (isLoading && user)) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-gray-50">
                <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Top Navigation */}
            <nav className="bg-white border-b border-gray-200">
                <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold">
                            AI
                        </div>
                        <span className="font-semibold text-gray-900 text-lg">AI Study Assistant</span>
                    </div>

                    <div className="flex items-center space-x-4">
                        {user && (
                            <span className="text-sm text-gray-600">
                                Signed in as <strong className="font-medium text-gray-900">{user.username}</strong>
                            </span>
                        )}
                        <button
                            onClick={handleLogout}
                            disabled={isLoggingOut}
                            className="text-sm text-gray-700 hover:text-red-600 font-medium px-3 py-1.5 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-50"
                        >
                            {isLoggingOut ? 'Logging out...' : 'Sign Out'}
                        </button>
                    </div>
                </div>
            </nav>

            <main className="max-w-6xl mx-auto p-6">
                <header className="mb-8 mt-4 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">My Workspaces</h1>
                        <p className="text-gray-600 mt-1">Organize your study materials into projects.</p>
                    </div>
                    <button
                        onClick={() => setIsCreating(true)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm font-medium"
                    >
                        + New Workspace
                    </button>
                </header>

                {isCreating && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl border border-gray-100">
                            <h2 className="text-xl font-bold mb-4 text-gray-900">Create New Workspace</h2>
                            <form onSubmit={handleCreateWorkspace} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Workspace Name</label>
                                    <input
                                        type="text"
                                        className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                        value={newWorkspaceName}
                                        onChange={(e) => setNewWorkspaceName(e.target.value)}
                                        placeholder="e.g., Biology 101, Machine Learning"
                                        required
                                        autoFocus
                                    />
                                </div>
                                <div className="flex justify-end space-x-3 pt-2">
                                    <button
                                        type="button"
                                        onClick={() => setIsCreating(false)}
                                        className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors"
                                    >
                                        Create
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {workspaces.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-xl border-2 border-dashed border-gray-200">
                        <div className="mx-auto w-12 h-12 text-gray-400 mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium text-gray-900 mb-1">No workspaces yet</h3>
                        <p className="text-gray-500 mb-4">Create your first workspace to start uploading documents and asking questions.</p>
                        <button
                            onClick={() => setIsCreating(true)}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
                        >
                            Create Workspace
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {workspaces.map((ws) => (
                            <div
                                key={ws.id}
                                onClick={() => router.push(`/workspace/${ws.id}`)}
                                className="p-6 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all cursor-pointer group hover:border-blue-300"
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div className="p-3 bg-blue-50 rounded-lg text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2z" />
                                        </svg>
                                    </div>
                                    <span className="text-xs text-gray-400">
                                        {new Date(ws.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">{ws.name}</h3>
                                <p className="text-sm text-gray-500 mb-4">Click to open and start chatting</p>
                                <div className="flex items-center text-blue-600 text-sm font-medium group-hover:translate-x-1 transition-transform">
                                    Open Workspace
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
