import React from 'react';
import logo from './logo.svg';
import './App.css';
import SearchPage from './components/SearchPage';

export const API_BASE = 'http://localhost:5000';

function App() {
    return (
        <div className="App">
            <SearchPage />
        </div>
    );
}

export default App;
