import React from 'react';
import logo from './logo.svg';
import './App.css';
import SearchPage from './components/SearchPage';
import ResultsPage from './components/ResultsPage';

export const API_BASE = 'http://127.0.0.1:5000';

function App() {
    return (
        <div className="App">
            {/* <SearchPage /> */}
            <ResultsPage />
        </div>
    );
}

export default App;
