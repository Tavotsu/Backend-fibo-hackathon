import React from 'react';

interface ThemeToggleProps {
    isDarkMode: boolean;
    toggle: () => void;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ isDarkMode, toggle }) => {
    return (
        <button
            onClick={toggle}
            className={`w-10 h-10 rounded-full border-2 border-black overflow-hidden relative shadow-sm hover:shadow-md transition-all duration-500 ease-in-out no-invert ${isDarkMode ? 'rotate-0' : 'rotate-180'}`}
            title="Cambiar tema"
            style={{
                background: 'linear-gradient(90deg, black 50%, white 50%)'
            }}
        >
            {/* The visual is purely the CSS background and border, no inner icons needed for this specific design */}
        </button>
    );
};
