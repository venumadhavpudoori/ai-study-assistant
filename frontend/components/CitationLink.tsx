import React from 'react';

interface CitationLinkProps {
    citationIndex: number;
    documentId: number;
    pageNumber: number;
}

export default function CitationLink({ citationIndex, documentId, pageNumber }: CitationLinkProps) {
    const handleCitationClick = (e: React.MouseEvent) => {
        e.preventDefault();
        // Opens the PDF at the specific page using the fragment identifier
        window.open(`/api/v1/documents/${documentId}/view#page=${pageNumber}`, '_blank');
    };

    return (
        <button
            onClick={handleCitationClick}
            className="inline-flex items-center px-1 rounded bg-blue-100 text-blue-700 text-xs font-bold hover:bg-blue-200 transition-colors mx-0.5"
            title={`Open Document ${documentId} at page ${pageNumber}`}
        >
            [{citationIndex}]
        </button>
    );
}
