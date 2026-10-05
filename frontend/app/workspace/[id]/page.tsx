"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { workspaceService, chatService, Document, Conversation } from '@/lib/api';
import ChatInterface from '@/components/ChatInterface';
import { useAuth } from '@/lib/AuthContext';

export default function WorkspacePage({ params }: { params: { id: string } }) {
    const { user, loading: authLoading, logout } = useAuth();
    const [docs, setDocs] = useState<Document[]>([]);
    const [convs, setConvs] = useState<Conversation[]>([]);
    const [activeConvId, setActiveConvId] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        if (!authLoading) {
            if (!user) {
                router.push('/login');
            } else {
                fetchWorkspaceData();
            }
        }
    }, [params.id, user, authLoading, router]);

    const fetchWorkspaceData = async () => {
        try {
            const [fetchedDocs, fetchedConvs] = await Promise.all([
                workspaceService.getDocuments(params.id),
                chatService.listConversations(params.id)
            ]);
            setDocs(fetchedDocs);
            setConvs(fetchedConvs);
            if (fetchedConvs.length > 0 && !activeConvId) {
                setActiveConvId(fetchedConvs[0].id.toString());
            }
        } catch (err: any) {
            if (err.response?.status === 401) {
                router.push('/login');
            } else {
                console.error("Failed to fetch workspace data", err);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const fileInput = (e.target as HTMLFormElement).elements.namedItem('file') as HTMLInputElement;
        if (!fileInput?.files?.[0]) return;

        setUploading(true);
        try {
            await workspaceService.uploadDocument(params.id, fileInput.files[0]);
            fileInput.value = '';
            await fetchWorkspaceData();
        } catch (err: any) {
            if (err.response?.status === 401) {
                alert("Your session has expired. Please log in again.");
                router.push('/login');
            } else {
                alert(err.response?.data?.detail || "Upload failed");
            }
        } finally {
            setUploading(false);
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
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Top Navigation */}
            <header className="h-14 bg-white border-b border-gray-200 px-6 flex items-center justify-between flex-shrink-0">
                <div className="flex items-center space-x-4">
                    <Link
                        href="/dashboard"
                        className="text-sm font-medium text-gray-600 hover:text-gray-900 flex items-center space-x-1"
                    >
                        <span>← Back to Workspaces</span>
                    </Link>
                    <span className="text-gray-300">|</span>
                    <span className="font-semibold text-gray-800 text-sm">Workspace #{params.id}</span>
                </div>

                <div className="flex items-center space-x-4">
                    {user && (
                        <span className="text-xs text-gray-600">
                            Signed in as <strong className="font-medium text-gray-900">{user.username}</strong>
                        </span>
                    )}
                    <button
                        onClick={logout}
                        className="text-xs text-gray-700 hover:text-red-600 font-medium px-2.5 py-1 rounded hover:bg-gray-100 transition-colors"
                    >
                        Sign Out
                    </button>
                </div>
            </header>

            {/* Main Workspace Body */}
            <div className="flex flex-1 overflow-hidden">
                {/* Sidebar: Documents */}
                <aside className="w-64 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
                    <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                        <h2 className="font-semibold text-gray-800 text-sm">Documents</h2>
                        <span className="text-xs text-gray-400">{docs.length} files</span>
                    </div>

                    <div className="flex-1 overflow-y-auto p-3 space-y-2">
                        {docs.length === 0 ? (
                            <p className="text-xs text-gray-400 p-2 text-center">No PDFs uploaded yet.</p>
                        ) : (
                            docs.map((doc) => (
                                <div
                                    key={doc.id}
                                    className="p-2.5 text-xs rounded-lg border border-gray-100 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
                                >
                                    <span className="truncate mr-2 font-medium text-gray-700" title={doc.filename}>
                                        {doc.filename}
                                    </span>
                                    <span
                                        className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                                            doc.status === 'READY'
                                                ? 'bg-green-100 text-green-700'
                                                : doc.status === 'FAILED'
                                                ? 'bg-red-100 text-red-700'
                                                : 'bg-yellow-100 text-yellow-700'
                                        }`}
                                    >
                                        {doc.status}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>

                    <form onSubmit={handleUpload} className="p-4 border-t border-gray-200 bg-gray-50">
                        <label className="block text-xs font-medium text-gray-700 mb-1.5">Upload Study PDF</label>
                        <input
                            type="file"
                            name="file"
                            accept=".pdf"
                            className="text-xs mb-2 w-full text-gray-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                            required
                        />
                        <button
                            type="submit"
                            disabled={uploading}
                            className="w-full bg-blue-600 text-white text-xs py-2 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 font-medium transition-colors"
                        >
                            {uploading ? 'Processing PDF...' : 'Upload PDF'}
                        </button>
                    </form>
                </aside>

                {/* Middle: Conversation List */}
                <aside className="w-64 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
                    <div className="p-4 border-b border-gray-100 flex justify-between items-center">
                        <h2 className="font-semibold text-gray-800 text-sm">Chats</h2>
                        <button
                            onClick={async () => {
                                try {
                                    const conv = await chatService.createConversation(parseInt(params.id), 'New Chat');
                                    setActiveConvId(conv.id.toString());
                                    await fetchWorkspaceData();
                                } catch (err: any) {
                                    alert(err.response?.data?.detail || 'Failed to create chat');
                                }
                            }}
                            className="text-blue-600 hover:text-blue-700 text-sm font-semibold px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                            title="Start new chat"
                        >
                            + New
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-2 space-y-1">
                        {convs.length === 0 ? (
                            <p className="text-xs text-gray-400 p-2 text-center">No chats started yet.</p>
                        ) : (
                            convs.map((conv) => (
                                <button
                                    key={conv.id}
                                    onClick={() => setActiveConvId(conv.id.toString())}
                                    className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors ${
                                        activeConvId === conv.id.toString()
                                            ? 'bg-blue-50 text-blue-700 font-medium'
                                            : 'hover:bg-gray-100 text-gray-700'
                                    }`}
                                >
                                    <div className="truncate">{conv.title}</div>
                                    <div className="text-[10px] text-gray-400 mt-0.5">
                                        {new Date(conv.created_at).toLocaleDateString()}
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </aside>

                {/* Right: Chat Interface */}
                <main className="flex-1 flex flex-col p-6 bg-gray-50 overflow-hidden">
                    {activeConvId ? (
                        <ChatInterface conversationId={activeConvId} />
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                            <div className="h-12 w-12 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 mb-3">
                                💬
                            </div>
                            <p className="text-sm font-medium text-gray-600">No chat selected</p>
                            <p className="text-xs text-gray-400 mt-1">Select an existing chat or click "+ New" to begin.</p>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
