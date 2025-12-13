import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Database, Terminal } from 'lucide-react';
import { BriaFiboResponse } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';

interface ResponseViewerProps {
  response: BriaFiboResponse | null;
  isLoading: boolean;
}

export const ResponseViewer: React.FC<ResponseViewerProps> = ({ response, isLoading }) => {
  if (isLoading) {
    return (
      <Card className="w-full mt-6 animate-pulse border-none shadow-none bg-transparent">
        <div className="flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-muted rounded w-3/4"></div>
            <div className="space-y-2">
              <div className="h-4 bg-muted rounded"></div>
              <div className="h-4 bg-muted rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  if (!response) return null;

  return (
    <div className="mt-8 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card className="border-l-4 border-l-primary shadow-sm overflow-hidden">
        <CardHeader className="bg-muted/30 pb-4">
          <div className="flex items-center space-x-2">
            <Terminal className="w-5 h-5 text-primary" />
            <CardTitle className="text-lg">Respuesta del Modelo</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-6 prose prose-slate dark:prose-invert max-w-none">
          <ReactMarkdown>{response.content || ''}</ReactMarkdown>
        </CardContent>
      </Card>

      {response.rag_sources && response.rag_sources.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {response.rag_sources.map((source, index) => (
            <div key={index} className="flex items-center p-3 text-sm border rounded-md bg-background hover:bg-accent/50 transition-colors">
              <Database className="w-4 h-4 mr-3 text-muted-foreground" />
              <span className="truncate font-medium text-foreground">{source}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};