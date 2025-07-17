import React from "react";

interface SearchBoxProps {
    value: string;
    onChange: (value: string) => void;
    onSubmit?: () => void;
    placeholder?: string;
}

const SearchBox: React.FC<SearchBoxProps> = ({ value, onChange, onSubmit, placeholder }) => {
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange(e.target.value);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter" && onSubmit) {
            onSubmit();
        }
    };

    return (
        <div className="mb-6">
            <input
                type="text"
                value={value}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={placeholder || "Search..."}
                className="w-full max-w-md px-4 py-2 rounded-lg border border-green-300 dark:border-gray-600 focus:ring-2 focus:ring-green-400 dark:focus:ring-green-500 focus:border-green-400 dark:focus:border-green-500 bg-white dark:bg-gray-700 text-green-900 dark:text-green-100 placeholder-green-500 dark:placeholder-green-400 transition"
            />
            {onSubmit && (
                <button
                    onClick={onSubmit}
                    className="ml-2 px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition"
                >
                    Search
                </button>
            )}
        </div>
    );
};

export default SearchBox;