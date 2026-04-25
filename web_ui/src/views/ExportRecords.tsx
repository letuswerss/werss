import React, { useState } from 'react'
import ExportRecordsComponent from '@/components/ExportRecords'

const ExportRecords: React.FC = () => {
  const [mpId] = useState('')

  return <ExportRecordsComponent mp_id={mpId} />
}

export default ExportRecords
