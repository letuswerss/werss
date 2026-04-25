import React, { useState } from 'react'

const NovelReader: React.FC = () => {
  const [categories] = useState([
    { id: 1, name: '玄幻' },
    { id: 2, name: '都市' },
    { id: 3, name: '科幻' }
  ])
  const [novels] = useState([
    { id: 1, title: '小说1', description: '这是一本小说' },
    { id: 2, title: '小说2', description: '这是另一本小说' }
  ])
  const [chapters] = useState([
    { id: 1, title: '第一章' },
    { id: 2, title: '第二章' }
  ])
  const [currentContent] = useState('这里是小说正文内容...')
  const [isReading, setIsReading] = useState(false)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [hasError, setHasError] = useState(false)

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  const toggleDrawer = () => {
    setIsDrawerOpen(!isDrawerOpen)
  }

  const prevPage = () => {
    // 上一页逻辑
  }

  const nextPage = () => {
    // 下一页逻辑
  }

  const retry = () => {
    // 重试逻辑
  }

  return (
    <div className="font-[Arial,sans-serif] max-w-[800px] mx-auto p-5">
      {/* 顶部搜索栏 */}
      <div className="flex mb-5">
        <input type="text" placeholder="搜索小说" className="flex-1 p-2.5 border border-[#ccc] rounded" />
        <button className="p-2.5 ml-2.5 bg-[#007bff] text-white border-none rounded cursor-pointer">搜索</button>
      </div>

      {/* 公告 */}
      <div className="bg-[#f8f9fa] p-2.5 mb-5 rounded">
        <p>最新公告：欢迎使用小说阅读器！</p>
      </div>

      {/* 分类导航 */}
      <div className="flex mb-5">
        {categories.map((category) => (
          <div key={category.id} className="p-2.5 mr-2.5 bg-[#e9ecef] rounded cursor-pointer">
            {category.name}
          </div>
        ))}
      </div>

      {/* 小说列表 */}
      <div className="mb-5">
        {novels.map((novel) => (
          <div key={novel.id} className="p-4 mb-2.5 bg-[#f8f9fa] rounded">
            <h3>{novel.title}</h3>
            <p>{novel.description}</p>
          </div>
        ))}
      </div>

      {/* 阅读页面 */}
      {isReading && (
        <div className="relative">
          <div className="p-5 bg-card text-card-foreground rounded cursor-pointer" onClick={toggleMenu}>
            {currentContent}
          </div>

          {/* 左侧滑出目录 */}
          <div className={`fixed top-0 -left-[300px] w-[300px] h-full bg-card border-r border-border transition-[left] duration-300 z-[1000] ${isDrawerOpen ? 'left-0' : ''}`}>
            <div className="p-5">
              <h3 className="text-foreground">目录</h3>
              <ul className="text-muted-foreground">
                {chapters.map((chapter) => (
                  <li key={chapter.id} className="hover:text-primary py-2 cursor-pointer transition-colors">{chapter.title}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* 菜单和设置 */}
          {isMenuOpen && (
            <div className="fixed bottom-5 left-1/2 -translate-x-1/2 flex bg-black/80 backdrop-blur-sm p-2.5 rounded-xl shadow-2xl z-[1001]">
              <button className="mx-[5px] py-2 px-4 bg-primary text-primary-foreground border-none rounded-lg cursor-pointer hover:opacity-90 transition-all font-medium" onClick={prevPage}>上一页</button>
              <button className="mx-[5px] py-2 px-4 bg-primary text-primary-foreground border-none rounded-lg cursor-pointer hover:opacity-90 transition-all font-medium" onClick={nextPage}>下一页</button>
              <button className="mx-[5px] py-2 px-4 bg-primary text-primary-foreground border-none rounded-lg cursor-pointer hover:opacity-90 transition-all font-medium" onClick={toggleDrawer}>目录</button>
            </div>
          )}
        </div>
      )}

      {/* 出错界面 */}
      {hasError && (
        <div className="text-center p-5 bg-destructive/10 text-destructive border border-destructive/20 rounded-xl">
          <p className="font-medium mb-3">网络错误，请重试！</p>
          <button className="px-5 py-2 bg-destructive text-destructive-foreground border-none rounded-lg cursor-pointer hover:opacity-90 transition-all font-bold" onClick={retry}>重试</button>
        </div>
      )}
    </div>
  )
}

export default NovelReader
