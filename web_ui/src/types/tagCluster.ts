export interface TagClusterListItem {
  id: string
  name: string
  description?: string | null
  centroid_tag_id?: string | null
  centroid_tag_name?: string | null
  size: number
  cluster_version: string
  updated_at?: string | null
}

export interface TagClusterMember {
  tag_id: string
  tag_name: string
  member_score: number
}

export interface SimilarTagItem {
  tag_id: string
  similar_tag_id: string
  similar_tag_name: string
  score: number
  embedding_score: number
  cooccurrence_score: number
  lexical_score: number
}

export interface TagClusterMergeSuggestion {
  source_tag_id: string
  source_tag_name: string
  target_tag_id: string
  target_tag_name: string
  score: number
  reason: string
}

export interface TagClusterDetail extends TagClusterListItem {
  members: TagClusterMember[]
  merge_suggestions?: TagClusterMergeSuggestion[]
}

export interface TagClusterListResponse {
  list: TagClusterListItem[]
  page?: {
    offset: number
    limit: number
    total: number
  }
}
