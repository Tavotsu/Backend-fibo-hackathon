import React, { ReactNode } from 'react';

interface MainLayoutProps {
    isDarkMode: boolean;
    children: ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ isDarkMode, children }) => {
    return (
        <div className={`${!isDarkMode ? 'invert-mode' : ''} h-screen w-full transition-all duration-300`}>
            <div className="flex h-full w-full bg-zinc-950 text-zinc-100 font-sans overflow-hidden">
                {children}
            </div>
        </div>
    );
};
