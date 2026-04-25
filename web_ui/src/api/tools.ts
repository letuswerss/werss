import http from './http'

export const exportArticles = (params:any) => {
    // 确保 format 是数组
    const formatArray = Array.isArray(params.format) ? params.format : []
    
    // 处理 doc_id：如果是导出选中，使用 ids；否则使用空数组
    // 确保 doc_id 是字符串数组，过滤掉无效值
    let doc_id: string[] = []
    if (params.scope === 'selected' && params.ids) {
      doc_id = params.ids
        .map((id: any) => String(id)) // 转换为字符串
        .filter((id: string) => id && id !== 'undefined' && id !== 'null' && id.trim() !== '') // 过滤无效值
    }
    
    // 调试日志：检查传递的参数
    console.log('exportArticles 参数:', {
      scope: params.scope,
      ids: params.ids,
      idsType: typeof params.ids,
      idsIsArray: Array.isArray(params.ids),
      doc_id: doc_id,
      doc_idLength: doc_id.length,
      mp_id: params.mp_id
    })
    
    const requestData = {
      mp_id: params.mp_id || '',
      doc_id: doc_id,
      page_size: params.page_size || 10,
      page_count: params.page_count || 1,
      add_title: params.add_title !== undefined ? params.add_title : true,
      remove_images: params.remove_images || false,
      remove_links: params.remove_links || false,
      export_md: formatArray.includes('md'),
      export_docx: formatArray.includes('docx'),
      export_json: formatArray.includes('json'),
      export_csv: formatArray.includes('csv'),
      export_pdf: formatArray.includes('pdf'),
      zip_filename: params.zip_filename || ''
    };
    
    // 调试日志：检查最终请求数据
    console.log('exportArticles 请求数据:', {
      ...requestData,
      doc_id: requestData.doc_id,
      doc_idLength: requestData.doc_id.length,
      doc_idValues: requestData.doc_id, // 显示数组中的实际值
      doc_idStringified: JSON.stringify(requestData.doc_id) // 以字符串形式显示
    })
    
    // 验证至少选择一个导出格式
    if (!requestData.export_md && !requestData.export_docx && !requestData.export_json && 
        !requestData.export_csv && !requestData.export_pdf) {
      throw new Error('请至少选择一个导出格式')
    }
    
  return http.post<{code: number, data: any, message?: string}>('/wx/tools/export/articles', requestData, {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
}
export const reExtractTags = (articleIds: string[]) => {
  return http.post<{code: number, data: any, message?: string}>('/wx/tools/extract_tags', {
    article_ids: articleIds
  })
}

/** 异步补充缺失标签：返回 job_id 与 total，再轮询 getMissingTagsJobStatus */
export const startMissingTagsJob = () => {
  return http.post<{ code: number; data: { job_id: string | null; total: number }; message?: string }>(
    '/wx/tools/extract_tags_missing/start'
  )
}

export const getMissingTagsJobStatus = (jobId: string) => {
  return http.get<{
    code: number
    data: {
      job_id: string
      status: string
      total: number
      processed: number
      success_count?: number
      error_count?: number
      message?: string
      started_at?: number
      finished_at?: number | null
      elapsed_seconds?: number | null
    }
  }>('/wx/tools/extract_tags_missing/status', { params: { job_id: jobId } })
}

export const getExportRecords = (params:any) => {
    const requestData = {
      mp_id: params.mp_id,
    };
  return http.get<{code: number, data: string}>('/wx/tools/export/list', {params:requestData})
}
export const DeleteExportRecords = (params:any) => {
    const requestData = {
      mp_id: params.mp_id||"",
      filename: params.filename,
    };
  return http.delete<{code: number, data: string}>('/wx/tools/export/delete', {data:requestData})
}