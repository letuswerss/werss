import { GITHUB_BLOB_BASE } from '@/config/public';

function toGithubBlobUrl(repoRelativePath: string, line?: string): string {
  if (!GITHUB_BLOB_BASE) return '#';
  const cleanPath = repoRelativePath.replace(/^\/+/, '');
  return line ? `${GITHUB_BLOB_BASE}/${cleanPath}#L${line}` : `${GITHUB_BLOB_BASE}/${cleanPath}`;
}

function resolveRelativePath(from: string, to: string): string {
  const fromDir = from.substring(0, from.lastIndexOf('/'));
  const parts = fromDir.split('/').filter(Boolean);
  for (const seg of to.split('/')) {
    if (seg === '..') parts.pop();
    else if (seg && seg !== '.') parts.push(seg);
  }
  return '/' + parts.join('/');
}

export function resolveMarkdownHref(href: string, currentRoute: string): string {
  if (!href) return href;
  if (/^(https?:|mailto:|tel:|javascript:)/i.test(href) || href.startsWith('#')) return href;

  const [rawPath, hash = ''] = href.split('#');
  const hashSuffix = hash ? `#${hash}` : '';

  if (rawPath.startsWith('/docs/') || rawPath === '/') {
    return `${rawPath}${hashSuffix}`;
  }

  // Relative link: resolve against current route
  const currentDocsPath = currentRoute.startsWith('/docs/') ? currentRoute.slice('/docs/'.length) : 'overview';
  const resolved = resolveRelativePath(`/docs/${currentDocsPath}`, rawPath);

  if (resolved.startsWith('/docs/')) {
    const withoutExt = resolved.replace(/\.md$/, '').slice('/docs/'.length);
    const route = withoutExt === 'overview' ? '/docs/overview' : `/docs/${withoutExt}`;
    return `${route}${hashSuffix}`;
  }

  const repoRelativePath = resolved.startsWith('/') ? resolved.slice(1) : resolved;
  return `${toGithubBlobUrl(repoRelativePath)}${hashSuffix}`;
}
