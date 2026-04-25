import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { FileQuestion, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  const { t } = useTranslation()

  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center px-4">
      <div className="flex max-w-md flex-col items-center text-center">
        <div
          className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-muted text-muted-foreground"
          aria-hidden
        >
          <FileQuestion className="h-12 w-12" strokeWidth={1.5} />
        </div>
        <p className="text-sm font-medium uppercase tracking-widest text-muted-foreground">
          404
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          {t('notFound.title')}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {t('notFound.description')}
        </p>
        <Button asChild className="mt-8">
          <Link to="/">
            <Home />
            {t('notFound.backHome')}
          </Link>
        </Button>
      </div>
    </div>
  )
}
