/**
 * 文档站对外的「源码」与 GitHub blob 基址，由构建时环境变量注入。
 * 默认留空，避免在发布物中写死或绑定特定 GitHub 账号/仓库。
 * 自托管时可设置：VITE_GITHUB_REPO_URL、VITE_GITHUB_BLOB_BASE
 */
const trim = (s: string | undefined) => (s ?? '').trim()

export const GITHUB_REPO_URL = trim(import.meta.env.VITE_GITHUB_REPO_URL)
export const GITHUB_BLOB_BASE = trim(import.meta.env.VITE_GITHUB_BLOB_BASE)
