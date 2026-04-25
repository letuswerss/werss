import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = path.resolve(root, '..');
const docsDir = path.join(repoRoot, 'docs');
const searchIndexFile = path.join(root, 'src/content/search-index.json');
const navFile = path.join(root, 'src/locales/zh-CN.json');
const repoRootPrefix = `${repoRoot}${path.sep}`;
const docsRootPrefix = `${docsDir}${path.sep}`;

function walk(dir, out = []) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, out);
    else if (ent.isFile() && ent.name.endsWith('.md')) out.push(p);
  }
  return out;
}

function routeForDoc(file) {
  const rel = path.relative(docsDir, file).replace(/\\/g, '/');
  const noExt = rel.replace(/\.md$/, '');
  return noExt === 'overview' ? '/docs/overview' : `/docs/${noExt}`;
}

function stripLineSuffix(target) {
  const match = /^(.*?)(?::(\d+))?$/.exec(target);
  return match ? { path: match[1], line: match[2] } : { path: target };
}

function toDocsRoute(relativeDocsPath) {
  const withoutExt = relativeDocsPath.replace(/\.md$/, '');
  return withoutExt === 'overview' ? '/docs/overview' : `/docs/${withoutExt}`;
}

function toGithubBlobUrl(repoRelativePath, line) {
  const cleanPath = repoRelativePath.replace(/^\/+/, '');
  return line ? `https://github.com/letuswerss/werss/blob/main/${cleanPath}#L${line}` : `https://github.com/letuswerss/werss/blob/main/${cleanPath}`;
}

function resolveMarkdownHref(href, currentRoute) {
  if (!href) return href;
  if (/^(https?:|mailto:|tel:|javascript:)/i.test(href) || href.startsWith('#')) return href;

  const [rawPath, hash = ''] = href.split('#');
  const hashSuffix = hash ? `#${hash}` : '';

  if (rawPath.startsWith('/docs/') || rawPath === '/') return `${rawPath}${hashSuffix}`;

  if (rawPath.startsWith(repoRootPrefix)) {
    const { path: targetPath, line } = stripLineSuffix(rawPath);
    if (targetPath.startsWith(docsRootPrefix)) {
      const relativeDocsPath = targetPath.slice(docsRootPrefix.length);
      return `${toDocsRoute(relativeDocsPath)}${hashSuffix}`;
    }

    const repoRelativePath = targetPath.slice(repoRootPrefix.length);
    return `${toGithubBlobUrl(repoRelativePath, line)}${hashSuffix}`;
  }

  const currentDocsPath = currentRoute.startsWith('/docs/') ? currentRoute.slice('/docs/'.length) : 'overview';
  const currentAbsFile = `${docsDir}${path.sep}${currentDocsPath}.md`;
  const resolvedAbs = new URL(rawPath, `file://${currentAbsFile}`).pathname;

  if (resolvedAbs.startsWith(docsRootPrefix)) {
    const relativeDocsPath = resolvedAbs.slice(docsRootPrefix.length);
    if (relativeDocsPath.endsWith('.md')) {
      return `${toDocsRoute(relativeDocsPath)}${hashSuffix}`;
    }
  }

  if (resolvedAbs.startsWith(repoRootPrefix)) {
    const repoRelativePath = resolvedAbs.slice(repoRootPrefix.length);
    return `${toGithubBlobUrl(repoRelativePath)}${hashSuffix}`;
  }

  return `${rawPath}${hashSuffix}`;
}

function extractLinks(md) {
  const links = [];
  const re = /!?\[[^\]]*\]\(([^)]+)\)/g;
  let match;
  while ((match = re.exec(md)) !== null) {
    links.push(match[1].trim());
  }
  return links;
}

const docs = walk(docsDir).sort();
const routes = new Set(docs.map(routeForDoc));
const searchIndex = JSON.parse(fs.readFileSync(searchIndexFile, 'utf8'));
const nav = JSON.parse(fs.readFileSync(navFile, 'utf8')).nav.sections.flatMap((section) => section.items.map((item) => item.path));

const routeMismatches = [];
for (const entry of searchIndex) {
  if (entry.path !== '/' && !routes.has(entry.path)) {
    routeMismatches.push(entry.path);
  }
}

const brokenLinks = [];
for (const file of docs) {
  const relRoute = routeForDoc(file);
  const markdown = fs.readFileSync(file, 'utf8');
  for (const href of extractLinks(markdown)) {
    if (/^(https?:|mailto:|tel:|javascript:)/i.test(href) || href.startsWith('#')) continue;
    const resolved = resolveMarkdownHref(href, relRoute);
    if (resolved.startsWith('/docs/')) {
      if (!routes.has(resolved.split('#')[0])) {
        brokenLinks.push({ file: path.relative(repoRoot, file), href, resolved });
      }
      continue;
    }
    if (resolved.startsWith('/')) continue;
    if (resolved.startsWith('https://github.com/letuswerss/werss/blob/main/')) continue;
    brokenLinks.push({ file: path.relative(repoRoot, file), href, resolved });
  }
}

const missingFromNav = [...routes].filter((route) => route !== '/' && !nav.includes(route));

const report = {
  docs: docs.length,
  routes: routes.size,
  navItems: nav.length,
  routeMismatches,
  missingFromNav,
  brokenLinks,
};

console.log(JSON.stringify(report, null, 2));

if (routeMismatches.length || brokenLinks.length) {
  process.exitCode = 1;
}
