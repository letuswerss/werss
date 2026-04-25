import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom';
import { DocLayout } from '@/layouts/DocLayout';
import { HomePage } from '@/pages/HomePage';
import { DocPage } from '@/pages/DocPage';
import { docsContent } from '@/content/docs-content';
import zh from '@/locales/zh-CN.json';
import { interpolate } from '@/locales/interpolate';
import '@/styles/global.css';

function DocRoute() {
  const { '*': section } = useParams();
  const path = section ? `docs/${section}` : 'docs/overview';
  const missingBody = interpolate(zh.app.notFoundBody, { path });
  const rawContent = docsContent[path] || `# ${zh.app.notFoundH1}\n\n${missingBody}`;
  return <DocPage rawContent={rawContent} />;
}

export function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/docs/*" element={<DocLayout><DocRoute /></DocLayout>} />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
