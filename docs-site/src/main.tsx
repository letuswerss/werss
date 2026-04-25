import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app/App';
import zh from './locales/zh-CN.json';

document.title = zh.meta.htmlTitle;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
